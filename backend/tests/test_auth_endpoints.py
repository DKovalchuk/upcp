"""Tests for auth endpoints — setup, login, logout, refresh, me, password change."""

import pytest
from app.identity.models import User
from app.identity.token_service import TokenService
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


@pytest.fixture()
def token_service() -> TokenService:
    return TokenService(secret_key="test-secret-key-for-endpoint-tests")


@pytest.fixture()
def auth_app(db_session: Session, token_service: TokenService) -> FastAPI:
    from app.identity.auth import _get_token_service
    from app.identity.endpoints import public_router, router
    from app.shared.database import get_session

    app = FastAPI()
    app.include_router(public_router, prefix="/auth")
    app.include_router(router, prefix="/auth")

    def override_session():
        yield db_session

    def override_token_service():
        return token_service

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[_get_token_service] = override_token_service
    return app


@pytest.fixture()
def client(auth_app: FastAPI) -> TestClient:
    return TestClient(auth_app)


# ---------------------------------------------------------------------------
# POST /auth/setup
# ---------------------------------------------------------------------------


class TestSetup:
    def test_setup_creates_owner(self, client: TestClient) -> None:
        resp = client.post(
            "/auth/setup",
            json={
                "email": "owner@example.com",
                "password": "securepass123",
                "display_name": "Owner",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["user"]["email"] == "owner@example.com"
        assert data["organization"]["name"] == "Owner's Organization"
        assert "access_token" in data
        assert "refresh_token" in data

    def test_setup_fails_if_users_exist(self, client: TestClient, db_session: Session) -> None:
        user = User(email="existing@example.com", password_hash="hash", display_name="Existing")
        db_session.add(user)
        db_session.flush()

        resp = client.post(
            "/auth/setup",
            json={
                "email": "new@example.com",
                "password": "securepass123",
                "display_name": "New",
            },
        )
        assert resp.status_code == 409

    def test_setup_invalid_email(self, client: TestClient) -> None:
        resp = client.post(
            "/auth/setup",
            json={
                "email": "not-an-email",
                "password": "securepass123",
                "display_name": "Bad",
            },
        )
        assert resp.status_code == 422

    def test_setup_weak_password(self, client: TestClient) -> None:
        resp = client.post(
            "/auth/setup",
            json={
                "email": "weak@example.com",
                "password": "short",
                "display_name": "Weak",
            },
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------


class TestLogin:
    def test_login_success(self, client: TestClient, db_session: Session) -> None:
        import bcrypt

        pw_hash = bcrypt.hashpw(b"securepass123", bcrypt.gensalt()).decode()
        user = User(email="login@example.com", password_hash=pw_hash, display_name="Login")
        db_session.add(user)
        db_session.flush()

        resp = client.post(
            "/auth/login",
            json={
                "email": "login@example.com",
                "password": "securepass123",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client: TestClient, db_session: Session) -> None:
        import bcrypt

        pw_hash = bcrypt.hashpw(b"correct-password", bcrypt.gensalt()).decode()
        user = User(email="wrong@example.com", password_hash=pw_hash, display_name="Wrong")
        db_session.add(user)
        db_session.flush()

        resp = client.post(
            "/auth/login",
            json={
                "email": "wrong@example.com",
                "password": "wrong-password",
            },
        )
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, client: TestClient) -> None:
        resp = client.post(
            "/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "anypassword",
            },
        )
        assert resp.status_code == 401

    def test_login_inactive_user(self, client: TestClient, db_session: Session) -> None:
        import bcrypt

        pw_hash = bcrypt.hashpw(b"securepass123", bcrypt.gensalt()).decode()
        user = User(
            email="inactive@example.com",
            password_hash=pw_hash,
            display_name="Inactive",
            is_active=False,
        )
        db_session.add(user)
        db_session.flush()

        resp = client.post(
            "/auth/login",
            json={
                "email": "inactive@example.com",
                "password": "securepass123",
            },
        )
        assert resp.status_code == 401

    def test_login_lockout_after_5_failures(self, client: TestClient, db_session: Session) -> None:
        import bcrypt

        pw_hash = bcrypt.hashpw(b"correct-password", bcrypt.gensalt()).decode()
        user = User(email="lockout@example.com", password_hash=pw_hash, display_name="Lockout")
        db_session.add(user)
        db_session.flush()

        for _ in range(5):
            client.post(
                "/auth/login",
                json={
                    "email": "lockout@example.com",
                    "password": "wrong",
                },
            )

        resp = client.post(
            "/auth/login",
            json={
                "email": "lockout@example.com",
                "password": "correct-password",
            },
        )
        assert resp.status_code == 423  # Locked

    def test_login_audit_recorded(self, client: TestClient, db_session: Session) -> None:
        import bcrypt
        from app.identity.models import LoginAudit

        pw_hash = bcrypt.hashpw(b"securepass123", bcrypt.gensalt()).decode()
        user = User(email="audit@example.com", password_hash=pw_hash, display_name="Audit")
        db_session.add(user)
        db_session.flush()

        client.post(
            "/auth/login",
            json={
                "email": "audit@example.com",
                "password": "securepass123",
            },
        )

        audits = db_session.query(LoginAudit).filter_by(email="audit@example.com").all()
        assert len(audits) >= 1
        assert audits[0].action == "login_success"


# ---------------------------------------------------------------------------
# POST /auth/refresh
# ---------------------------------------------------------------------------


class TestRefresh:
    def test_refresh_returns_new_tokens(self, client: TestClient, db_session: Session) -> None:
        import bcrypt

        pw_hash = bcrypt.hashpw(b"securepass123", bcrypt.gensalt()).decode()
        user = User(email="refresh@example.com", password_hash=pw_hash, display_name="Refresh")
        db_session.add(user)
        db_session.flush()

        login_resp = client.post(
            "/auth/login",
            json={
                "email": "refresh@example.com",
                "password": "securepass123",
            },
        )
        refresh_token = login_resp.json()["refresh_token"]

        resp = client.post(
            "/auth/refresh",
            json={
                "refresh_token": refresh_token,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["refresh_token"] != refresh_token

    def test_refresh_invalid_token(self, client: TestClient) -> None:
        resp = client.post(
            "/auth/refresh",
            json={
                "refresh_token": "invalid-token",
            },
        )
        assert resp.status_code == 401

    def test_refresh_old_token_invalid(self, client: TestClient, db_session: Session) -> None:
        import bcrypt

        pw_hash = bcrypt.hashpw(b"securepass123", bcrypt.gensalt()).decode()
        user = User(email="rotate@example.com", password_hash=pw_hash, display_name="Rotate")
        db_session.add(user)
        db_session.flush()

        login_resp = client.post(
            "/auth/login",
            json={
                "email": "rotate@example.com",
                "password": "securepass123",
            },
        )
        old_refresh = login_resp.json()["refresh_token"]

        client.post("/auth/refresh", json={"refresh_token": old_refresh})

        resp = client.post("/auth/refresh", json={"refresh_token": old_refresh})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /auth/me
# ---------------------------------------------------------------------------


class TestMe:
    def test_me_returns_user(self, client: TestClient, db_session: Session) -> None:
        import bcrypt

        pw_hash = bcrypt.hashpw(b"securepass123", bcrypt.gensalt()).decode()
        user = User(email="me@example.com", password_hash=pw_hash, display_name="Me")
        db_session.add(user)
        db_session.flush()

        login_resp = client.post(
            "/auth/login",
            json={
                "email": "me@example.com",
                "password": "securepass123",
            },
        )
        access_token = login_resp.json()["access_token"]

        resp = client.get(
            "/auth/me",
            headers={
                "Authorization": f"Bearer {access_token}",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["email"] == "me@example.com"

    def test_me_no_token(self, client: TestClient) -> None:
        resp = client.get("/auth/me")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# POST /auth/password/change
# ---------------------------------------------------------------------------


class TestPasswordChange:
    def test_password_change_success(self, client: TestClient, db_session: Session) -> None:
        import bcrypt

        pw_hash = bcrypt.hashpw(b"old-password-123", bcrypt.gensalt()).decode()
        user = User(email="changepw@example.com", password_hash=pw_hash, display_name="ChangePW")
        db_session.add(user)
        db_session.flush()

        login_resp = client.post(
            "/auth/login",
            json={
                "email": "changepw@example.com",
                "password": "old-password-123",
            },
        )
        access_token = login_resp.json()["access_token"]

        resp = client.post(
            "/auth/password/change",
            json={
                "current_password": "old-password-123",
                "new_password": "new-password-456",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert resp.status_code == 200

    def test_password_change_wrong_current(self, client: TestClient, db_session: Session) -> None:
        import bcrypt

        pw_hash = bcrypt.hashpw(b"correct-password", bcrypt.gensalt()).decode()
        user = User(email="wrongpw@example.com", password_hash=pw_hash, display_name="WrongPW")
        db_session.add(user)
        db_session.flush()

        login_resp = client.post(
            "/auth/login",
            json={
                "email": "wrongpw@example.com",
                "password": "correct-password",
            },
        )
        access_token = login_resp.json()["access_token"]

        resp = client.post(
            "/auth/password/change",
            json={
                "current_password": "wrong-current",
                "new_password": "new-password-456",
            },
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert resp.status_code == 400
