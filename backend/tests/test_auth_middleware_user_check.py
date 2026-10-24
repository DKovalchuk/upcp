"""AuthMiddleware user-existence check — SPEC-0027 §3.2 / TASK-0146 (red → green).

Finding 2: middleware verified only the JWT signature, so a correctly
signed token whose subject never existed (or was disabled) was accepted
on every domain route until exp. New semantics: after signature
verification the subject must exist and be active:

- Redis negative cache ``auth:user:{sub}`` = "1"/"0", TTL 60s;
- miss → SessionLocal DB lookup (same lazy-import pattern as the
  agent-token branch — tests point SessionLocal at the test DB);
- Redis down → direct DB query; DB failure → fail-closed 401.

Agent-token branch and PUBLIC_PATHS are untouched (covered by existing
tests). New symbols are imported/patched inside tests, so the file
collects before the implementation exists.
"""

from __future__ import annotations

from collections.abc import Iterator

import app.shared.database as db_mod
import pytest
from app.identity.middleware import AuthMiddleware
from app.identity.models import User
from app.identity.token_service import TokenService
from app.shared.database import Base
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.conftest import _test_engine, _TestSession

TS = TokenService(secret_key="test-secret")
_DEAD_SUB = "00000000-0000-4000-8000-00000000dead"


class _MemRedis:
    """In-memory cache stand-in — hermetic tests must not need a live Redis."""

    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    def get(self, key: str):  # noqa: ANN001
        return self.store.get(key)

    def set(self, key: str, value: str, ex: int | None = None) -> None:  # noqa: ANN001
        self.store[key] = value


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
    """App with middleware; SessionLocal lazily redirected to the test DB.

    The middleware resolves SessionLocal at call time (agent-branch
    precedent), so monkeypatching app.shared.database redirects the
    user-existence lookup without touching the middleware code.
    """
    Base.metadata.create_all(bind=_test_engine)
    monkeypatch.setattr(db_mod, "SessionLocal", _TestSession)

    app = FastAPI()
    app.add_middleware(AuthMiddleware, token_service=TS)

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

    Was the finding-2 hole: middleware passed it through until exp.
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
    """
    calls = {"n": 0}
    import app.identity.middleware as mw

    real_fetch = mw._fetch_user_state

    def counting_fetch(user_id: str) -> str:
        calls["n"] += 1
        return real_fetch(user_id)

    monkeypatch.setattr(mw, "_fetch_user_state", counting_fetch)
    # One shared instance: get_redis_client() is called separately for the
    # read and the write — a fresh instance per call would drop the write.
    fake_redis = _MemRedis()
    monkeypatch.setattr(mw, "get_redis_client", lambda: fake_redis)

    sub = _add_user("mw-known@test.local", active=True)

    assert _get(app_client, sub).status_code == 200
    first = calls["n"]
    assert first == 1, f"cold request must hit the DB once, hit {first}"

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
    import app.identity.middleware as mw

    class _BrokenRedis:
        def get(self, key: str):  # noqa: ANN001
            raise ConnectionError("redis down")

        def set(self, key: str, value: str, ex: int | None = None) -> None:  # noqa: ANN001
            raise ConnectionError("redis down")

    monkeypatch.setattr(mw, "get_redis_client", lambda: _BrokenRedis())

    active = _add_user("mw-redis@test.local", active=True)
    assert _get(app_client, active).status_code == 200
    assert _get(app_client, _DEAD_SUB).status_code == 401
