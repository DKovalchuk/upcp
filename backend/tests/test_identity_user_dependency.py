"""get_current_user over SubjectStateService + UserRepository — SPEC-0029 §3.5 / TASK-0175.

D4 parity: bearer/JWT/denylist checks stay as-is; the raw subject query
is replaced by the cached ``SubjectStateService`` (``auth:user:{sub}``,
TTL 60) and the profile is read via ``UserRepository.get_by_id`` on the
REQUEST session.

Design decision (task evidence): the cache serves the LIVENESS path
only — the profile stays ONE direct read per request; the task AC
«0 DB reads» applies to the liveness lookup (cache-spy tests below pin
both counts). Session split: liveness runs session-less (its own lazy
session), the profile reuses the request ``db`` (``Session.get`` hits
the identity map — correct for flush-only fixtures on the shared test
connection).

Parity guards (green from the start) pin the historical 401 shapes; the
cache-spy tests encode the NEW behavior (red before the rewiring). New
symbols are imported inside tests so the file collects before the
implementation exists.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Iterator
from uuid import uuid4

import app.shared.redis as shared_redis
import pytest
from app.identity.auth import get_current_user
from app.identity.dependencies import CurrentUser
from app.identity.models import User
from app.identity.token_service import TokenService
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

TS = TokenService(secret_key="test-secret-key-unification")


class _MemRedis:
    """In-memory redis stand-in — hermetic tests must not need a live Redis."""

    def __init__(self) -> None:
        self.store: dict[str, str] = {}
        self.ttls: dict[str, int | None] = {}

    def get(self, key: str):  # noqa: ANN201
        return self.store.get(key)

    def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.store[key] = value
        self.ttls[key] = ex


class _BrokenRedis:
    """Redis refuses connections — the outage fallback path."""

    def get(self, key: str):  # noqa: ANN201
        raise ConnectionError("redis down")

    def set(self, key: str, value: str, ex: int | None = None) -> None:
        raise ConnectionError("redis down")


@pytest.fixture()
def seed_user(db_session: Session) -> Iterator[Callable[..., tuple[str, str]]]:
    """Committed seed + teardown purge. Seeds COMMIT on purpose: the
    session-less liveness read closes (and thereby rolls back)
    uncommitted work on the shared StaticPool test connection — probe:
    only an identity-map ``Session.get`` still serves it afterwards.
    """
    created: list[str] = []

    def _seed(*, active: bool = True, superuser: bool = False) -> tuple[str, str]:
        suffix = uuid4().hex[:10]
        user = User(
            email=f"unif-{suffix}@test.local",
            password_hash="x" * 60,
            display_name="Unif",
            is_active=active,
            is_superuser=superuser,
        )
        db_session.add(user)
        db_session.commit()
        created.append(str(user.id))
        return str(user.id), user.email

    yield _seed
    if created:
        db_session.query(User).filter(User.id.in_(created)).delete(synchronize_session=False)
        db_session.commit()


@pytest.fixture()
def client(db_session: Session) -> TestClient:
    """Minimal app exposing get_current_user, request session = db_session."""
    from app.identity.auth import _get_token_service
    from app.shared.database import get_session

    app = FastAPI()

    @app.get("/protected-user")
    async def protected(user: CurrentUser = Depends(get_current_user)) -> dict[str, object]:
        return {"user_id": user.user_id, "email": user.email, "is_superuser": user.is_superuser}

    def override_session():
        yield db_session

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[_get_token_service] = lambda: TS
    return TestClient(app)


def _auth(user_id: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {TS.create_access_token(user_id)}"}


def _spy_user_repository(monkeypatch: pytest.MonkeyPatch, attr: str) -> dict[str, int]:
    """Count UserRepository.<attr> calls (class-level seam, red pre-TASK-0175)."""
    from app.identity.repositories import UserRepository

    calls = {"n": 0}
    original = getattr(UserRepository, attr)

    def counting(self: UserRepository, user_id: str):  # noqa: ANN201
        calls["n"] += 1
        return original(self, user_id)

    monkeypatch.setattr(UserRepository, attr, counting)
    return calls


# ── Positives: valid JWT → CurrentUser fields ───────────────────────


def test_valid_jwt_returns_current_user_fields(
    client: TestClient, seed_user: Callable[..., tuple[str, str]]
) -> None:
    uid, email = seed_user()
    resp = client.get("/protected-user", headers=_auth(uid))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["user_id"] == uid
    assert body["email"] == email
    assert body["is_superuser"] is False


def test_superuser_flag_returned(
    client: TestClient, seed_user: Callable[..., tuple[str, str]]
) -> None:
    uid, _ = seed_user(superuser=True)
    resp = client.get("/protected-user", headers=_auth(uid))
    assert resp.status_code == 200, resp.text
    assert resp.json()["is_superuser"] is True


# ── Negatives: historical 401 shapes, byte-parity guards ────────────


def test_unknown_subject_rejected_with_historical_detail(client: TestClient) -> None:
    resp = client.get("/protected-user", headers=_auth(str(uuid4())))
    assert resp.status_code == 401, resp.text
    assert resp.json()["detail"] == "User not found or inactive"
    assert resp.headers.get("www-authenticate") == "Bearer"


def test_disabled_subject_rejected_with_historical_detail(
    client: TestClient, seed_user: Callable[..., tuple[str, str]]
) -> None:
    uid, _ = seed_user(active=False)
    resp = client.get("/protected-user", headers=_auth(uid))
    assert resp.status_code == 401, resp.text
    assert resp.json()["detail"] == "User not found or inactive"
    assert resp.headers.get("www-authenticate") == "Bearer"


def test_missing_token_rejected(client: TestClient) -> None:
    resp = client.get("/protected-user")
    assert resp.status_code == 401, resp.text
    assert resp.json()["detail"] == "Missing authentication token"
    assert resp.headers.get("www-authenticate") == "Bearer"


def test_invalid_token_rejected(client: TestClient) -> None:
    resp = client.get("/protected-user", headers={"Authorization": "Bearer nope"})
    assert resp.status_code == 401, resp.text
    assert resp.json()["detail"] == "Invalid or expired token"
    assert resp.headers.get("www-authenticate") == "Bearer"


def test_denylisted_token_rejected_with_invalid_shape(
    client: TestClient,
    seed_user: Callable[..., tuple[str, str]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Logout denylist still wins before any liveness lookup (kept code path)."""
    fake = _MemRedis()
    monkeypatch.setattr(shared_redis, "get_redis_client", lambda: fake)
    uid, _ = seed_user()
    token = TS.create_access_token(uid)
    fake.store["auth:deny:" + hashlib.sha256(token.encode()).hexdigest()] = "1"

    resp = client.get("/protected-user", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401, resp.text
    assert resp.json()["detail"] == "Invalid or expired token"


# ── Boundaries: Redis outage → DB fallback, no exception ────────────


def test_redis_outage_liveness_falls_back_to_db(
    client: TestClient,
    seed_user: Callable[..., tuple[str, str]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(shared_redis, "get_redis_client", lambda: _BrokenRedis())
    active, _ = seed_user()
    disabled, _ = seed_user(active=False)

    ok = client.get("/protected-user", headers=_auth(active))
    assert ok.status_code == 200, f"outage must not break auth: {ok.text}"
    rejected = client.get("/protected-user", headers=_auth(disabled))
    assert rejected.status_code == 401, rejected.text
    assert rejected.json()["detail"] == "User not found or inactive"


# ── AC: cache-spy on the liveness path + profile-read deviation ─────


def test_second_request_serves_liveness_from_cache(
    client: TestClient,
    seed_user: Callable[..., tuple[str, str]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cache-spy: cold liveness = one state DB read; warm = zero (AC3/AC5)."""
    calls = _spy_user_repository(monkeypatch, "get_auth_state")
    fake = _MemRedis()
    monkeypatch.setattr(shared_redis, "get_redis_client", lambda: fake)

    uid, _ = seed_user()
    assert client.get("/protected-user", headers=_auth(uid)).status_code == 200
    assert calls["n"] == 1, f"cold liveness must read the state DB once, got {calls['n']}"
    assert client.get("/protected-user", headers=_auth(uid)).status_code == 200
    assert calls["n"] == 1, f"warm liveness must be served from cache, DB reads={calls['n']}"
    assert fake.store.get(f"auth:user:{uid}") == "active"


def test_profile_read_stays_one_repository_read_per_request(
    client: TestClient,
    seed_user: Callable[..., tuple[str, str]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Documented deviation: cache serves liveness; the profile read stays
    exactly ONE direct repository read per request (same query count as
    the pre-rewiring code for valid users)."""
    uid, email = seed_user()
    calls = _spy_user_repository(monkeypatch, "get_by_id")  # new seam — red pre-TASK-0175
    fake = _MemRedis()
    monkeypatch.setattr(shared_redis, "get_redis_client", lambda: fake)

    resp = client.get("/protected-user", headers=_auth(uid))
    assert resp.status_code == 200, resp.text
    assert resp.json()["email"] == email
    assert client.get("/protected-user", headers=_auth(uid)).status_code == 200
    assert calls["n"] == 2, (
        f"profile must be read once per request (the liveness cache does not "
        f"cover it), got {calls['n']}"
    )


def test_user_deleted_within_cache_ttl_rejected(
    client: TestClient,
    db_session: Session,
    seed_user: Callable[..., tuple[str, str]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cache HIT must not resurrect a deleted profile: liveness serves
    "active" from cache, the profile read answers None → same 401."""
    calls = _spy_user_repository(monkeypatch, "get_auth_state")
    fake = _MemRedis()
    monkeypatch.setattr(shared_redis, "get_redis_client", lambda: fake)

    uid, _ = seed_user()
    headers = _auth(uid)
    assert client.get("/protected-user", headers=headers).status_code == 200  # primes TTL 60
    assert fake.store.get(f"auth:user:{uid}") == "active"

    db_session.query(User).filter_by(id=uid).delete(synchronize_session=False)
    db_session.expire_all()
    db_session.commit()

    resp = client.get("/protected-user", headers=headers)
    assert resp.status_code == 401, resp.text
    assert resp.json()["detail"] == "User not found or inactive"
    assert resp.headers.get("www-authenticate") == "Bearer"
    assert calls["n"] == 1, f"warm liveness must come from the cache, reads={calls['n']}"
