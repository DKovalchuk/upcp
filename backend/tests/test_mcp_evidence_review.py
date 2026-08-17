"""Tests for MCP evidence & review tools — TASK-0081."""

import asyncio
import json

import pytest
from app.delivery.models import Feature, Task  # noqa: F401
from app.mcp.tools import call_tool
from app.projects.models import Project  # noqa: F401
from app.shared.database import Base

from tests.conftest import _test_engine, _TestSession


@pytest.fixture()
def _db():
    import app.audit.models  # noqa: F401
    import app.delivery.models  # noqa: F401
    import app.gitread.models  # noqa: F401
    import app.identity.agents  # noqa: F401
    import app.identity.models  # noqa: F401
    import app.identity.rbac  # noqa: F401
    import app.projects.models  # noqa: F401
    import app.quality.models  # noqa: F401
    import app.reporting.models  # noqa: F401
    import app.structure.models  # noqa: F401

    Base.metadata.create_all(bind=_test_engine)
    yield
    Base.metadata.drop_all(bind=_test_engine)


@pytest.fixture()
def session(_db):
    s = _TestSession()
    yield s
    s.close()


@pytest.fixture()
def project(session):
    p = Project(name="Test", slug="test")
    session.add(p)
    session.flush()
    return p


@pytest.fixture()
def feature(session, project):
    f = Feature(project_id=project.id, name="F1", slug="f1")
    session.add(f)
    session.flush()
    return f


@pytest.fixture()
def task(session, feature):
    t = Task(feature_id=feature.id, title="T1", status="in_progress")
    session.add(t)
    session.flush()
    return t


def _parse(result):
    return json.loads(result.content[0]["text"])


class TestMCPEvidenceTools:
    def test_list_evidence_empty(self, session, task):
        r = asyncio.run(call_tool("list_evidence", {"task_id": task.id}, session))
        data = _parse(r)
        assert data["items"] == []

    def test_attach_and_list_evidence(self, session, task):
        async def _run():
            await call_tool(
                "attach_evidence",
                {
                    "task_id": task.id,
                    "type": "commit",
                    "title": "Initial commit",
                    "created_by_type": "agent",
                    "created_by_id": "a1",
                },
                session,
            )
            return await call_tool("list_evidence", {"task_id": task.id}, session)

        r = asyncio.run(_run())
        data = _parse(r)
        assert len(data["items"]) == 1
        assert data["items"][0]["type"] == "commit"
        assert data["items"][0]["verification_state"] == "unverified"

    def test_attach_evidence_with_all_fields(self, session, task):
        async def _run():
            return await call_tool(
                "attach_evidence",
                {
                    "task_id": task.id,
                    "type": "test_output",
                    "title": "pytest output",
                    "description": "12 passed",
                    "url": "https://ci.example.com/123",
                    "content_snippet": "12 passed in 0.5s",
                    "created_by_type": "agent",
                    "created_by_id": "a1",
                },
                session,
            )

        r = asyncio.run(_run())
        data = _parse(r)
        assert data["type"] == "test_output"
        assert data["id"] is not None


class TestMCPReviewTools:
    def test_list_review_rounds_empty(self, session, task):
        r = asyncio.run(call_tool("list_review_rounds", {"task_id": task.id}, session))
        data = _parse(r)
        assert data["items"] == []

    def test_submit_review_verdict(self, session, task):
        async def _run():
            from app.quality.service import ReviewRoundService

            svc = ReviewRoundService(session)
            rr = svc.create(task_id=task.id, requested_by_type="agent", requested_by_id="a1")
            svc.start(rr.id)

            return await call_tool(
                "submit_review_verdict",
                {
                    "round_id": rr.id,
                    "verdict": "approve",
                    "confidence": 95,
                    "summary": "All good",
                },
                session,
            )

        r = asyncio.run(_run())
        data = _parse(r)
        assert data["state"] == "completed"
        assert data["verdict"] == "approve"
