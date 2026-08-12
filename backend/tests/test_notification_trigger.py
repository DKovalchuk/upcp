"""Tests for NotificationTrigger — TASK-0100 S18.1."""

import pytest
from app.delivery.models import Feature, Task  # noqa: F401
from app.projects.models import Project  # noqa: F401
from app.reporting.models import Notification
from app.reporting.trigger import NotificationTrigger
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
def session(_db):
    s = _TestSession()
    yield s
    s.close()


@pytest.fixture()
def trigger(session):
    return NotificationTrigger(session)


class TestNotificationTrigger:
    def test_task_claimed(self, trigger, session):
        trigger.trigger(
            "task.claimed",
            entity_type="task",
            entity_id="t1",
            actor_id="agent-1",
            metadata={"task_title": "Build API"},
        )
        session.flush()
        notifs = session.query(Notification).all()
        assert len(notifs) == 1
        assert notifs[0].type == "task.claimed"
        assert notifs[0].entity_type == "task"
        assert notifs[0].entity_id == "t1"
        assert "Build API" in notifs[0].message

    def test_clarification_asked(self, trigger, session):
        trigger.trigger(
            "clarification.asked",
            entity_type="task",
            entity_id="t1",
            actor_id="reviewer-1",
            target_user_id="agent-1",
            metadata={"question": "What framework?"},
        )
        session.flush()
        notifs = session.query(Notification).all()
        assert len(notifs) == 1
        assert notifs[0].type == "clarification.asked"
        assert notifs[0].user_id == "agent-1"
        assert "What framework?" in notifs[0].message

    def test_clarification_answered(self, trigger, session):
        trigger.trigger(
            "clarification.answered",
            entity_type="task",
            entity_id="t1",
            actor_id="agent-1",
            target_user_id="reviewer-1",
            metadata={"answer": "React"},
        )
        session.flush()
        notifs = session.query(Notification).all()
        assert len(notifs) == 1
        assert notifs[0].type == "clarification.answered"
        assert notifs[0].user_id == "reviewer-1"

    def test_evidence_attached(self, trigger, session):
        trigger.trigger(
            "evidence.attached",
            entity_type="task",
            entity_id="t1",
            actor_id="agent-1",
            metadata={"evidence_title": "Test Results"},
        )
        session.flush()
        notifs = session.query(Notification).all()
        assert len(notifs) == 1
        assert notifs[0].type == "evidence.attached"
        assert "Test Results" in notifs[0].message

    def test_review_completed(self, trigger, session):
        trigger.trigger(
            "review.completed",
            entity_type="task",
            entity_id="t1",
            actor_id="reviewer-1",
            target_user_id="agent-1",
            metadata={"verdict": "approve"},
        )
        session.flush()
        notifs = session.query(Notification).all()
        assert len(notifs) == 1
        assert notifs[0].type == "review.completed"
        assert notifs[0].user_id == "agent-1"

    def test_review_rejected(self, trigger, session):
        trigger.trigger(
            "review.rejected",
            entity_type="task",
            entity_id="t1",
            actor_id="reviewer-1",
            target_user_id="agent-1",
            metadata={"verdict": "reject"},
        )
        session.flush()
        notifs = session.query(Notification).all()
        assert len(notifs) == 1
        assert notifs[0].type == "review.rejected"
        assert notifs[0].user_id == "agent-1"

    def test_claim_stale(self, trigger, session):
        trigger.trigger(
            "claim.stale",
            entity_type="task",
            entity_id="t1",
            actor_id="system",
            metadata={"agent_id": "agent-1", "task_title": "Build API"},
        )
        session.flush()
        notifs = session.query(Notification).all()
        assert len(notifs) == 1
        assert notifs[0].type == "claim.stale"
        assert "agent-1" in notifs[0].message

    def test_task_status_changed(self, trigger, session):
        trigger.trigger(
            "task.status_changed",
            entity_type="task",
            entity_id="t1",
            actor_id="agent-1",
            metadata={
                "old_status": "backlog",
                "new_status": "in_progress",
                "task_title": "Build API",
            },
        )
        session.flush()
        notifs = session.query(Notification).all()
        assert len(notifs) == 1
        assert notifs[0].type == "task.status_changed"
        assert "in_progress" in notifs[0].message

    def test_trigger_no_target_uses_system_user(self, trigger, session):
        trigger.trigger(
            "task.claimed",
            entity_type="task",
            entity_id="t1",
            actor_id="agent-1",
        )
        session.flush()
        notifs = session.query(Notification).all()
        assert len(notifs) == 1
        assert notifs[0].user_id == "system"

    def test_trigger_with_target_user(self, trigger, session):
        trigger.trigger(
            "clarification.asked",
            entity_type="task",
            entity_id="t1",
            actor_id="reviewer-1",
            target_user_id="agent-1",
        )
        session.flush()
        notifs = session.query(Notification).all()
        assert len(notifs) == 1
        assert notifs[0].user_id == "agent-1"
