"""MCP principal binding — SPEC-0028 §3.4 (AC5) / TASK-0171. RED first.

The agent-auth blanket stamps ``request.state.agent_id`` on every agent
route (TASK-0170), but the JSON-RPC dispatch historically never saw it:
``tools/call`` took ``agent_id`` from tool ARGUMENTS, so authenticated
agent A could act as agent B. This file pins the binding contract:

- inventory: every tool whose schema declares ``agent_id`` is enumerated
  from ``get_tools()`` itself and the negative matrix is generated FROM
  that list (task AC);
- spoofing (AC5): A-authenticated ``tools/call`` with ``agent_id=B`` →
  JSON-RPC error ``-32001`` inside a normal HTTP 200 response;
- match: ``agent_id=A`` passes the binding for every inventoried tool;
- fail-closed: auth ON + no principal reaching the handler (mis-mounted
  router — scope gate bypassed through the FastAPI override seam) →
  ``-32001``;
- hermetic escape: ``disable_auth=true`` (conftest default) skips the
  binding entirely — bare ``create_mcp_router()`` mounts keep legacy
  behavior;
- observability: structured warning + span attrs on refusal;
- isolation: two concurrent clients as different agents — each request
  sees only its own principal (per-request ``request.state``).

Red note: the module imports only PRE-EXISTING symbols, so the file
collects cleanly before the implementation exists — red manifests as
assertion failures (6 spoof + missing-principal + observability +
concurrent-spoof cases).
"""

from __future__ import annotations

import hashlib
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

import pytest
from app.identity.agents import Agent, AgentToken
from app.identity.dependencies import get_agent_auth
from app.mcp.server import create_mcp_router
from app.mcp.tools import get_tools
from app.shared.config import get_settings
from app.shared.database import Base, get_session
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from tests.conftest import _override_session

MCP_PATH = "/mcp/"
MCP_SCOPE = "agent:mcp"
FORBIDDEN_CODE = -32001
MISMATCH_MSG = "Forbidden: agent identity mismatch"
NO_PRINCIPAL_MSG = "Forbidden: no authenticated principal"

# Inventory driven from the tool schemas themselves (task AC: the
# parametrized negative test is generated FROM this list).
AGENT_ID_TOOLS: list[str] = sorted(
    tool.name for tool in get_tools() if "agent_id" in tool.input_schema.properties
)
EXPECTED_AGENT_ID_TOOLS = {
    "claim_task",
    "release_task",
    "heartbeat_task",
    "request_clarification",
    "submit_task_for_review",
    "get_agent_inbox",
}


# ── Harness ───────────────────────────────────────────────────────────────


@pytest.fixture()
def auth_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """Auth deps evaluate the flag per request — turn the guard ON (AC1 style)."""
    monkeypatch.setattr(get_settings(), "disable_auth", False)


def _seed_agent(db: Session) -> tuple[str, str]:
    """Commit an active agent + agent:mcp token; return (raw token, agent_id)."""
    raw = f"raw-{uuid4().hex}"
    agent = Agent(name=f"pb-{uuid4().hex[:8]}", description="principal-binding", created_by=None)
    agent.is_active = True
    db.add(agent)
    db.flush()
    db.add(
        AgentToken(
            agent_id=agent.id,
            token_hash=hashlib.sha256(raw.encode()).hexdigest(),
            name="t",
            scopes=[MCP_SCOPE],
        )
    )
    db.commit()
    return raw, str(agent.id)


def _binding_app() -> FastAPI:
    """Production-like mount: agent blanket + router scope gate (TASK-0170)."""
    app = FastAPI()
    app.include_router(
        create_mcp_router(),
        prefix="/mcp",
        dependencies=[Depends(get_agent_auth())],
    )
    app.dependency_overrides[get_session] = _override_session
    return app


def _mis_mounted_app() -> FastAPI:
    """A router that reaches the JSON-RPC handler with NO auth context.

    The scope gate is disabled through FastAPI's documented
    ``dependency_overrides`` seam and no blanket is attached — exactly
    the mis-mounted-router situation the binding must fail closed on.
    """
    router = create_mcp_router()
    post = next(r for r in router.routes if "POST" in (r.methods or set()))
    gate = post.dependencies[0].dependency
    app = FastAPI()
    app.include_router(router, prefix="/mcp")
    app.dependency_overrides[gate] = lambda: None
    app.dependency_overrides[get_session] = _override_session
    return app


def _tools_call(
    client: TestClient,
    headers: dict[str, str],
    tool: str,
    arguments: dict[str, object],
    *,
    req_id: int = 1,
):  # noqa: ANN202 — httpx.Response
    return client.post(
        MCP_PATH,
        json={
            "jsonrpc": "2.0",
            "id": req_id,
            "method": "tools/call",
            "params": {"name": tool, "arguments": arguments},
        },
        headers=headers,
    )


def _error_of(resp) -> dict | None:  # noqa: ANN001
    body = resp.json()
    return body.get("error")


class _RecordingSpan:
    """Span spy: records set_attributes without a real tracer."""

    def __init__(self) -> None:
        self.attributes: dict[str, object] = {}

    def is_recording(self) -> bool:
        return True

    def set_attributes(self, attributes: dict[str, object]) -> None:
        self.attributes.update(attributes)


# ── Inventory (task AC) ───────────────────────────────────────────────────


def test_agent_id_tool_inventory_matches_expected() -> None:
    assert set(AGENT_ID_TOOLS) == EXPECTED_AGENT_ID_TOOLS, (
        f"inventory drift — update the task evidence table and this pin together: {AGENT_ID_TOOLS}"
    )


# ── AC5: spoofing rejected for EVERY inventoried tool ─────────────────────


@pytest.mark.parametrize("tool", AGENT_ID_TOOLS)
def test_spoofed_agent_id_rejected(auth_enabled: None, db_session: Session, tool: str) -> None:
    """A-authenticated call acting as B → JSON-RPC -32001 (HTTP stays 200)."""
    raw, _principal = _seed_agent(db_session)
    _other_raw, other = _seed_agent(db_session)
    client = TestClient(_binding_app())
    resp = _tools_call(client, {"X-Agent-Token": raw}, tool, {"agent_id": other})
    assert resp.status_code == 200, resp.text
    error = _error_of(resp)
    assert error, f"spoofed {tool} must be refused, got: {resp.text[:300]}"
    assert error["code"] == FORBIDDEN_CODE, resp.text
    assert error["message"] == MISMATCH_MSG, resp.text


@pytest.mark.parametrize("tool", AGENT_ID_TOOLS)
def test_matching_agent_id_passes_binding(
    auth_enabled: None, db_session: Session, tool: str
) -> None:
    """A-authenticated call with agent_id=A is never refused BY THE BINDING.

    The tool itself may still fail downstream (unknown task, etc.) — that
    lands in ``result.is_error``, never in a JSON-RPC ``error``.
    """
    raw, principal = _seed_agent(db_session)
    client = TestClient(_binding_app())
    resp = _tools_call(client, {"X-Agent-Token": raw}, tool, {"agent_id": principal})
    assert resp.status_code == 200, resp.text
    assert _error_of(resp) is None, resp.text
    if tool == "get_agent_inbox":
        assert resp.json()["result"]["is_error"] is False, resp.text


# ── Fail-closed: auth ON, no principal reaching the handler ───────────────


def test_tools_call_without_principal_rejected_when_auth_enabled(
    auth_enabled: None, db_session: Session
) -> None:
    """Mis-mounted router: handler reachable with auth ON and NO principal."""
    client = TestClient(_mis_mounted_app())
    resp = _tools_call(client, {}, "get_agent_inbox", {"agent_id": str(uuid4())})
    assert resp.status_code == 200, resp.text
    error = _error_of(resp)
    assert error, f"principal-less tools/call must be refused, got: {resp.text[:300]}"
    assert error["code"] == FORBIDDEN_CODE, resp.text
    assert error["message"] == NO_PRINCIPAL_MSG, resp.text


def test_no_credentials_401_at_entry(auth_enabled: None, db_session: Session) -> None:
    """Entry pin: the normal (gate + blanket) mount still 401s before dispatch."""
    client = TestClient(_binding_app())
    resp = _tools_call(client, {}, "get_agent_inbox", {"agent_id": str(uuid4())})
    assert resp.status_code == 401, resp.text
    assert resp.json()["detail"] == "Missing agent token", resp.text


# ── Hermetic escape (flag ON = conftest default) — binding skipped ────────


def test_binding_skipped_under_hermetic_disable_auth(db_session: Session) -> None:
    """Legacy behavior pinned: bare mount, no auth stack, spoof freely."""
    assert get_settings().disable_auth is True, "test precondition: hermetic mode"
    app = FastAPI()
    app.include_router(create_mcp_router(), prefix="/mcp")
    app.dependency_overrides[get_session] = _override_session
    client = TestClient(app)
    resp = _tools_call(client, {}, "get_agent_inbox", {"agent_id": "anyone-else"})
    assert resp.status_code == 200, resp.text
    assert _error_of(resp) is None, f"binding must be inert under disable_auth: {resp.text}"


# ── Observability: structured warning + span attrs ────────────────────────


def test_mismatch_emits_warning_and_span_attrs(
    auth_enabled: None,
    db_session: Session,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import opentelemetry.trace as otel_trace

    span = _RecordingSpan()
    monkeypatch.setattr(otel_trace, "get_current_span", lambda: span)

    raw, principal = _seed_agent(db_session)
    _other_raw, other = _seed_agent(db_session)
    client = TestClient(_binding_app())
    with caplog.at_level(logging.WARNING, logger="app.mcp.server"):
        resp = _tools_call(client, {"X-Agent-Token": raw}, "claim_task", {"agent_id": other})

    assert _error_of(resp) is not None, resp.text
    records = [r for r in caplog.records if getattr(r, "action", "") == "auth.principal_mismatch"]
    assert records, [getattr(r, "action", None) for r in caplog.records]
    assert principal in records[0].getMessage()
    assert "claim_task" in records[0].getMessage()
    assert span.attributes["upcp.auth.principal_mismatch"] is True
    assert span.attributes["upcp.auth.sub"] == principal


# ── Isolation: concurrent clients as different agents ─────────────────────


def _file_sessionmaker(db_path: Path) -> tuple[sessionmaker, object]:
    """FILE-backed sqlite engine: separate connections per request.

    The suite's shared StaticPool in-memory connection cannot serve
    concurrent writers (sqlite3 ``InterfaceError: API misuse`` — a
    test-infra limitation of the hermetic harness, not product behavior),
    so genuine concurrency for the auth + binding path needs its own
    engine with one connection per session.
    """
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False, "timeout": 5.0},
    )

    @event.listens_for(engine, "connect")
    def _enable_fk(dbapi_conn, _record):  # noqa: ANN001 — pysqlite connection
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine), engine


def test_principal_isolation_between_concurrent_clients(auth_enabled: None, tmp_path: Path) -> None:
    """Per-request state: each concurrent client sees only its own principal."""
    maker, engine = _file_sessionmaker(tmp_path / "binding.db")
    app = FastAPI()
    app.include_router(
        create_mcp_router(),
        prefix="/mcp",
        dependencies=[Depends(get_agent_auth())],
    )

    def _session_override():
        s = maker()
        try:
            yield s
            s.commit()
        except Exception:
            s.rollback()
            raise
        finally:
            s.close()

    app.dependency_overrides[get_session] = _session_override

    db = maker()
    try:
        a_raw, a_id = _seed_agent(db)
        b_raw, b_id = _seed_agent(db)
    finally:
        db.close()

    try:
        cases: list[tuple[str, str, bool]] = [
            (a_raw, a_id, True),  # A as A → accepted
            (b_raw, b_id, True),  # B as B → accepted
            (a_raw, b_id, False),  # A as B → refused
            (b_raw, a_id, False),  # B as A → refused
        ]

        def run(case: tuple[str, str, bool]):
            token, agent_arg, _should_pass = case
            client = TestClient(app)
            return _tools_call(
                client, {"X-Agent-Token": token}, "get_agent_inbox", {"agent_id": agent_arg}
            )

        with ThreadPoolExecutor(max_workers=len(cases)) as pool:
            results = [f.result() for f in [pool.submit(run, c) for c in cases]]
    finally:
        engine.dispose()

    for case, resp in zip(cases, results, strict=True):
        _token, agent_arg, should_pass = case
        error = _error_of(resp)
        if should_pass:
            assert error is None, f"agent {agent_arg} wrongly refused: {resp.text[:300]}"
        else:
            assert error is not None and error["code"] == FORBIDDEN_CODE, (
                f"agent {agent_arg} spoof not refused: {resp.text[:300]}"
            )


# ── AC5: identity args OUTSIDE the historical ``agent_id`` inventory ──────
# (aspect-review FIX 3: ``answered_by`` / ``created_by_id`` carried agent
#  identity but sat outside the binding — spoofable.)


def test_spoofed_answered_by_rejected(auth_enabled: None, db_session: Session) -> None:
    """A-authenticated answer_clarification claiming answered_by=B → -32001."""
    raw, _principal = _seed_agent(db_session)
    _other_raw, other = _seed_agent(db_session)
    client = TestClient(_binding_app())
    resp = _tools_call(
        client,
        {"X-Agent-Token": raw},
        "answer_clarification",
        {"clarification_id": str(uuid4()), "answer": "looks good", "answered_by": other},
    )
    assert resp.status_code == 200, resp.text
    error = _error_of(resp)
    assert error, f"spoofed answered_by must be refused by the BINDING, got: {resp.text[:300]}"
    assert error["code"] == FORBIDDEN_CODE, resp.text
    assert error["message"] == MISMATCH_MSG, resp.text


def test_spoofed_created_by_id_rejected(auth_enabled: None, db_session: Session) -> None:
    """A-authenticated attach_evidence claiming created_by_id=B → -32001."""
    raw, _principal = _seed_agent(db_session)
    _other_raw, other = _seed_agent(db_session)
    client = TestClient(_binding_app())
    resp = _tools_call(
        client,
        {"X-Agent-Token": raw},
        "attach_evidence",
        {
            "task_id": str(uuid4()),
            "type": "test_output",
            "title": "spoofed evidence",
            "created_by_type": "agent",
            "created_by_id": other,
        },
    )
    assert resp.status_code == 200, resp.text
    error = _error_of(resp)
    assert error, f"spoofed created_by_id must be refused by the BINDING, got: {resp.text[:300]}"
    assert error["code"] == FORBIDDEN_CODE, resp.text
    assert error["message"] == MISMATCH_MSG, resp.text


def test_matching_identity_args_pass_binding(auth_enabled: None, db_session: Session) -> None:
    """Own identity in answered_by / created_by_id is never refused BY THE BINDING
    (the tool itself may still fail downstream — that lands in ``result.is_error``)."""
    from app.delivery.models import Feature, Task
    from app.projects.models import Project

    raw, principal = _seed_agent(db_session)
    project = Project(name="pb-matching", slug="pb-matching")
    db_session.add(project)
    db_session.flush()
    feature = Feature(project_id=project.id, name="F", slug="f")
    db_session.add(feature)
    db_session.flush()
    task = Task(feature_id=feature.id, title="T", status="in_progress")
    db_session.add(task)
    db_session.commit()

    client = TestClient(_binding_app())
    answer = _tools_call(
        client,
        {"X-Agent-Token": raw},
        "answer_clarification",
        {"clarification_id": str(uuid4()), "answer": "ok", "answered_by": principal},
    )
    assert _error_of(answer) is None, answer.text
    evidence = _tools_call(
        client,
        {"X-Agent-Token": raw},
        "attach_evidence",
        {
            "task_id": str(task.id),
            "type": "test_output",
            "title": "own evidence",
            "created_by_type": "agent",
            "created_by_id": principal,
        },
    )
    assert _error_of(evidence) is None, evidence.text
    assert evidence.json()["result"]["is_error"] is False, evidence.text


# ── Class guard: a NEW identity-ish schema arg breaks until the map is ────
# extended (aspect-review FIX 3 — the declared map can never silently lag
# behind ``get_tools()``.)


# Tuned against the real inventory: matches exactly ``agent_id``,
# ``answered_by`` and ``created_by_id`` — and nothing else (e.g.
# ``created_by_type`` is a role discriminator, not an identity id).
IDENTITY_ARG_RE = re.compile(r"^(agent_id|.*_(by|by_id|owner_id|creator_id)|answered_by)$", re.I)


def test_identity_arg_class_guard_matches_declared_binding_map() -> None:
    from app.mcp.server import IDENTITY_ARGS

    declared = {
        prop
        for tool in get_tools()
        for prop in (tool.input_schema.properties or {})
        if IDENTITY_ARG_RE.match(prop)
    }
    assert declared == set(IDENTITY_ARGS), (
        f"schema/binding drift — extend IDENTITY_ARGS in app/mcp/server.py: "
        f"unmapped={sorted(declared - set(IDENTITY_ARGS))} "
        f"stale={sorted(set(IDENTITY_ARGS) - declared)}"
    )
