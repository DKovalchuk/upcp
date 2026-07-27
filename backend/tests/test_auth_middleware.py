"""Tests for auth middleware — FastAPI dependencies for JWT + agent auth."""

import pytest
from app.identity.auth import get_current_agent, get_current_user
from app.identity.dependencies import CurrentAgent, CurrentUser
from app.identity.models import User
from app.identity.token_service import TokenService
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


@pytest.fixture()
def token_service() -> TokenService:
    return TokenService(secret_key="test-secret-key-for-middleware-tests")


@pytest.fixture()
def test_user(db_session: Session) -> User:
    user = User(
        email="auth-test@example.com",
        password_hash="hash",
        display_name="Auth Test",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture()
def auth_app(token_service: TokenService, db_session: Session) -> FastAPI:
    from app.identity.auth import _get_token_service
    from app.shared.database import get_session

    app = FastAPI()

    def override_session():
        yield db_session

    def override_token_service():
        return token_service

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[_get_token_service] = override_token_service

    @app.get("/protected-user")
    async def protected_user(user: CurrentUser = Depends(get_current_user)) -> dict:
        return {"user_id": user.user_id, "email": user.email}

    @app.get("/protected-agent")
    async def protected_agent(agent: CurrentAgent = Depends(get_current_agent)) -> dict:
        return {"agent_id": agent.agent_id, "name": agent.name}

    @app.get("/either")
    async def either_auth(
        user: CurrentUser | None = Depends(get_current_user),
        agent: CurrentAgent | None = Depends(get_current_agent),
    ) -> dict:
        if user:
            return {"type": "user", "id": user.user_id}
        if agent:
            return {"type": "agent", "id": agent.agent_id}
        return {"type": "none"}

    return app


# ---------------------------------------------------------------------------
# User auth
# ---------------------------------------------------------------------------


class TestGetCurrentUser:
    def test_valid_jwt_returns_user(
        self,
        auth_app: FastAPI,
        test_user: User,
        token_service: TokenService,
        db_session: Session,
    ) -> None:
        token = token_service.create_access_token(test_user.id)
        client = TestClient(auth_app)
        resp = client.get(
            "/protected-user",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["user_id"] == test_user.id
        assert resp.json()["email"] == test_user.email

    def test_missing_header_returns_401(self, auth_app: FastAPI) -> None:
        client = TestClient(auth_app)
        resp = client.get("/protected-user")
        assert resp.status_code == 401

    def test_invalid_token_returns_401(self, auth_app: FastAPI) -> None:
        client = TestClient(auth_app)
        resp = client.get(
            "/protected-user",
            headers={"Authorization": "Bearer invalid-token-value"},
        )
        assert resp.status_code == 401

    def test_expired_token_returns_401(
        self,
        auth_app: FastAPI,
        test_user: User,
        token_service: TokenService,
    ) -> None:
        from datetime import timedelta

        token = token_service.create_access_token(test_user.id, expires_delta=timedelta(seconds=-1))
        client = TestClient(auth_app)
        resp = client.get(
            "/protected-user",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 401

    def test_wrong_scheme_returns_401(
        self,
        auth_app: FastAPI,
        test_user: User,
        token_service: TokenService,
    ) -> None:
        token = token_service.create_access_token(test_user.id)
        client = TestClient(auth_app)
        resp = client.get(
            "/protected-user",
            headers={"Authorization": f"Basic {token}"},
        )
        assert resp.status_code == 401

    def test_inactive_user_returns_401(
        self,
        auth_app: FastAPI,
        test_user: User,
        token_service: TokenService,
        db_session: Session,
    ) -> None:
        test_user.is_active = False
        db_session.flush()

        token = token_service.create_access_token(test_user.id)
        client = TestClient(auth_app)
        resp = client.get(
            "/protected-user",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 401

    def test_nonexistent_user_returns_401(
        self,
        auth_app: FastAPI,
        token_service: TokenService,
    ) -> None:
        token = token_service.create_access_token("nonexistent-user-id")
        client = TestClient(auth_app)
        resp = client.get(
            "/protected-user",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Agent auth
# ---------------------------------------------------------------------------


class TestGetCurrentAgent:
    def test_missing_header_returns_401(self, auth_app: FastAPI) -> None:
        client = TestClient(auth_app)
        resp = client.get("/protected-agent")
        assert resp.status_code == 401

    def test_invalid_token_returns_401(self, auth_app: FastAPI) -> None:
        client = TestClient(auth_app)
        resp = client.get(
            "/protected-agent",
            headers={"X-Agent-Token": "invalid-token"},
        )
        assert resp.status_code == 401
