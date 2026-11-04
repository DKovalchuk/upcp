"""Agent-surface auth — blanket default-deny, scope enforcement, hermetic parity.

SPEC-0028 S28.3 (AC4/AC6) / TASK-0170. RED first: new symbols are imported
inside the tests so the module collects and fails per case.

Layers:

- ``surface_app`` — production composition (``include_surfaces``) on a fresh
  ``FastAPI``: registry-attached blanket + router scope gates, WITHOUT the
  pre-retirement middleware — exact 401/403 details are deterministic in
  every commit of this task;
- real ``app.main`` — status-level lifecycle net (the still-mounted
  middleware may answer first with its own folded details; exact canonical
  details are pinned on ``surface_app``);
- simple own apps — ``request.state`` principal, exactly one verification
  when blanket and handler dependency share a request, and the hermetic
  ``disable_auth`` decision (blanket + scope gate inert; handler-level
  ``get_current_agent`` keeps enforcing — pinned by
  ``test_identity_agent_dependency.test_missing_header_rejected``).
"""

from __future__ import annotations

import hashlib
import logging
from collections.abc import Generator
from datetime import UTC, datetime
from unittest.mock import patch
from uuid import uuid4

import pytest
from app.api.registry import include_surfaces
from app.identity.agents import Agent, AgentToken
from app.shared.config import get_settings
from app.shared.database import get_session
from fastapi import Depends, FastAPI, Request
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

_FAKE = "00000000-0000-0000-0000-000000000000"
MCP_TOOLS = "/mcp/tools"
AGENT_ME = "/api/v1/agent/me"
WORKFLOW_CLAIMS = f"/api/v1/tasks/{_FAKE}/claims"
PAST = datetime(2020, 1, 1, tzinfo=UTC)

CANONICAL: dict[str, str] = {
    "missing": "Missing agent token",
    "unknown": "Invalid agent token",
    "revoked": "Agent token has been revoked",
    "expired": "Agent token has expired",
    "inactive": "Agent not found or inactive",
    "scope": "Insufficient scope",
}


# ── Harness ───────────────────────────────────────────────────────────────


@pytest.fixture()
def auth_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """Auth deps evaluate the flag per request — turn the guard ON (AC1 style)."""
    monkeypatch.setattr(get_settings(), "disable_auth", False)


def _seed_token(
    db: Session,
    *,
    scopes: object | None = None,
    revoked_at: datetime | None = None,
    expires_at: datetime | None = None,
    active: bool = True,
) -> str:
    """Commit an agent + token; return the raw token value."""
    raw = f"raw-{uuid4().hex}"
    agent = Agent(name=f"sa-{uuid4().hex[:8]}", description="surface-auth", created_by=None)
    agent.is_active = active
    db.add(agent)
    db.flush()
    db.add(
        AgentToken(
            agent_id=agent.id,
            token_hash=hashlib.sha256(raw.encode()).hexdigest(),
            name="t",
            scopes=scopes,
            revoked_at=revoked_at,
            expires_at=expires_at,
        )
    )
    db.commit()
    return raw


def _pin_db(app: FastAPI, db: Session) -> FastAPI:
    def _override() -> Generator[Session, None, None]:
        yield db

    app.dependency_overrides[get_session] = _override
    return app


def _surface_app(db: Session) -> FastAPI:
    """Production composition (registry blankets + router gates), DB seam pinned."""
    app = FastAPI()
    include_surfaces(app)
    return _pin_db(app, db)


def _main_client() -> TestClient:
    from app.main import app  # lazy: shared instance, no import-order dance

    return TestClient(app, raise_server_exceptions=False)


# ── AC4: canonical 401 details through the registry-attached blanket ──────


def test_missing_header_canonical_401_on_every_agent_route(
    auth_enabled: None, db_session: Session
) -> None:
    client = TestClient(_surface_app(db_session))
    for path in (MCP_TOOLS, AGENT_ME, WORKFLOW_CLAIMS):
        resp = client.get(path)
        assert resp.status_code == 401, f"{path} -> {resp.status_code}: {resp.text[:160]}"
        assert resp.json()["detail"] == CANONICAL["missing"], path


@pytest.mark.parametrize(
    ("seed_kwargs", "detail_key"),
    [
        ({"scopes": None}, "unknown"),  # the header below matches no row
        ({"revoked_at": datetime.now(UTC)}, "revoked"),
        ({"expires_at": PAST}, "expired"),
        ({"active": False}, "inactive"),
    ],
    ids=["unknown", "revoked", "expired", "inactive-agent"],
)
def test_lifecycle_rejections_canonical_401(
    auth_enabled: None, db_session: Session, seed_kwargs: dict, detail_key: str
) -> None:
    raw = _seed_token(db_session, **seed_kwargs)
    headers = {"X-Agent-Token": "never-issued-value" if detail_key == "unknown" else raw}
    resp = TestClient(_surface_app(db_session)).get(MCP_TOOLS, headers=headers)
    assert resp.status_code == 401, resp.text
    assert resp.json()["detail"] == CANONICAL[detail_key]


# ── AC6: scope matrix per router ──────────────────────────────────────────


def test_scope_missing_denies_with_403_and_observability(
    auth_enabled: None, db_session: Session, caplog: pytest.LogCaptureFixture
) -> None:
    raw = _seed_token(db_session, scopes=[])  # production shape: list[str]
    client = TestClient(_surface_app(db_session))
    with caplog.at_level(logging.WARNING, logger="app.identity.agent_auth"):
        resp = client.get(MCP_TOOLS, headers={"X-Agent-Token": raw})
    assert resp.status_code == 403, resp.text
    assert resp.json()["detail"] == CANONICAL["scope"]

    from app.shared.metrics import agent_scope_denials_total  # new in TASK-0170

    assert agent_scope_denials_total.labels(scope="agent:mcp")._value.get() >= 1
    assert any(
        r.levelno == logging.WARNING
        and getattr(r, "action", "") == "auth.scope_denied"
        and "agent:mcp" in r.getMessage()
        for r in caplog.records
    ), "scope denial must emit a structured warning (permissions.py style)"


def test_scope_present_allows_each_router(auth_enabled: None, db_session: Session) -> None:
    client = TestClient(_surface_app(db_session))
    ok_mcp = _seed_token(db_session, scopes=["agent:mcp"])
    assert client.get(MCP_TOOLS, headers={"X-Agent-Token": ok_mcp}).status_code == 200
    ok_self = _seed_token(db_session, scopes=["agent:self"])
    assert client.get(AGENT_ME, headers={"X-Agent-Token": ok_self}).status_code == 200
    ok_wf = _seed_token(db_session, scopes=["agent:workflow"])
    resp = client.get(WORKFLOW_CLAIMS, headers={"X-Agent-Token": ok_wf})
    assert resp.status_code == 404, "workflow scope passes the auth stage (lookup follows)"


def test_wrong_scope_denied_per_router(auth_enabled: None, db_session: Session) -> None:
    client = TestClient(_surface_app(db_session))
    cross = _seed_token(db_session, scopes=["agent:self"])
    assert client.get(MCP_TOOLS, headers={"X-Agent-Token": cross}).status_code == 403
    wf_only = _seed_token(db_session, scopes=["agent:workflow"])
    resp = client.get(AGENT_ME, headers={"X-Agent-Token": wf_only})
    assert resp.status_code == 403
    assert resp.json()["detail"] == CANONICAL["scope"]
    resp = client.get(WORKFLOW_CLAIMS, headers={"X-Agent-Token": cross})
    assert resp.status_code == 403, resp.text


def test_scope_shape_policy(auth_enabled: None, db_session: Session) -> None:
    """Stored shapes: None grandfathered; list = membership; dict = truthy key."""
    client = TestClient(_surface_app(db_session))
    legacy = _seed_token(db_session, scopes=None)
    assert client.get(MCP_TOOLS, headers={"X-Agent-Token": legacy}).status_code == 200
    dict_on = _seed_token(db_session, scopes={"agent:mcp": True})
    assert client.get(MCP_TOOLS, headers={"X-Agent-Token": dict_on}).status_code == 200
    dict_off = _seed_token(db_session, scopes={"agent:mcp": False})
    assert client.get(MCP_TOOLS, headers={"X-Agent-Token": dict_off}).status_code == 403


# ── Principal state + single execution ────────────────────────────────────


def test_blanket_sets_principal_state(auth_enabled: None, db_session: Session) -> None:
    from app.identity.agent_auth import agent_auth  # new in TASK-0170

    raw = _seed_token(db_session, scopes=None)
    app = FastAPI(dependencies=[Depends(agent_auth)])

    @app.get("/echo-state")
    def echo(request: Request) -> dict[str, object]:
        return {
            "agent_id": request.state.agent_id,
            "agent_name": request.state.agent_name,
            "auth_type": request.state.auth_type,
            "api_surface": request.state.api_surface,
        }

    resp = TestClient(_pin_db(app, db_session)).get("/echo-state", headers={"X-Agent-Token": raw})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["auth_type"] == "agent"
    assert body["api_surface"] == "agent"
    assert body["agent_id"] and body["agent_name"]


def test_blanket_and_handler_share_one_verification(
    auth_enabled: None, db_session: Session
) -> None:
    from app.identity.agent_auth import agent_auth, get_current_agent
    from app.identity.agent_token_service import AgentTokenService
    from app.identity.dependencies import CurrentAgent

    raw = _seed_token(db_session, scopes=None)
    app = FastAPI(dependencies=[Depends(agent_auth)])

    @app.get("/twice")
    def twice(agent: CurrentAgent = Depends(get_current_agent)) -> dict[str, str]:
        return {"agent_id": agent.agent_id}

    calls: list[object] = []
    original = AgentTokenService.verify_detailed

    def spy(self: AgentTokenService, *args: object, **kwargs: object) -> object:
        calls.append(self)
        return original(self, *args, **kwargs)

    with patch.object(AgentTokenService, "verify_detailed", spy):
        resp = TestClient(_pin_db(app, db_session)).get("/twice", headers={"X-Agent-Token": raw})

    assert resp.status_code == 200, resp.text
    assert len(calls) == 1, f"exactly ONE verification per request, got {len(calls)}"


# ── Hermetic disable_auth decision (documented in the task evidence) ──────


def test_blanket_inert_under_disable_auth(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Flag ON: the blanket skips — parity with the middleware not being mounted."""
    from app.identity.agent_auth import agent_auth

    monkeypatch.setattr(get_settings(), "disable_auth", True)
    app = FastAPI(dependencies=[Depends(agent_auth)])

    @app.get("/open")
    def open_() -> dict[str, str]:
        return {"ok": "true"}

    assert TestClient(app).get("/open").status_code == 200


def test_scope_gate_inert_under_disable_auth(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Bare ``create_mcp_router`` sites stay hermetically open (guard inert)."""
    from app.mcp.server import create_mcp_router

    monkeypatch.setattr(get_settings(), "disable_auth", True)
    app = FastAPI()
    app.include_router(create_mcp_router(), prefix="/mcp")
    assert TestClient(app).get(MCP_TOOLS).status_code == 200


def test_handler_dependency_keeps_enforcing_under_disable_auth(db_session: Session) -> None:
    """The asymmetry pin: handler-level get_current_agent never consults the flag."""
    from app.identity.agent_auth import get_current_agent
    from app.identity.dependencies import CurrentAgent

    app = FastAPI()

    @app.get("/handler")
    def handler(agent: CurrentAgent = Depends(get_current_agent)) -> dict[str, str]:
        return {"agent_id": agent.agent_id}

    resp = TestClient(app).get("/handler")
    assert resp.status_code == 401
    assert resp.json()["detail"] == CANONICAL["missing"]


# ── Real production app: status-level lifecycle net ───────────────────────


def test_real_main_agent_surface_lifecycle(auth_enabled: None, db_session: Session) -> None:
    """app.main: every agent-surface class answers its documented status.

    Statuses are mechanism-agnostic (middleware pre-retirement, dependency
    post-retirement); exact details are pinned on ``surface_app`` above, so
    this test survives the TASK-0170 retirement commit unchanged.
    """
    client = _main_client()
    seeds = {
        "missing": None,
        "unknown": {"X-Agent-Token": "never-issued"},
        "revoked": {"X-Agent-Token": _seed_token(db_session, revoked_at=datetime.now(UTC))},
        "expired": {"X-Agent-Token": _seed_token(db_session, expires_at=PAST)},
        "inactive": {"X-Agent-Token": _seed_token(db_session, active=False)},
    }
    for cls, headers in seeds.items():
        resp = client.get(MCP_TOOLS, headers=headers or {})
        assert resp.status_code == 401, f"{cls} -> {resp.status_code}"

    under = _seed_token(db_session, scopes=["agent:self"])
    assert client.get(MCP_TOOLS, headers={"X-Agent-Token": under}).status_code == 403
    ok = _seed_token(db_session, scopes=["agent:mcp"])
    assert client.get(MCP_TOOLS, headers={"X-Agent-Token": ok}).status_code == 200


# ── AC6: issuance fail-closed — a NEW key can never be scopeless ──────────
# (aspect-review FIX 1: body default ``scopes=None`` used to store NULL,
#  which the scope gate grandfathers → omission silently meant ALLOW.)


def _issue_key(db: Session, *, scopes: list[str] | None = None) -> tuple[str, str]:
    """Issue a key through the REAL endpoint function; return (raw, token_id)."""
    from app.identity.agent_endpoints import AgentTokenCreate, create_agent_token
    from app.identity.dependencies import CurrentUser
    from app.identity.models import User

    # The ownership gate re-loads the owner from the user table (its
    # superuser bypass is table-backed), so seed a real admin row.
    owner = User(
        email=f"iss-{uuid4().hex[:10]}@issuance.local",
        password_hash="x" * 60,
        display_name="Issuance",
        is_superuser=True,
    )
    db.add(owner)
    db.flush()
    agent = Agent(
        name=f"iss-{uuid4().hex[:8]}",
        description="issuance",
        created_by=str(owner.id),
    )
    agent.is_active = True
    db.add(agent)
    db.commit()
    cu = CurrentUser(user_id=str(owner.id), email=owner.email, is_superuser=True)
    issued = create_agent_token(
        str(agent.id), AgentTokenCreate(name="issued", scopes=scopes), cu, db
    )
    return str(issued["token"]), str(issued["id"])


def test_key_issuance_without_scopes_stores_deny_all(db_session: Session) -> None:
    """Omission must store ``[]`` (deny-all), never NULL (grandfather-bait)."""
    _raw, token_id = _issue_key(db_session, scopes=None)
    row = db_session.get(AgentToken, token_id)
    assert row is not None, "issuance must commit the key row"
    assert row.scopes == [], f"scopeless-by-omission key would be grandfathered: {row.scopes!r}"


def test_key_issued_without_scopes_denied_by_scope_gate(
    auth_enabled: None, db_session: Session
) -> None:
    """A key issued without scopes grants NOTHING until scopes are granted."""
    raw, _token_id = _issue_key(db_session, scopes=None)
    resp = TestClient(_surface_app(db_session)).get(MCP_TOOLS, headers={"X-Agent-Token": raw})
    assert resp.status_code == 403, f"scopeless new key must be denied, got {resp.status_code}"
    assert resp.json()["detail"] == CANONICAL["scope"]


# ── AC4 cross-surface: one surface's credentials never work on the other ──
# (aspect-review FIX 8 — gap cases both directions.)


def test_web_bearer_jwt_is_rejected_on_agent_surface(
    auth_enabled: None, db_session: Session
) -> None:
    """A valid web JWT without X-Agent-Token → 401 at the agent blanket."""
    from app.identity.token_service import TokenService

    web_jwt = TokenService().create_access_token(str(uuid4()))
    resp = TestClient(_surface_app(db_session)).get(
        MCP_TOOLS, headers={"Authorization": f"Bearer {web_jwt}"}
    )
    assert resp.status_code == 401, resp.text
    assert resp.json()["detail"] == CANONICAL["missing"]


# ── AC11: raw X-Agent-Token values never reach log records ────────────────
# (aspect-review FIX 9 — mirrors test_web_auth_dependency's ``token not in
#  caplog.text`` assertions for the web surface.)


def test_agent_token_never_logged_on_denial(
    auth_enabled: None, db_session: Session, caplog: pytest.LogCaptureFixture
) -> None:
    """401 denial class: the raw key must not appear in any log record."""
    raw = _seed_token(db_session, revoked_at=datetime.now(UTC))
    client = TestClient(_surface_app(db_session))
    with caplog.at_level(logging.WARNING):
        resp = client.get(MCP_TOOLS, headers={"X-Agent-Token": raw})
    assert resp.status_code == 401, resp.text
    assert resp.json()["detail"] == CANONICAL["revoked"]
    assert raw not in caplog.text, "AC11: raw agent token leaked into logs"


def test_agent_token_never_logged_on_scope_refusal(
    auth_enabled: None, db_session: Session, caplog: pytest.LogCaptureFixture
) -> None:
    """403 scope refusal: the structured warning carries ids, never the key."""
    raw = _seed_token(db_session, scopes=[])
    client = TestClient(_surface_app(db_session))
    with caplog.at_level(logging.WARNING):
        resp = client.get(MCP_TOOLS, headers={"X-Agent-Token": raw})
    assert resp.status_code == 403, resp.text
    refusal = [r for r in caplog.records if getattr(r, "action", "") == "auth.scope_denied"]
    assert refusal, "scope refusal must stay observable"
    assert raw not in caplog.text, "AC11: raw agent token leaked into logs"
