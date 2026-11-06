"""Role/superuser gate factories + reaper ops-endpoint — TASK-0172 (red → green).

``require_role`` has no production route yet (inventory in the task file:
no current route is role-semantic in practice), so it is pinned at factory
level with the manual cases from the test matrix: matching role passes;
wrong role → 403 ``{"detail": "Insufficient role"}``; missing principal →
401; ``UPCP_DISABLE_AUTH`` → inert; superuser bypass parity (SPEC-0027 §3.1).

``require_superuser`` IS applied — ``POST /api/v1/internal/reaper/tick``
(evidence: internal ops endpoint, no non-admin HTTP caller anywhere) —
so its cases run through the real route. Plus: every pair referenced by
the coverage matrix must exist in the seed catalog (seed drift guard).

Factories are imported inside tests so the file collects before the
implementation exists (red phase).
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from app.api.v1.reaper import router as reaper_router
from app.identity.auth import _get_token_service
from app.identity.models import User
from app.identity.rbac import Role, RoleBinding
from app.identity.seed import seed_roles
from app.identity.token_service import TokenService
from app.shared.config import get_settings
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient

from tests.conftest import _TestSession, make_test_app

TS = TokenService(secret_key="rbac-role-gates-secret")


def _add_user(db, email: str, role_name: str | None, *, superuser: bool = False) -> User:
    user = User(
        email=f"{email}@role-gates.local",
        password_hash="x" * 60,
        display_name=email,
        is_superuser=superuser,
    )
    db.add(user)
    db.flush()
    if role_name is not None:
        role = db.query(Role).filter_by(name=role_name).first()
        assert role is not None, f"role {role_name} not seeded"
        db.add(RoleBinding(user_id=user.id, role_id=role.id))
    db.commit()
    return user


def _principal_from_header(request: Request) -> None:
    """Stub for web_auth in factory probes: the gate only reads state.user_id."""
    user_id = request.headers.get("X-Test-User")
    if user_id is not None:
        request.state.user_id = user_id


def _probe_app(role: str) -> tuple[FastAPI, TestClient]:
    """App with one route gated by ``require_role(role)`` and NO web blanket:
    the probe feeds the principal itself, isolating the factory."""
    from app.identity.permissions import require_role

    app = make_test_app()  # fresh schema + session override, no auth blanket

    @app.get(
        "/probe",
        dependencies=[Depends(_principal_from_header), Depends(require_role(role))],
    )
    def probe() -> dict[str, bool]:
        return {"ok": True}

    return app, TestClient(app)


@pytest.fixture()
def role_env(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    monkeypatch.setattr(get_settings(), "disable_auth", False)
    _, client = _probe_app("Owner")  # BEFORE seeding: make_test_app drops tables
    db = _TestSession()
    seed_roles(db)
    holder = _add_user(db, "role-holder", "Owner")
    other = _add_user(db, "role-other", "Viewer")
    superuser = _add_user(db, "role-super", None, superuser=True)
    hdr = lambda u: {"X-Test-User": str(u.id)}  # noqa: E731
    yield SimpleNamespace(
        client=client, holder=hdr(holder), other=hdr(other), superuser=hdr(superuser), db=db
    )
    db.close()


def test_role_gate_allows_matching_role(role_env) -> None:
    resp = role_env.client.get("/probe", headers=role_env.holder)
    assert resp.status_code == 200, resp.text[:200]


def test_role_gate_rejects_wrong_role_403(role_env) -> None:
    resp = role_env.client.get("/probe", headers=role_env.other)
    assert resp.status_code == 403, resp.text[:200]
    assert resp.json() == {"detail": "Insufficient role"}


def test_role_gate_missing_principal_401(role_env) -> None:
    resp = role_env.client.get("/probe")
    assert resp.status_code == 401, resp.text[:200]


def test_role_gate_superuser_bypasses_without_binding(role_env) -> None:
    """Parity with require_permission: superusers hold full access (AC9)."""
    resp = role_env.client.get("/probe", headers=role_env.superuser)
    assert resp.status_code == 200, resp.text[:200]


def test_role_gate_inert_when_auth_disabled() -> None:
    """Hermetic parity branch: gates short-circuit under UPCP_DISABLE_AUTH.

    Deliberately fixture-free — ``role_env`` flips auth ON; this case needs
    conftest's hermetic default (no monkeypatch, no principal at all).
    """
    _, client = _probe_app("Owner")
    assert get_settings().disable_auth is True, "precondition: hermetic mode"
    resp = client.get("/probe")
    assert resp.status_code == 200, resp.text[:200]


# ── require_superuser on the reaper ops endpoint (real route) ────────


@pytest.fixture()
def reaper_env(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    monkeypatch.setattr(get_settings(), "disable_auth", False)
    app = make_test_app(reaper_router, protect=True)
    app.dependency_overrides[_get_token_service] = lambda: TS
    client = TestClient(app)
    db = _TestSession()
    seed_roles(db)
    owner = _add_user(db, "reaper-owner", "Owner")
    viewer = _add_user(db, "reaper-viewer", "Viewer")
    superuser = _add_user(db, "reaper-super", None, superuser=True)
    hdr = lambda u: {"Authorization": f"Bearer {TS.create_access_token(u.id)}"}  # noqa: E731
    yield SimpleNamespace(
        client=client, owner=hdr(owner), viewer=hdr(viewer), superuser=hdr(superuser), db=db
    )
    db.close()


def test_reaper_tick_owner_forbidden(reaper_env) -> None:
    """Owner (full permissions, not superuser) → 403 — route is superuser-only."""
    resp = reaper_env.client.post("/api/v1/internal/reaper/tick", headers=reaper_env.owner)
    assert resp.status_code == 403, f"owner tick -> {resp.status_code}: {resp.text[:200]}"
    assert resp.json() == {"detail": "Superuser required"}


def test_reaper_tick_superuser_allowed(reaper_env) -> None:
    resp = reaper_env.client.post("/api/v1/internal/reaper/tick", headers=reaper_env.superuser)
    assert resp.status_code == 200, f"superuser tick -> {resp.status_code}: {resp.text[:200]}"
    assert "stale" in resp.json()


def test_reaper_tick_viewer_forbidden(reaper_env) -> None:
    resp = reaper_env.client.post("/api/v1/internal/reaper/tick", headers=reaper_env.viewer)
    assert resp.status_code == 403, f"viewer tick -> {resp.status_code}: {resp.text[:200]}"


def test_reaper_tick_missing_principal_401(monkeypatch: pytest.MonkeyPatch) -> None:
    """No web blanket → the gate itself must fail closed 401."""
    monkeypatch.setattr(get_settings(), "disable_auth", False)
    app = make_test_app(reaper_router)
    resp = TestClient(app).post("/api/v1/internal/reaper/tick")
    assert resp.status_code == 401, f"anonymous tick -> {resp.status_code}"


def test_reaper_tick_inert_when_auth_disabled() -> None:
    """Hermetic mode (conftest default): the endpoint keeps working open."""
    app = make_test_app(reaper_router)
    assert get_settings().disable_auth is True, "precondition: hermetic mode"
    resp = TestClient(app).post("/api/v1/internal/reaper/tick")
    assert resp.status_code == 200, f"inert tick -> {resp.status_code}"


# ── Seed drift guard: every gated pair must exist in the catalog ─────


def test_every_matrix_pair_is_seeded() -> None:
    from app.identity.seed import DEFAULT_PERMISSIONS, ROLE_PERMISSIONS

    from tests.rbac_gates_matrix import GATES

    catalog = set(DEFAULT_PERMISSIONS)
    owner_grants = set(ROLE_PERMISSIONS["Owner"])
    for gate in GATES:
        pair = (gate.action, gate.resource)
        assert pair in catalog, f"pair {pair} missing from DEFAULT_PERMISSIONS (seed.py)"
        assert pair in owner_grants, f"pair {pair} not granted to Owner (owner positive fails)"
