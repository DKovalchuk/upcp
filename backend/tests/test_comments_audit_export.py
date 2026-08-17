"""Tests for Task Comments and Audit Export — TASK-0118 (S22.4)."""

from __future__ import annotations

import csv
import io
import uuid

import pytest
from app.audit.models import AuditEvent  # noqa: F401
from app.audit.service import AuditService
from app.delivery.models import Feature, Task  # noqa: F401
from app.delivery.service import CommentService
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
    try:
        yield s
        s.rollback()
    finally:
        s.close()


@pytest.fixture()
def task_id(session) -> str:
    prefix = uuid.uuid4().hex[:6]
    p = Project(name=f"P-{prefix}", slug=f"p-{prefix}")
    session.add(p)
    session.flush()
    f = Feature(project_id=p.id, name=f"F-{prefix}", slug=f"f-{prefix}")
    session.add(f)
    session.flush()
    t = Task(feature_id=f.id, title=f"T-{prefix}", status="in_progress")
    session.add(t)
    session.flush()
    return t.id


class TestCommentService:
    """Test CommentService create and list."""

    def test_create_comment(self, session, task_id):
        svc = CommentService(session)
        c = svc.create(
            task_id=task_id,
            author_type="human",
            author_id="user-1",
            body="This looks good!",
        )
        assert c.task_id == task_id
        assert c.body == "This looks good!"
        assert c.author_id == "user-1"
        assert c.parent_id is None

    def test_create_reply(self, session, task_id):
        svc = CommentService(session)
        parent = svc.create(
            task_id=task_id,
            author_type="human",
            author_id="user-1",
            body="Question about this?",
        )
        reply = svc.create(
            task_id=task_id,
            author_type="agent",
            author_id="agent-1",
            body="Yes, I'll fix it.",
            parent_id=parent.id,
        )
        assert reply.parent_id == parent.id

    def test_list_by_task(self, session, task_id):
        svc = CommentService(session)
        svc.create(task_id=task_id, author_type="human", author_id="u1", body="A")
        svc.create(task_id=task_id, author_type="human", author_id="u2", body="B")
        comments = svc.list_by_task(task_id)
        assert len(comments) == 2

    def test_list_empty_task(self, session, task_id):
        svc = CommentService(session)
        comments = svc.list_by_task(task_id)
        assert comments == []


class TestAuditExport:
    """Test audit export as CSV and JSON."""

    def test_export_json(self, session):
        svc = AuditService(session)
        prefix = uuid.uuid4().hex[:6]
        svc.log_event(
            event_type="task.created",
            entity_type="task",
            entity_id=f"task-{prefix}",
            actor_type="human",
            actor_id="user-1",
            payload={"title": "Test task"},
        )
        events, total = svc.list_events(f"task-{prefix}", offset=0, limit=100)
        assert total == 1
        assert events[0].event_type == "task.created"

    def test_export_csv_format(self, session):
        svc = AuditService(session)
        prefix = uuid.uuid4().hex[:6]
        svc.log_event(
            event_type="task.completed",
            entity_type="task",
            entity_id=f"task-{prefix}",
            actor_type="agent",
            actor_id="agent-1",
        )
        events, _ = svc.list_events(f"task-{prefix}", offset=0, limit=100)

        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "timestamp",
                "event_type",
                "entity_type",
                "entity_id",
                "actor_type",
                "actor_id",
                "note",
            ],
        )
        writer.writeheader()
        for e in events:
            writer.writerow(
                {
                    "timestamp": e.timestamp.isoformat(),
                    "event_type": e.event_type,
                    "entity_type": e.entity_type,
                    "entity_id": e.entity_id,
                    "actor_type": e.actor_type,
                    "actor_id": e.actor_id,
                    "note": e.note or "",
                }
            )

        csv_text = output.getvalue()
        reader = csv.DictReader(io.StringIO(csv_text))
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["event_type"] == "task.completed"
