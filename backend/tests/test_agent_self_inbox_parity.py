"""Characterization parity for the agent-self inbox — TASK-0176.

Written BEFORE the cross-context refactor: pins the exact response of
``GET /agent/inbox`` (own-agent scoping, unread filter, auth) so it stays
green UNMODIFIED once the query moves behind ``AgentActivityService``
(SPEC-0029 AC8).

Ownership boundary (agent-self): only the token's own agent's events are
returned — a foreign agent's rows never leak (contrast with the web-admin
tabs, which are open reads by design).
"""

import hashlib
import uuid
from types import SimpleNamespace

import app.audit.models  # noqa: F401
import app.gitread.models  # noqa: F401
import app.identity.agents  # noqa: F401
import app.identity.models  # noqa: F401
import app.identity.rbac  # noqa: F401
import app.quality.models  # noqa: F401
import app.reporting.models  # noqa: F401
import pytest
from app.api.v1.agent_self import router as self_router
from app.delivery.models import AgentInboxEvent
from app.identity.agents import Agent, AgentToken
from app.identity.models import User
from app.shared.database import Base, get_session
from app.shared.errors import register_error_handlers
from app.shared.text import new_id
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.conftest import _override_session, _test_engine, _TestSession

_RAW_TOKEN = "inbox-parity-token"
_OTHER_AGENT = "foreign-agent"
_EVENT_KEYS = {"id", "event_type", "task_id", "message", "is_read", "created_at"}


@pytest.fixture()
def inbox():
    """Agent-self app with a seeded agent + token (test_agent_self style)."""
    Base.metadata.drop_all(bind=_test_engine)
    Base.metadata.create_all(bind=_test_engine)
    app = FastAPI()
    register_error_handlers(app)
    app.include_router(self_router, prefix="/api/v1")
    app.dependency_overrides[get_session] = _override_session

    uid = uuid.uuid4().hex[:8]
    session = _TestSession()
    try:
        # agent.created_by is an FK: the owning user must exist first.
        session.add(
            User(
                id=f"u-{uid}",
                email=f"i-{uid}@x.com",
                password_hash="x",
                display_name="I",
            )
        )
        session.flush()
        agent = Agent(name=f"InboxAgent-{uid}", description="d", created_by=f"u-{uid}")
        session.add(agent)
        session.flush()
        session.add(
            AgentToken(
                id=f"tok-{uid}",
                agent_id=agent.id,
                token_hash=hashlib.sha256(_RAW_TOKEN.encode()).hexdigest(),
                name="t",
                scopes={"read": True, "write": True},
            )
        )
        session.commit()
        agent_id = agent.id
    finally:
        session.close()

    yield SimpleNamespace(client=TestClient(app), agent_id=agent_id)
    Base.metadata.drop_all(bind=_test_engine)
    Base.metadata.create_all(bind=_test_engine)


def _hdr() -> dict[str, str]:
    return {"X-Agent-Token": _RAW_TOKEN}


def _event(agent_id: str, *, message: str, is_read: bool = False) -> str:
    session = _TestSession()
    try:
        row = AgentInboxEvent(
            id=new_id(),
            agent_id=agent_id,
            event_type="task.assigned",
            message=message,
            is_read=is_read,
        )
        session.add(row)
        session.commit()
        return row.id
    finally:
        session.close()


class TestAgentSelfInbox:
    def test_returns_own_events_only(self, inbox) -> None:
        own = _event(inbox.agent_id, message="mine")
        _event(_OTHER_AGENT, message="foreign")
        resp = inbox.client.get("/api/v1/agent/inbox", headers=_hdr())
        assert resp.status_code == 200
        events = resp.json()["events"]
        assert len(events) == 1
        assert set(events[0]) == _EVENT_KEYS
        assert events[0]["id"] == own
        assert events[0]["message"] == "mine"

    def test_unread_only_filter(self, inbox) -> None:
        _event(inbox.agent_id, message="read", is_read=True)
        unread = _event(inbox.agent_id, message="unread", is_read=False)
        resp = inbox.client.get("/api/v1/agent/inbox?unread_only=true", headers=_hdr())
        assert resp.status_code == 200
        events = resp.json()["events"]
        assert [e["id"] for e in events] == [unread]
        assert events[0]["message"] == "unread"

    def test_missing_token_401(self, inbox) -> None:
        resp = inbox.client.get("/api/v1/agent/inbox")
        assert resp.status_code == 401
