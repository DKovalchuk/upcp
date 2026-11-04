"""Subject-liveness check of the web auth guard — SPEC-0027 §3.2 / TASK-0146 (red → green).

Finding 2: the guard verified only the JWT signature, so a correctly
signed token whose subject never existed (or was disabled) was accepted
on every domain route until exp. New semantics: after signature
verification the subject must exist and be active:

- Redis negative cache ``auth:user:{sub}`` = state string, TTL 60s;
- miss → ``SessionLocal`` DB lookup (session-less repository seam);
- Redis down → direct DB query; DB failure → fail-closed 401.

TASK-0169 harness migration: the app is now protected by the
``web_auth`` dependency (formerly ``add_middleware(AuthMiddleware)``), so
the old ``mw._fetch_user_state`` / ``mw.get_redis_client`` seams
re-point to the same layer the middleware extracted into:

| old seam (middleware)               | new seam (dependency path)                  |
|-------------------------------------|---------------------------------------------|
| ``mw._fetch_user_state`` (spy)      | ``UserRepository.get_auth_state`` (class spy)|
| ``mw.get_redis_client``             | ``app.shared.redis.get_redis_client``       |

Behavioral assertions (negative caching, TTL 60, cache-hit → no DB read,
Redis-down → DB) are unchanged. Agent-surface auth (the retired
middleware's agent branch + PUBLIC_PATHS) is covered by
``test_agent_surface_auth.py`` since TASK-0170. New symbols are
imported/patched inside tests, so the file collects before the
implementation exists.
"""

from __future__ import annotations

from collections.abc import Iterator

import app.shared.redis as shared_redis
import pytest
from app.identity.auth import _get_token_service
from app.identity.models import User
from app.identity.token_service import TokenService
from app.identity.web_auth import web_auth
from app.shared.config import get_settings
from app.shared.database import Base
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from tests.conftest import _test_engine, _TestSession

TS = TokenService(secret_key="test-secret")
_DEAD_SUB = "00000000-0000-4000-8000-00000000dead"


class _MemRedis:
    """In-memory cache stand-in — hermetic tests must not need a live Redis."""

    def __init__(self) -> None:
        self.store: dict[str, str] = {}
        self.ttls: dict[str, int | None] = {}

    def get(self, key: str):  # noqa: ANN001
        return self.store.get(key)

    def set(self, key: str, value: str, ex: int | None = None) -> None:  # noqa: ANN001
        self.store[key] = value
        self.ttls[key] = ex


def _add_user(email: str, *, active: bool) -> str:
    session = _TestSession()
    try:
        user = User(email=email, password_hash="x" * 60, display_name="MW", is_active=active)
        session.add(user)
        session.commit()
        return str(user.id)
    finally:
        session.close()


def _cleanup_users() -> None:
    session = _TestSession()
    try:
        session.query(User).filter(User.email.like("mw-%@test.local")).delete()
        session.commit()
    finally:
        session.close()


@pytest.fixture()
def app_client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """web_auth-protected app; SessionLocal redirected to the test DB.

    ``web_auth`` resolves ``SubjectStateService``'s session lazily
    (session-less repository seam), so monkeypatching
    app.shared.database redirects the user-existence lookup without
    touching the guard's code — same trick as the old middleware.
    """
    monkeypatch.setattr(get_settings(), "disable_auth", False)  # guard must be ON
    Base.metadata.create_all(bind=_test_engine)

    app = FastAPI(dependencies=[Depends(web_auth)])
    app.dependency_overrides[_get_token_service] = lambda: TS

    @app.get("/api/v1/projects")
    async def list_projects() -> dict:
        return {"items": []}

    yield TestClient(app)
    _cleanup_users()


def _get(client: TestClient, sub: str):
    token = TS.create_access_token(sub)
    return client.get("/api/v1/projects", headers={"Authorization": f"Bearer {token}"})


def test_unknown_subject_rejected_401(app_client: TestClient) -> None:
    """Valid-signature token for a subject that never existed → 401.

    Was the finding-2 hole: the guard passed it through until exp.
    """
    resp = _get(app_client, _DEAD_SUB)
    assert resp.status_code == 401, f"unknown subject GET -> {resp.status_code}: {resp.text[:200]}"
    assert resp.headers.get("www-authenticate") == "Bearer"


def test_disabled_user_rejected_401(app_client: TestClient) -> None:
    """is_active=False user with a valid token → 401 (not just no-permissions)."""
    sub = _add_user("mw-disabled@test.local", active=False)
    resp = _get(app_client, sub)
    assert resp.status_code == 401, f"disabled user GET -> {resp.status_code}"


def test_existing_active_user_passes(app_client: TestClient) -> None:
    """Positive control: real active user with valid token → 200."""
    sub = _add_user("mw-active@test.local", active=True)
    resp = _get(app_client, sub)
    assert resp.status_code == 200, f"active user GET -> {resp.status_code}"


def test_negative_cache_stored_and_avoids_db_hit(
    app_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Second request for the same subject is served from the cache.

    AC3 (SPEC-0027): negative caching included — the DB lookup runs once.
    Seam: ``UserRepository.get_auth_state`` counted at class level (the
    middleware's ``_fetch_user_state`` after the SPEC-0029 extraction).
    """
    from app.identity.repositories import UserRepository

    calls = {"n": 0}
    real_fetch = UserRepository.get_auth_state

    def counting_fetch(self: UserRepository, user_id: str) -> str:
        calls["n"] += 1
        return real_fetch(self, user_id)

    monkeypatch.setattr(UserRepository, "get_auth_state", counting_fetch)
    # One shared instance: get_redis_client() is called separately for the
    # read and the write — a fresh instance per call would drop the write.
    fake_redis = _MemRedis()
    monkeypatch.setattr(shared_redis, "get_redis_client", lambda: fake_redis)

    sub = _add_user("mw-known@test.local", active=True)

    assert _get(app_client, sub).status_code == 200
    first = calls["n"]
    assert first == 1, f"cold request must hit the DB once, hit {first}"
    # TTL contract of the subject-state cache (SPEC-0027 §3.2)
    key = f"auth:user:{sub}"
    assert key in fake_redis.store, f"subject-state cache key missing: {sorted(fake_redis.store)}"
    assert fake_redis.ttls[key] == 60, f"TTL must stay 60s, got {fake_redis.ttls[key]}"

    assert _get(app_client, sub).status_code == 200
    assert calls["n"] == first, (
        f"warm request re-queried the DB (cache miss): {calls['n']} > {first}"
    )

    # Negative caching: unknown subject is stored after first sight and
    # never re-queried within the TTL. Fresh UUID per run so a persistent
    # cache outside this test can't satisfy the lookup spuriously.
    import uuid

    fresh_dead = str(uuid.uuid4())
    dead = _get(app_client, fresh_dead)
    assert dead.status_code == 401
    assert calls["n"] == first + 1, "unknown subject must be looked up once"


def test_redis_outage_falls_back_to_db(
    app_client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Redis unreachable → correctness from the DB, no auth bypass (AC5-ish)."""

    class _BrokenRedis:
        def get(self, key: str):  # noqa: ANN001
            raise ConnectionError("redis down")

        def set(self, key: str, value: str, ex: int | None = None) -> None:  # noqa: ANN001
            raise ConnectionError("redis down")

    # the denylist + subject-state cache resolve the client lazily per call
    monkeypatch.setattr(shared_redis, "get_redis_client", lambda: _BrokenRedis())

    active = _add_user("mw-redis@test.local", active=True)
    assert _get(app_client, active).status_code == 200
    assert _get(app_client, _DEAD_SUB).status_code == 401
