"""Permission cache/query behind AuthCacheProvider + PermissionRepository — TASK-0175.

SPEC-0029 §3.5: the gate's data access moves out of ``permissions.py`` —
the Redis cache read/write goes through ``AuthCacheProvider`` (same key
``rbac:user_perms:{user_id}``, same JSON encoding, same TTL 60, same
never-raises degradation) and the granted-pairs query lives in
``PermissionRepository.granted_pairs`` (identical SQL).

The gate logic itself (fail-closed check order, superuser bypass,
deny-list logging/metrics/span attributes, ``disable_auth`` inert branch)
stays byte-identical — only the data access is replaced. Parity guards
(green from the start) pin the historical 403/401 shapes; the repository
spy / cache-shape tests encode the NEW seams and are red before the
rewiring (import of ``PermissionRepository`` inside the tests).
"""

from __future__ import annotations

from collections.abc import Iterator
from types import SimpleNamespace

import app.shared.redis as shared_redis
import pytest
from app.api.v1.projects import router as projects_router
from app.identity.auth import _get_token_service
from app.identity.models import User
from app.identity.rbac import Role, RoleBinding
from app.identity.seed import seed_roles
from app.identity.token_service import TokenService
from app.shared.config import get_settings
from app.shared.database import get_session
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.conftest import _override_session, _TestSession, make_test_app

TS = TokenService(secret_key="rbac-unification-secret")
_MEMBER_EMAIL = "member-unif@example.com"
_OWNER_EMAIL = "owner-unif@example.com"


class _MemRedis:
    """In-memory cache stand-in — hermetic tests must not need a live Redis."""

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


def _add_user(db, email: str, role_name: str | None) -> User:  # noqa: ANN001
    user = User(email=email, password_hash="x" * 60, display_name=email.split("@")[0])
    db.add(user)
    db.flush()
    if role_name is not None:
        role = db.query(Role).filter_by(name=role_name).first()
        assert role is not None, f"role {role_name} not seeded"
        db.add(RoleBinding(user_id=user.id, role_id=role.id))
    db.commit()
    return user


def _enable_enforcement(monkeypatch: pytest.MonkeyPatch) -> None:
    """Gates are inert under UPCP_DISABLE_AUTH (conftest default) — turn on."""
    monkeypatch.setattr(get_settings(), "disable_auth", False)


@pytest.fixture()
def env(monkeypatch: pytest.MonkeyPatch) -> Iterator[SimpleNamespace]:
    """Gated app (web_auth blanket + projects router) with member/owner users."""
    _enable_enforcement(monkeypatch)
    app = make_test_app(projects_router, protect=True)
    app.dependency_overrides[_get_token_service] = lambda: TS
    db = _TestSession()
    seed_roles(db)
    member = _add_user(db, _MEMBER_EMAIL, "Member")
    owner = _add_user(db, _OWNER_EMAIL, "Owner")

    yield SimpleNamespace(
        app=app,
        client=TestClient(app),
        db=db,
        member=member,
        owner=owner,
        member_h={"Authorization": f"Bearer {TS.create_access_token(member.id)}"},
        owner_h={"Authorization": f"Bearer {TS.create_access_token(owner.id)}"},
    )
    db.query(User).filter(User.email.in_((_MEMBER_EMAIL, _OWNER_EMAIL))).delete(
        synchronize_session=False
    )
    db.commit()
    db.close()


def _spy_granted_pairs(monkeypatch: pytest.MonkeyPatch) -> dict[str, int]:
    """Count PermissionRepository.granted_pairs calls (class-level seam)."""
    from app.identity.repositories import PermissionRepository

    calls = {"n": 0}
    original = PermissionRepository.granted_pairs

    def counting(self: PermissionRepository, user_id: str) -> list[list[str]]:
        calls["n"] += 1
        return original(self, user_id)

    monkeypatch.setattr(PermissionRepository, "granted_pairs", counting)
    return calls


# ── Positives: permitted mutation passes the gate ───────────────────


def test_owner_mutation_passes_gate(env: SimpleNamespace) -> None:
    resp = env.client.post(
        "/api/v1/projects", json={"name": "Owner-Unif-Proj"}, headers=env.owner_h
    )
    assert resp.status_code in (200, 201), f"owner POST -> {resp.status_code}: {resp.text[:200]}"


# ── Negatives: historical 403/401 shapes, byte-parity guards ────────


def test_member_mutation_forbidden_with_historical_detail(env: SimpleNamespace) -> None:
    resp = env.client.post(
        "/api/v1/projects", json={"name": "Member-Unif-Proj"}, headers=env.member_h
    )
    assert resp.status_code == 403, resp.text
    assert resp.json()["detail"] == "Insufficient permissions"


def test_missing_principal_rejected_401(monkeypatch: pytest.MonkeyPatch) -> None:
    """No identity on the request (gate without middleware) → fail-closed 401."""
    _enable_enforcement(monkeypatch)
    app = FastAPI()
    app.include_router(projects_router, prefix="/api/v1")
    app.dependency_overrides[get_session] = _override_session

    resp = TestClient(app).post("/api/v1/projects", json={"name": "anon"})
    assert resp.status_code == 401, resp.text
    assert resp.json()["detail"] == "Missing authentication token"
    assert resp.headers.get("www-authenticate") == "Bearer"


# ── Boundaries: Redis outage + corrupt cache → DB fallback ──────────


def test_redis_outage_permission_falls_back_to_db(
    env: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(shared_redis, "get_redis_client", lambda: _BrokenRedis())
    denied = env.client.post("/api/v1/projects", json={"name": "Outage-M"}, headers=env.member_h)
    assert denied.status_code == 403, f"outage must not break the gate: {denied.text}"
    allowed = env.client.post("/api/v1/projects", json={"name": "Outage-O"}, headers=env.owner_h)
    assert allowed.status_code in (200, 201), f"owner under outage -> {allowed.status_code}"


@pytest.mark.parametrize(
    "garbage",
    ["{broken json", "42", '{"not": "a list"}'],
    ids=["parse-fail", "scalar", "object"],
)
def test_corrupt_cache_value_falls_back_to_db(
    env: SimpleNamespace,
    monkeypatch: pytest.MonkeyPatch,
    garbage: str,
) -> None:
    """Defensive parsing (pre-existing contract): unparseable/non-list cache
    payloads degrade to the granted-pairs query instead of crashing (500)."""
    fake = _MemRedis()
    monkeypatch.setattr(shared_redis, "get_redis_client", lambda: fake)
    calls = _spy_granted_pairs(monkeypatch)
    key = f"rbac:user_perms:{env.member.id}"
    fake.store[key] = garbage

    resp = env.client.post("/api/v1/projects", json={"name": "Corrupt-M"}, headers=env.member_h)

    assert resp.status_code == 403, f"corrupt cache must fall back, not fail: {resp.text}"
    assert calls["n"] == 1, f"corrupt cache must read the DB once, got {calls['n']}"


# ── AC: cache-spy on the permission path ────────────────────────────


def test_second_permission_check_served_from_cache(
    env: SimpleNamespace, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Cache-spy: cold gate = one granted-pairs query; warm = zero; the
    entry lands under the historical key with TTL 60."""
    import json

    fake = _MemRedis()
    monkeypatch.setattr(shared_redis, "get_redis_client", lambda: fake)
    calls = _spy_granted_pairs(monkeypatch)

    first = env.client.post("/api/v1/projects", json={"name": "Spy-1"}, headers=env.member_h)
    assert first.status_code == 403, first.text
    assert calls["n"] == 1, f"cold gate must query granted pairs once, got {calls['n']}"

    second = env.client.post("/api/v1/projects", json={"name": "Spy-2"}, headers=env.member_h)
    assert second.status_code == 403, second.text
    assert calls["n"] == 1, f"warm gate must be served from cache, DB reads={calls['n']}"

    key = f"rbac:user_perms:{env.member.id}"
    assert key in fake.store, f"historical cache key missing: {sorted(fake.store)}"
    assert fake.ttls[key] == 60, f"TTL must stay 60s, got {fake.ttls[key]}"
    cached = json.loads(fake.store[key])
    assert isinstance(cached, list) and all(
        isinstance(pair, list) and len(pair) == 2 for pair in cached
    ), f"JSON pair encoding changed: {cached!r}"
    assert ["update", "component"] in cached, "Member's update:component grant must be cached"
