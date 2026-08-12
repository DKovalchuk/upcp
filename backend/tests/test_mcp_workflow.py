"""Tests for MCP workflow tools — TASK-0076."""

import json

import pytest
from app.delivery.models import Feature, Task, TaskClaim  # noqa: F401
from app.mcp.tools import call_tool, get_tools
from app.projects.models import Project  # noqa: F401
from app.shared.database import Base

from tests.conftest import _test_engine, _TestSession


@pytest.fixture()
def _db():
    import app.audit.models  # noqa: F401
    import app.auth.models  # noqa: F401
    import app.delivery.models  # noqa: F401
    import app.gitread.models  # noqa: F401
    import app.identity.agents  # noqa: F401
    import app.identity.models  # noqa: F401
    import app.identity.rbac  # noqa: F401
    import app.projects.models  # noqa: F401
    import app.quality.models  # noqa: F401
    import app.reporting.models  # noqa: F401
    import app.structure.models  # noqa: F401

    Base.metadata.drop_all(bind=_test_engine)
    Base.metadata.create_all(bind=_test_engine)
    yield
    Base.metadata.drop_all(bind=_test_engine)


@pytest.fixture()
def session():
    s = _TestSession()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


@pytest.fixture()
def seed(_db, session):
    p = Project(name="Test", slug="test-mcp-wf")
    session.add(p)
    session.flush()
    f = Feature(project_id=p.id, name="F1", slug="f1")
    session.add(f)
    session.flush()
    t = Task(feature_id=f.id, title="T1", status="ready")
    session.add(t)
    session.flush()
    return {"project_id": p.id, "feature_id": f.id, "task_id": t.id}


def _call(name: str, args: dict, session) -> dict:
    """Call MCP tool and return parsed JSON result."""
    import asyncio

    result = asyncio.run(call_tool(name, args, session=session))
    return json.loads(result.content[0]["text"])


class TestToolRegistration:
    def test_workflow_tools_registered(self):
        tools = get_tools()
        names = {t.name for t in tools}
        for tool in [
            "claim_task",
            "release_task",
            "heartbeat_task",
            "request_clarification",
            "answer_clarification",
            "submit_task_for_review",
            "get_agent_inbox",
            "get_agent_playbook",
        ]:
            assert tool in names, f"{tool} not registered"


class TestClaimTool:
    def test_claim_task(self, session, seed):
        data = _call("claim_task", {"task_id": seed["task_id"], "agent_id": "a1"}, session)
        assert data["state"] == "active"
        assert data["agent_id"] == "a1"

    def test_claim_already_claimed(self, session, seed):
        _call("claim_task", {"task_id": seed["task_id"], "agent_id": "a1"}, session)
        import asyncio

        from app.mcp.tools import call_tool as ct

        result = asyncio.run(
            ct("claim_task", {"task_id": seed["task_id"], "agent_id": "a2"}, session=session)
        )
        assert result.is_error is True


class TestReleaseTool:
    def test_release_task(self, session, seed):
        _call("claim_task", {"task_id": seed["task_id"], "agent_id": "a1"}, session)
        data = _call("release_task", {"task_id": seed["task_id"], "agent_id": "a1"}, session)
        assert data["ok"] is True


class TestHeartbeatTool:
    def test_heartbeat(self, session, seed):
        _call("claim_task", {"task_id": seed["task_id"], "agent_id": "a1"}, session)
        data = _call(
            "heartbeat_task",
            {
                "task_id": seed["task_id"],
                "agent_id": "a1",
                "progress_percent": 50,
                "current_step": "coding",
                "next_step": "testing",
            },
            session,
        )
        assert data["ok"] is True


class TestClarificationTool:
    def test_request_clarification(self, session, seed):
        t = session.get(Task, seed["task_id"])
        t.status = "in_progress"
        session.flush()

        data = _call(
            "request_clarification",
            {
                "task_id": seed["task_id"],
                "agent_id": "a1",
                "question": "What format?",
            },
            session,
        )
        assert data["state"] == "open"
        assert data["question"] == "What format?"


class TestSubmitForReview:
    def test_submit_own_task(self, session, seed):
        """Agent can submit their own claimed task for review."""
        _call("claim_task", {"task_id": seed["task_id"], "agent_id": "a1"}, session)
        # Move to in_progress first (in_progress → ready_for_review is valid)
        t = session.get(Task, seed["task_id"])
        t.status = "in_progress"
        session.flush()

        data = _call(
            "submit_task_for_review",
            {
                "task_id": seed["task_id"],
                "agent_id": "a1",
            },
            session,
        )
        assert data["status"] == "ready_for_review"

    def test_submit_other_agents_task_rejected(self, session, seed):
        """Agent cannot submit task claimed by another agent."""
        _call("claim_task", {"task_id": seed["task_id"], "agent_id": "a1"}, session)
        t = session.get(Task, seed["task_id"])
        t.status = "in_progress"
        session.flush()

        import asyncio

        from app.mcp.tools import call_tool as ct

        result = asyncio.run(
            ct(
                "submit_task_for_review",
                {
                    "task_id": seed["task_id"],
                    "agent_id": "a2",
                },
                session=session,
            )
        )
        assert result.is_error is True
        assert "no active claim" in result.content[0]["text"]

    def test_submit_unclaimed_task_rejected(self, session, seed):
        """Cannot submit task with no active claim."""
        t = session.get(Task, seed["task_id"])
        t.status = "in_progress"
        session.flush()

        import asyncio

        from app.mcp.tools import call_tool as ct

        result = asyncio.run(
            ct(
                "submit_task_for_review",
                {
                    "task_id": seed["task_id"],
                    "agent_id": "a1",
                },
                session=session,
            )
        )
        assert result.is_error is True


class TestPlaybookTool:
    def test_get_playbook(self, session):
        data = _call("get_agent_playbook", {}, session)
        assert len(data["content"]) > 0
