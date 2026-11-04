"""RBAC enforcement — SPEC-0027 §3.1 / TASK-0145 (red → green).

Member (no project permissions) gets 403 — not 404/200 — on
admin-dangerous project mutations; Owner passes; superusers bypass gates
(seeder/setup admins hold no RoleBinding by design); unknown subjects are
rejected 401 on mutations; ungated reads stay any-authenticated; and the
gates are inert when ``UPCP_DISABLE_AUTH=true`` (hermetic test mode —
mirrors ``web_auth``'s early return and main.py not mounting the guard
then).

New symbols are imported inside tests so the file collects before the
implementation exists.
"""

from __future__ import annotations

from types import SimpleNamespace

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

TS = TokenService(secret_key="rbac-test-secret")


def _enable_enforcement(monkeypatch: pytest.MonkeyPatch) -> None:
    """Gates are inert under UPCP_DISABLE_AUTH (conftest default) — turn on."""
    monkeypatch.setattr(get_settings(), "disable_auth", False)


def _add_user(db, email: str, role_name: str | None) -> User:
    user = User(email=email, password_hash="x" * 60, display_name=email.split("@")[0])
    db.add(user)
    db.flush()
    if role_name is not None:
        role = db.query(Role).filter_by(name=role_name).first()
        assert role is not None, f"role {role_name} not seeded"
        db.add(RoleBinding(user_id=user.id, role_id=role.id))
    db.commit()
    return user


def _client_with_identity() -> SimpleNamespace:
    """App with the web_auth blanket (TASK-0169); gates follow the caller's flag."""
    app = make_test_app(projects_router, protect=True)
    app.dependency_overrides[_get_token_service] = lambda: TS
    return SimpleNamespace(app=app, client=TestClient(app))


@pytest.fixture()
def env(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    _enable_enforcement(monkeypatch)

    ns = _client_with_identity()
    db = _TestSession()
    seed_roles(db)
    member = _add_user(db, "member-rbac@example.com", "Member")
    owner = _add_user(db, "owner-rbac@example.com", "Owner")

    member_h = {"Authorization": f"Bearer {TS.create_access_token(member.id)}"}
    owner_h = {"Authorization": f"Bearer {TS.create_access_token(owner.id)}"}
    project = ns.client.post("/api/v1/projects", json={"name": "RBAC-Proj"}, headers=owner_h).json()
    assert "id" in project, f"owner project create failed: {project}"

    yield SimpleNamespace(client=ns.client, member=member_h, owner=owner_h, project=project, db=db)
    db.close()


# ── Finding 1: Member is refused with 403, before resource lookup ──


def test_member_patch_project_forbidden(env) -> None:
    resp = env.client.patch(
        f"/api/v1/projects/{env.project['id']}",
        json={"name": "nope"},
        headers=env.member,
    )
    assert resp.status_code == 403, (
        f"Member PATCH project -> {resp.status_code} (404/200 = finding 1): {resp.text[:200]}"
    )


def test_member_create_project_forbidden(env) -> None:
    resp = env.client.post("/api/v1/projects", json={"name": "Member-Proj"}, headers=env.member)
    assert resp.status_code == 403, f"Member POST project -> {resp.status_code}"


def test_member_delete_project_forbidden(env) -> None:
    resp = env.client.delete(f"/api/v1/projects/{env.project['id']}", headers=env.member)
    assert resp.status_code == 403, f"Member DELETE project -> {resp.status_code}"


def test_user_without_any_binding_forbidden(monkeypatch: pytest.MonkeyPatch) -> None:
    """Seeded non-superuser identities (authz member fixture) hold no bindings."""
    _enable_enforcement(monkeypatch)
    ns = _client_with_identity()
    db = _TestSession()
    seed_roles(db)
    orphan = _add_user(db, "orphan-rbac@example.com", None)

    resp = ns.client.post(
        "/api/v1/projects",
        json={"name": "Orphan-Proj"},
        headers={"Authorization": f"Bearer {TS.create_access_token(orphan.id)}"},
    )
    assert resp.status_code == 403, f"binding-less non-superuser POST -> {resp.status_code}"
    db.close()


# ── Positive controls ─────────────────────────────────────────────


def test_owner_mutations_allowed(env) -> None:
    created = env.client.post("/api/v1/projects", json={"name": "Owner-Proj"}, headers=env.owner)
    assert created.status_code in (200, 201), f"Owner POST -> {created.status_code}"
    patched = env.client.patch(
        f"/api/v1/projects/{env.project['id']}",
        json={"name": "Owner-Renamed"},
        headers=env.owner,
    )
    assert patched.status_code == 200, f"Owner PATCH -> {patched.status_code}"


def test_member_reads_stay_allowed(env) -> None:
    resp = env.client.get("/api/v1/projects", headers=env.member)
    assert resp.status_code == 200, f"Member GET projects -> {resp.status_code}"


def test_superuser_without_binding_bypasses_gates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Seeder/setup admins are superusers with no RoleBinding — bypass, not backfill.

    Backfilling Owner onto every binding-less user would also grant it to
    the deliberately permission-less seeder members and destroy the authz
    negative control (SPEC-0027 §3.1 deviation).
    """
    _enable_enforcement(monkeypatch)
    ns = _client_with_identity()
    db = _TestSession()
    seed_roles(db)
    admin = User(
        email="superuser-rbac@example.com",
        password_hash="x" * 60,
        display_name="Superuser",
        is_superuser=True,
    )
    db.add(admin)
    db.commit()

    resp = ns.client.post(
        "/api/v1/projects",
        json={"name": "Superuser-Proj"},
        headers={"Authorization": f"Bearer {TS.create_access_token(admin.id)}"},
    )
    assert resp.status_code in (200, 201), (
        f"superuser POST project -> {resp.status_code} (expected bypass)"
    )
    db.close()


# ── Fail-closed identity checks ───────────────────────────────────


def test_write_without_identity_rejected_401(monkeypatch: pytest.MonkeyPatch) -> None:
    """No auth middleware at all → dependency must fail closed (401)."""
    _enable_enforcement(monkeypatch)
    app = FastAPI()
    app.include_router(projects_router, prefix="/api/v1")
    app.dependency_overrides[get_session] = _override_session
    resp = TestClient(app).post("/api/v1/projects", json={"name": "anon"})
    assert resp.status_code == 401, (
        f"anonymous POST /projects -> {resp.status_code}, expected fail-closed 401"
    )


def test_unknown_subject_mutation_rejected_401(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Valid-signature token whose sub has no user row → 401 on a mutation.

    Finding 2 (TASK-0146) closed: the middleware user-existence check
    rejects such tokens before the route — this pins the end-to-end 401.
    """
    _enable_enforcement(monkeypatch)
    ns = _client_with_identity()
    db = _TestSession()
    seed_roles(db)

    resp = ns.client.post(
        "/api/v1/projects",
        json={"name": "Ghost-Proj"},
        headers={
            "Authorization": f"Bearer {TS.create_access_token('00000000-0000-4000-8000-00000000dead')}"
        },
    )
    assert resp.status_code == 401, f"unknown-subject mutation -> {resp.status_code}"
    db.close()


def test_inactive_user_mutation_rejected_401(monkeypatch: pytest.MonkeyPatch) -> None:
    """Disabled user with an Owner binding still gets 401 — active check first."""
    _enable_enforcement(monkeypatch)
    ns = _client_with_identity()
    db = _TestSession()
    seed_roles(db)
    user = _add_user(db, "inactive-rbac@example.com", "Owner")
    user.is_active = False
    db.commit()

    resp = ns.client.post(
        "/api/v1/projects",
        json={"name": "Inactive-Proj"},
        headers={"Authorization": f"Bearer {TS.create_access_token(user.id)}"},
    )
    assert resp.status_code == 401, f"inactive-user mutation -> {resp.status_code}"
    db.close()


# ── Hermetic mode: gates must be inert under UPCP_DISABLE_AUTH ────


def test_gates_inert_when_auth_disabled() -> None:
    """conftest sets UPCP_DISABLE_AUTH=true — anonymous mutations keep working.

    No settings monkeypatch here: this pins the default hermetic contract
    that hundreds of existing tests (open clients, no auth guard) rely on.
    """
    app = make_test_app(projects_router)  # no auth blanket, auth flag on
    assert get_settings().disable_auth is True, "test precond: hermetic auth off"
    resp = TestClient(app).post("/api/v1/projects", json={"name": "Open-Proj"})
    assert resp.status_code in (200, 201), (
        f"anonymous POST with disable_auth=true -> {resp.status_code}; "
        "gates must not fire when the auth stack is disabled"
    )
