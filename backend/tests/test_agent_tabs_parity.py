"""Characterization parity for agent detail tabs + agent-self inbox — TASK-0176.

Written BEFORE the cross-context refactor: every test here pins the exact
response shape/status of endpoints whose data access moves behind the
owner-context services, and must stay green UNMODIFIED across it
(SPEC-0029 AC8). Also pins the read-ownership boundary: GET tabs are open
to any authenticated user (no owner check), agent-self reads only its own
agent's rows. Agent-self inbox parity lives in ``test_agent_self_inbox_parity.py``.
"""

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
from app.delivery.models import (
    AgentInboxEvent,
    ClarificationRequest,
    Feature,
    Task,
)
from app.identity.agent_endpoints import router as agents_router
from app.identity.agents import Agent
from app.identity.auth import get_current_user
from app.identity.dependencies import CurrentUser
from app.identity.models import User
from app.projects.models import Project
from app.quality.models import Evidence, ReviewRound
from app.shared.database import Base, get_session
from app.shared.errors import register_error_handlers
from app.shared.text import new_id
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tests.conftest import _override_session, _test_engine, _TestSession

_OTHER_AGENT = "foreign-agent"

_EVENT_KEYS = {"id", "event_type", "task_id", "message", "is_read", "created_at"}
_EVIDENCE_KEYS = {"id", "task_id", "type", "title", "verification_state", "created_at"}
_REVIEW_KEYS = {"id", "task_id", "state", "verdict", "confidence", "created_at"}
_CLARIFICATION_KEYS = {"id", "task_id", "question", "state", "blocking", "created_at"}


@pytest.fixture()
def tabs():
    """Web-surface app for the detail tabs; superuser override for reads."""
    Base.metadata.drop_all(bind=_test_engine)
    Base.metadata.create_all(bind=_test_engine)
    app = FastAPI()
    register_error_handlers(app)
    app.include_router(agents_router, prefix="/api/v1")
    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        user_id="parity-user", email="parity@x.com", is_superuser=True
    )

    uid = uuid.uuid4().hex[:8]
    session = _TestSession()
    try:
        session.add(
            User(
                id="parity-user",
                email=f"p-{uid}@x.com",
                password_hash="x",
                display_name="Parity",
                is_superuser=True,
            )
        )
        session.flush()
        project = Project(name=f"Parity-{uid}", slug=f"parity-{uid}")
        session.add(project)
        session.flush()
        feature = Feature(project_id=project.id, name="PF", slug=f"pf-{uid}")
        session.add(feature)
        session.flush()
        task = Task(feature_id=feature.id, title="PT", status="ready")
        session.add(task)
        session.flush()
        agent = Agent(name=f"ParityAgent-{uid}", description="d", created_by="parity-user")
        session.add(agent)
        session.commit()
        data = {"agent_id": agent.id, "task_id": task.id}
    finally:
        session.close()

    yield SimpleNamespace(client=TestClient(app), app=app, data=data)
    Base.metadata.drop_all(bind=_test_engine)
    Base.metadata.create_all(bind=_test_engine)


def _insert(factory) -> str:
    """Insert one seeded row and return its id."""
    session = _TestSession()
    try:
        row = factory()
        session.add(row)
        session.commit()
        return row.id
    finally:
        session.close()


# ── identity: detail tabs (parity) ───────────────────────────────────────────


class TestEvidenceTab:
    def test_empty(self, tabs) -> None:
        resp = tabs.client.get(f"/api/v1/agents/{tabs.data['agent_id']}/evidence")
        assert resp.status_code == 200
        assert resp.json() == {"items": []}

    def test_positive_shape_and_creator_filter(self, tabs) -> None:
        agent_id = tabs.data["agent_id"]
        task_id = tabs.data["task_id"]
        own = _insert(
            lambda: Evidence(
                id=new_id(),
                task_id=task_id,
                type="file",
                title="mine",
                created_by_type="agent",
                created_by_id=agent_id,
            )
        )
        _insert(
            lambda: Evidence(
                id=new_id(),
                task_id=task_id,
                type="file",
                title="others",
                created_by_type="agent",
                created_by_id=_OTHER_AGENT,
            )
        )
        resp = tabs.client.get(f"/api/v1/agents/{agent_id}/evidence")
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 1
        assert set(items[0]) == _EVIDENCE_KEYS
        assert items[0]["id"] == own
        assert items[0]["task_id"] == task_id
        assert items[0]["title"] == "mine"
        assert items[0]["verification_state"] == "unverified"

    def test_unknown_agent_404(self, tabs) -> None:
        resp = tabs.client.get("/api/v1/agents/nonexistent/evidence")
        assert resp.status_code == 404


class TestReviewsTab:
    def test_empty(self, tabs) -> None:
        resp = tabs.client.get(f"/api/v1/agents/{tabs.data['agent_id']}/reviews")
        assert resp.status_code == 200
        assert resp.json() == {"items": []}

    def test_positive_shape_and_reviewer_filter(self, tabs) -> None:
        agent_id = tabs.data["agent_id"]
        task_id = tabs.data["task_id"]
        own = _insert(
            lambda: ReviewRound(
                id=new_id(),
                task_id=task_id,
                requested_by_type="agent",
                requested_by_id="someone",
                reviewer_id=agent_id,
            )
        )
        _insert(
            lambda: ReviewRound(
                id=new_id(),
                task_id=task_id,
                requested_by_type="agent",
                requested_by_id="someone",
                reviewer_id=_OTHER_AGENT,
            )
        )
        resp = tabs.client.get(f"/api/v1/agents/{agent_id}/reviews")
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 1
        assert set(items[0]) == _REVIEW_KEYS
        assert items[0]["id"] == own
        assert items[0]["state"] == "pending"
        assert items[0]["verdict"] is None
        assert items[0]["confidence"] is None

    def test_unknown_agent_404(self, tabs) -> None:
        resp = tabs.client.get("/api/v1/agents/nonexistent/reviews")
        assert resp.status_code == 404


class TestActivityTab:
    def test_positive_shape_order_and_agent_filter(self, tabs) -> None:
        agent_id = tabs.data["agent_id"]
        from datetime import UTC, datetime

        first = _insert(
            lambda: AgentInboxEvent(
                id=new_id(),
                agent_id=agent_id,
                event_type="task.assigned",
                task_id=tabs.data["task_id"],
                message="first",
                created_at=datetime(2026, 1, 1, tzinfo=UTC),
            )
        )
        second = _insert(
            lambda: AgentInboxEvent(
                id=new_id(),
                agent_id=agent_id,
                event_type="task.completed",
                message="second",
                created_at=datetime(2026, 1, 2, tzinfo=UTC),
            )
        )
        _insert(
            lambda: AgentInboxEvent(
                id=new_id(),
                agent_id=_OTHER_AGENT,
                event_type="task.assigned",
                message="foreign",
            )
        )
        resp = tabs.client.get(f"/api/v1/agents/{agent_id}/activity")
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert [i["id"] for i in items] == [second, first]  # created_at desc
        assert set(items[0]) == _EVENT_KEYS
        assert items[0]["message"] == "second"
        assert items[0]["is_read"] is False


class TestClarificationsTab:
    def test_positive_shape_and_author_filter(self, tabs) -> None:
        agent_id = tabs.data["agent_id"]
        task_id = tabs.data["task_id"]
        own = _insert(
            lambda: ClarificationRequest(
                id=new_id(),
                task_id=task_id,
                author_type="agent",
                author_id=agent_id,
                question="mine?",
                blocking=True,
            )
        )
        _insert(
            lambda: ClarificationRequest(
                id=new_id(),
                task_id=task_id,
                author_type="agent",
                author_id=_OTHER_AGENT,
                question="foreign?",
            )
        )
        resp = tabs.client.get(f"/api/v1/agents/{agent_id}/clarifications")
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) == 1
        assert set(items[0]) == _CLARIFICATION_KEYS
        assert items[0]["id"] == own
        assert items[0]["question"] == "mine?"
        assert items[0]["state"] == "open"
        assert items[0]["blocking"] is True


class TestReadOwnershipBoundary:
    """Characterization: GET tabs have NO owner check — any authenticated user
    (even a non-superuser stranger) may read any agent's data (TASK-0176
    Test design «чужой agent_id»). Write ops keep their 403 owner gate."""

    def test_non_owner_user_reads_foreign_agent_tabs(self, tabs) -> None:
        tabs.app.dependency_overrides[get_current_user] = lambda: CurrentUser(
            user_id="stranger", email="s@x.com", is_superuser=False
        )
        try:
            agent_id = tabs.data["agent_id"]
            for path in ("claims", "evidence", "reviews", "activity", "clarifications"):
                resp = tabs.client.get(f"/api/v1/agents/{agent_id}/{path}")
                assert resp.status_code == 200, path
        finally:
            tabs.app.dependency_overrides[get_current_user] = lambda: CurrentUser(
                user_id="parity-user", email="parity@x.com", is_superuser=True
            )
