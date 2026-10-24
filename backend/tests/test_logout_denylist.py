"""Logout access-token denylist — SPEC-0027 §3.3 / TASK-0147 (red → green).

Finding 3: logout revoked only the refresh token — the access JWT kept
working on every route until exp. New semantics: logout writes
``auth:deny:{sha256(raw)}`` with TTL = exp − now (self-expiring); the
middleware (domain routes) and ``get_current_user`` (/auth/*) reject the
token 401 — same shape as an invalid token, distinguishable in
logs/metric via reason=logout.

Redis is faked through ``app.shared.redis.get_redis_client`` (the
denylist imports it lazily — test seam per the ``_fetch_user_state``
precedent); Redis-down tests pin the documented fail-open tradeoff
(AC5). No denylist symbols are imported at module level, so the file
collects before the implementation exists.
"""

from __future__ import annotations

import hashlib
import logging
from collections.abc import Iterator
from types import SimpleNamespace
from uuid import uuid4

import app.shared.redis as shared_redis
import pytest
from app.identity.middleware import AuthMiddleware
from app.identity.models import User
from app.identity.token_service import TokenService
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

PASSWORD = "securepass123"


class _MemRedis:
    """In-memory redis stand-in — hermetic tests must not need a live Redis."""

    def __init__(self) -> None:
        self.store: dict[str, str] = {}
        self.ttls: dict[str, int | None] = {}

    def get(self, key):  # noqa: ANN001
        return self.store.get(key)

    def set(self, key, value, ex: int | None = None) -> None:  # noqa: ANN001
        self.store[key] = value
        self.ttls[key] = ex


class _BrokenRedis:
    """Redis refuses connections — the AC5 fail-open path."""

    def get(self, key):  # noqa: ANN001
        raise ConnectionError("redis down")

    def set(self, key, value, ex: int | None = None) -> None:  # noqa: ANN001
        raise ConnectionError("redis down")


@pytest.fixture()
def fake_redis(monkeypatch: pytest.MonkeyPatch) -> Iterator[_MemRedis]:
    """One shared instance: logout writes the key, the next request reads it."""
    fake = _MemRedis()
    monkeypatch.setattr(shared_redis, "get_redis_client", lambda: fake)
    yield fake


@pytest.fixture()
def logged_in(db_session: Session, fake_redis: _MemRedis) -> Iterator[SimpleNamespace]:
    """Auth router + middleware-guarded domain route, logged-in token pair.

    One TokenService instance signs the login JWTs and verifies them in
    the middleware, mirroring production wiring with a test secret.
    """
    import bcrypt
    from app.identity.auth import _get_token_service
    from app.identity.endpoints import router as auth_router
    from app.shared.database import get_session

    ts = TokenService(secret_key="test-secret-key-for-denylist-tests")
    app = FastAPI()
    app.include_router(auth_router, prefix="/auth")

    @app.get("/api/v1/projects")
    async def list_projects() -> dict:
        return {"items": []}

    app.add_middleware(AuthMiddleware, token_service=ts)

    def override_session():
        yield db_session

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[_get_token_service] = lambda: ts
    client = TestClient(app)

    pw_hash = bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt()).decode()
    # login() commits (audit invariant) — a fixed email would collide with the
    # next test in the same process (rollback only undoes uncommitted work)
    email = f"deny-{uuid4().hex[:10]}@example.com"
    user = User(email=email, password_hash=pw_hash, display_name="Deny")
    db_session.add(user)
    db_session.flush()

    login = client.post("/auth/login", json={"email": email, "password": PASSWORD})
    assert login.status_code == 200, f"login precondition -> {login.text[:200]}"
    tokens = login.json()
    user_id = str(user.id)

    yield SimpleNamespace(
        client=client,
        token_service=ts,
        access=tokens["access_token"],
        refresh=tokens["refresh_token"],
    )
    _purge_user(db_session, user_id)


def _logout(ns: SimpleNamespace) -> None:
    resp = ns.client.post(
        "/auth/logout",
        json={"refresh_token": ns.refresh},
        headers={"Authorization": f"Bearer {ns.access}"},
    )
    assert resp.status_code == 200, f"logout precondition -> {resp.status_code}: {resp.text[:200]}"


def _deny_key(raw_token: str) -> str:
    return "auth:deny:" + hashlib.sha256(raw_token.encode()).hexdigest()


def _purge_user(db_session: Session, user_id: str) -> None:
    """Remove rows the auth flow committed (login/logout commit invariant).

    db_session's teardown rollback only undoes *uncommitted* work — without
    this, committed test users leak into later files that assume an empty
    user table (first-run POST /auth/setup checks), making suite behavior
    depend on file order.
    """
    from app.identity.models import LoginAudit, RefreshToken

    db_session.query(RefreshToken).filter_by(user_id=user_id).delete()
    db_session.query(LoginAudit).filter_by(user_id=user_id).delete()
    db_session.query(User).filter_by(id=user_id).delete()
    db_session.commit()


# ── AC4: denied on both enforcement surfaces ────────────────────────


def test_domain_route_rejects_access_token_after_logout(logged_in: SimpleNamespace) -> None:
    """Middleware-protected domain route → 401 for the logged-out access token."""
    h = {"Authorization": f"Bearer {logged_in.access}"}
    assert logged_in.client.get("/api/v1/projects", headers=h).status_code == 200  # precondition

    _logout(logged_in)

    resp = logged_in.client.get("/api/v1/projects", headers=h)
    assert resp.status_code == 401, (
        f"domain GET after logout -> {resp.status_code}, expected 401 (finding 3): "
        f"{resp.text[:200]}"
    )
    assert resp.headers.get("www-authenticate") == "Bearer"


def test_auth_me_rejects_access_token_after_logout(logged_in: SimpleNamespace) -> None:
    """/auth/me goes through get_current_user — denylist must be enforced there too."""
    h = {"Authorization": f"Bearer {logged_in.access}"}
    assert logged_in.client.get("/auth/me", headers=h).status_code == 200  # precondition

    _logout(logged_in)

    resp = logged_in.client.get("/auth/me", headers=h)
    assert resp.status_code == 401, f"/auth/me after logout -> {resp.status_code}, expected 401"
    assert resp.headers.get("www-authenticate") == "Bearer"


def test_refresh_rotation_still_rejected_after_logout(logged_in: SimpleNamespace) -> None:
    """Existing behavior preserved: revoked refresh → 401 (AC4 tail)."""
    _logout(logged_in)
    resp = logged_in.client.post("/auth/refresh", json={"refresh_token": logged_in.refresh})
    assert resp.status_code == 401, f"refresh after logout -> {resp.status_code}, expected 401"


# ── Key shape + self-expiring TTL ────────────────────────────────────


def test_denylist_key_fingerprint_and_ttl(
    logged_in: SimpleNamespace, fake_redis: _MemRedis
) -> None:
    """Key = auth:deny:{sha256(raw)}; TTL = exp − now (≤ access lifetime, no cleanup job)."""
    payload = logged_in.token_service.verify_access_token(logged_in.access)
    exp = int(payload["exp"])

    _logout(logged_in)

    key = _deny_key(logged_in.access)
    assert key in fake_redis.store, f"denylist key missing: {sorted(fake_redis.store)}"
    assert fake_redis.store[key] == "1"
    ttl = fake_redis.ttls[key]
    assert ttl is not None and 0 < ttl <= 900, f"unbounded/self-expiry violated: ttl={ttl}"
    # exp − now at write time (±5s slack for the requests in between)
    assert abs(ttl - (exp - int(__import__("time").time()))) <= 5, (
        f"TTL must equal exp - now: ttl={ttl}, remaining={exp - int(__import__('time').time())}"
    )


# ── AC5: Redis down → fail-open + structured warning ────────────────


def test_redis_down_fails_open_and_warns(
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    request: pytest.FixtureRequest,
) -> None:
    """Redis refused → authenticated requests still succeed (availability over ≤15-min window)."""
    import bcrypt
    from app.identity.auth import _get_token_service
    from app.identity.endpoints import router as auth_router
    from app.shared.database import get_session

    monkeypatch.setattr(shared_redis, "get_redis_client", lambda: _BrokenRedis())

    ts = TokenService(secret_key="test-secret-key-for-denylist-tests")
    app = FastAPI()
    app.include_router(auth_router, prefix="/auth")

    @app.get("/api/v1/projects")
    async def list_projects() -> dict:
        return {"items": []}

    app.add_middleware(AuthMiddleware, token_service=ts)

    def override_session():
        yield db_session

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[_get_token_service] = lambda: ts
    client = TestClient(app)

    pw_hash = bcrypt.hashpw(PASSWORD.encode(), bcrypt.gensalt()).decode()
    email = f"redisdown-{uuid4().hex[:10]}@example.com"
    user = User(email=email, password_hash=pw_hash, display_name="RedisDown")
    db_session.add(user)
    db_session.flush()
    uid = str(user.id)
    request.addfinalizer(lambda: _purge_user(db_session, uid))

    login = client.post("/auth/login", json={"email": email, "password": PASSWORD})
    assert login.status_code == 200, f"login precondition -> {login.text[:200]}"
    tokens = login.json()
    h = {"Authorization": f"Bearer {tokens['access_token']}"}

    with caplog.at_level(logging.WARNING, logger="app.identity.denylist"):
        out = client.post(
            "/auth/logout", json={"refresh_token": tokens["refresh_token"]}, headers=h
        )
        assert out.status_code == 200, f"logout with redis down -> {out.text[:200]}"
        resp = client.get("/api/v1/projects", headers=h)

    assert resp.status_code == 200, (
        f"request with denylist redis down -> {resp.status_code}; AC5 requires fail-open"
    )
    warnings = [r for r in caplog.records if r.levelno >= logging.WARNING]
    assert any(getattr(r, "action", "").startswith("auth.denylist") for r in warnings), (
        "structured warning expected on denylist redis failure: "
        f"{[getattr(r, 'action', r.getMessage()) for r in warnings]}"
    )
