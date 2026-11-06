"""Phase-B RBAC gate coverage — SPEC-0028 AC8 / TASK-0172 (red → green).

Parametrized from the inventory table (``tests/rbac_gates_matrix.py`` ↔
``tasks/TASK-0172-rbac-coverage.md``): one case per route-level
``require_permission`` gate (36), pinned five ways — viewer without the
pair → 403 with the exact detail; Owner (pair granted) → 2xx; superuser →
2xx (bypass, SPEC-0027 AC9); no principal on the request → the gate itself
must fail closed 401; disabled Owner → 401 (fail-closed order, SPEC-0027
§3.1 — never 403). Plus the SPEC-0027 AC2 read-regression set:
representative ungated GETs keep answering 200 for a read-only user.

Gate factories are imported inside tests so the file collects before the
implementation exists (red phase, same convention as test_rbac_enforcement).
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from app.identity.auth import _get_token_service
from app.identity.models import User
from app.identity.rbac import Role, RoleBinding
from app.identity.seed import seed_roles
from app.identity.token_service import TokenService
from app.shared.config import get_settings
from fastapi.testclient import TestClient

from tests.conftest import _TestSession, make_test_app
from tests.rbac_gates_matrix import DUMMY_IDS, GATES, ROUTERS, Chain, Gate, call_gate

TS = TokenService(secret_key="rbac-coverage-secret")


def _add_user(db, email: str, role_name: str | None, *, superuser: bool = False) -> User:
    user = User(
        email=f"{email}@gates.local",
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


@pytest.fixture()
def env(monkeypatch: pytest.MonkeyPatch, tmp_path) -> SimpleNamespace:
    """Auth ON (gates live); hermetic (no Redis, no outbound webhook I/O)."""
    monkeypatch.setattr(get_settings(), "disable_auth", False)
    monkeypatch.setattr(get_settings(), "upload_dir", str(tmp_path))
    from app.reporting.channels.webhook import WebhookChannel

    monkeypatch.setattr(WebhookChannel, "send", lambda *a, **k: None)  # no network in tests

    app = make_test_app(*ROUTERS, protect=True)
    app.dependency_overrides[_get_token_service] = lambda: TS
    client = TestClient(app)
    db = _TestSession()
    seed_roles(db)
    viewer = _add_user(db, "viewer", "Viewer")
    owner = _add_user(db, "owner", "Owner")
    disabled = _add_user(db, "disabled", "Owner")
    disabled.is_active = False
    db.commit()
    superuser = _add_user(db, "super", None, superuser=True)
    hdr = lambda u: {"Authorization": f"Bearer {TS.create_access_token(u.id)}"}  # noqa: E731
    yield SimpleNamespace(
        client=client,
        viewer=hdr(viewer),
        owner=hdr(owner),
        disabled=hdr(disabled),
        superuser=hdr(superuser),
        db=db,
    )
    db.close()


@pytest.mark.parametrize("gate", GATES, ids=[g.id for g in GATES])
def test_viewer_mutation_denied_403(env, gate: Gate) -> None:
    """Read-only role without the pair → gate answers 403 before the handler."""
    resp = call_gate(env.client, gate, env.viewer, DUMMY_IDS)
    assert resp.status_code == 403, (
        f"{gate.id}: viewer -> {resp.status_code} (expected gate 403): {resp.text[:200]}"
    )
    assert resp.json() == {"detail": "Insufficient permissions"}, resp.text[:200]


@pytest.mark.parametrize("gate", GATES, ids=[g.id for g in GATES])
def test_owner_mutation_allowed(env, gate: Gate) -> None:
    """Owner holds the pair (seeded) → the mutation reaches the handler."""
    chain = Chain(env.client, env.superuser)
    ids = {**DUMMY_IDS, **{k: chain.id(k) for k in gate.needs}}
    resp = call_gate(env.client, gate, env.owner, ids)
    assert resp.status_code in (200, 201, 204), (
        f"{gate.id}: owner -> {resp.status_code}: {resp.text[:300]}"
    )


@pytest.mark.parametrize("gate", GATES, ids=[g.id for g in GATES])
def test_superuser_mutation_allowed(env, gate: Gate) -> None:
    """Superuser bypass (SPEC-0027 AC9) holds for every Phase-B gate."""
    chain = Chain(env.client, env.superuser)
    ids = {**DUMMY_IDS, **{k: chain.id(k) for k in gate.needs}}
    resp = call_gate(env.client, gate, env.superuser, ids)
    assert resp.status_code in (200, 201, 204), (
        f"{gate.id}: superuser -> {resp.status_code}: {resp.text[:300]}"
    )


@pytest.mark.parametrize("gate", GATES, ids=[g.id for g in GATES])
def test_missing_principal_fails_closed_401(monkeypatch: pytest.MonkeyPatch, gate: Gate) -> None:
    """No web_auth blanket at all → the gate itself must 401 (not run the handler)."""
    monkeypatch.setattr(get_settings(), "disable_auth", False)
    app = make_test_app(*ROUTERS)
    resp = call_gate(TestClient(app), gate, {}, DUMMY_IDS)
    assert resp.status_code == 401, (
        f"{gate.id}: anonymous -> {resp.status_code} (expected fail-closed 401): {resp.text[:200]}"
    )


@pytest.mark.parametrize("gate", GATES, ids=[g.id for g in GATES])
def test_disabled_owner_fails_closed_401(env, gate: Gate) -> None:
    """Permission granted but subject disabled → 401, never 403 (§3.1 order)."""
    resp = call_gate(env.client, gate, env.disabled, DUMMY_IDS)
    assert resp.status_code == 401, (
        f"{gate.id}: disabled owner -> {resp.status_code} (expected 401): {resp.text[:200]}"
    )


def test_ungated_reads_stay_200_for_viewer(env) -> None:
    """SPEC-0027 AC2 regression baseline: representative GETs unchanged."""
    chain = Chain(env.client, env.superuser)
    reads = [
        "/api/v1/projects",
        f"/api/v1/projects/{chain.id('project')}",
        f"/api/v1/projects/{chain.id('project')}/components",
        f"/api/v1/projects/{chain.id('project')}/quality/stats",
        f"/api/v1/features/{chain.id('feature')}/tasks",
        "/api/v1/notifications",
        "/api/v1/notification-channels",
        "/api/v1/dashboard/stats",
        "/api/v1/analytics/velocity",
        "/api/v1/search?q=gate",
        "/api/v1/git-links?entity_type=task&entity_id=gate-entity",
    ]
    for path in reads:
        resp = env.client.get(path, headers=env.viewer)
        assert resp.status_code == 200, (
            f"ungated GET {path} -> {resp.status_code} (SPEC-0027 AC2 baseline moved)"
        )
