"""Tests for bulk task operations — TASK-0117 (S22.3)."""

from __future__ import annotations

import uuid

import pytest
from app.delivery.models import Feature, Task  # noqa: F401
from app.delivery.service import TaskService
from app.projects.models import Project  # noqa: F401
from app.shared.database import Base
from app.shared.errors import ValidationError

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

    Base.metadata.drop_all(bind=_test_engine)
    Base.metadata.create_all(bind=_test_engine)
    yield
    Base.metadata.drop_all(bind=_test_engine)


@pytest.fixture()
def session(_db):
    s = _TestSession()
    try:
        yield s
        s.rollback()
    finally:
        s.close()


@pytest.fixture()
def task_ids(session) -> list[str]:
    """Create 5 tasks and return their IDs."""
    prefix = uuid.uuid4().hex[:6]
    p = Project(name=f"P-{prefix}", slug=f"p-{prefix}")
    session.add(p)
    session.flush()
    f = Feature(project_id=p.id, name=f"F-{prefix}", slug=f"f-{prefix}")
    session.add(f)
    session.flush()

    ids = []
    for i in range(5):
        t = Task(feature_id=f.id, title=f"T-{prefix}-{i}", status="backlog", priority=i)
        session.add(t)
        session.flush()
        ids.append(t.id)
    return ids


class TestBulkUpdate:
    """Test TaskService.bulk_update method."""

    def test_bulk_status_change(self, session, task_ids):
        svc = TaskService(session)
        count = svc.bulk_update(task_ids, status="ready")
        assert count == 5

        for tid in task_ids:
            t = svc.get(tid)
            assert t.status == "ready"

    def test_bulk_priority_change(self, session, task_ids):
        svc = TaskService(session)
        count = svc.bulk_update(task_ids, priority=99)
        assert count == 5

        for tid in task_ids:
            t = svc.get(tid)
            assert t.priority == 99

    def test_bulk_assign(self, session, task_ids):
        svc = TaskService(session)
        count = svc.bulk_update(task_ids, assignee_type="agent", assignee_id="agent-1")
        assert count == 5

        for tid in task_ids:
            t = svc.get(tid)
            assert t.assignee_type == "agent"
            assert t.assignee_id == "agent-1"

    def test_bulk_empty_list_returns_zero(self, session):
        svc = TaskService(session)
        count = svc.bulk_update([], status="done")
        assert count == 0

    def test_bulk_partial_failure_logs_and_continues(self, session, task_ids):
        svc = TaskService(session)
        ids_with_bad = task_ids + ["nonexistent-id"]
        count = svc.bulk_update(ids_with_bad, priority=5)
        assert count == 5  # only valid tasks updated

    def test_bulk_invalid_status_transition(self, session, task_ids):
        svc = TaskService(session)
        # backlog → ready is valid, but backlog → in_progress is not
        with pytest.raises(ValidationError, match="transition"):
            svc.bulk_update(task_ids, status="in_progress")

    def test_bulk_multiple_fields(self, session, task_ids):
        svc = TaskService(session)
        count = svc.bulk_update(
            task_ids,
            status="ready",
            priority=10,
            assignee_type="agent",
            assignee_id="agent-2",
        )
        assert count == 5

        for tid in task_ids:
            t = svc.get(tid)
            assert t.status == "ready"
            assert t.priority == 10
            assert t.assignee_id == "agent-2"


class TestBulkUpdateAPI:
    """Test PATCH /api/v1/tasks/bulk endpoint."""

    def _app(self):
        from app.api.v1.delivery import router
        from app.shared.database import get_session
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router, prefix="/api/v1")

        def _override():
            s = _TestSession()
            try:
                yield s
                s.rollback()
            finally:
                s.close()

        app.dependency_overrides[get_session] = _override
        return app

    def test_bulk_update_endpoint(self, task_ids):
        from fastapi.testclient import TestClient

        client = TestClient(self._app())
        resp = client.patch(
            "/api/v1/tasks/bulk",
            json={"task_ids": task_ids, "updates": {"status": "ready"}},
        )
        assert resp.status_code == 200
        assert resp.json()["updated"] == 5

    def test_bulk_update_empty_list(self):
        from fastapi.testclient import TestClient

        client = TestClient(self._app())
        resp = client.patch(
            "/api/v1/tasks/bulk",
            json={"task_ids": [], "updates": {"priority": 1}},
        )
        assert resp.status_code == 200
        assert resp.json()["updated"] == 0
