"""Unit tests for agent inbox events — TASK-0099 B3."""

import pytest
from app.delivery.inbox_events import (
    count_unread,
    create_agent_event,
    get_agent_events,
    mark_all_read,
    mark_event_read,
)
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


class TestCreateAgentEvent:
    def test_create_event(self, _db, session):
        event = create_agent_event(
            session,
            agent_id="agent-001",
            event_type="clarification_request",
            task_id="task-001",
            message="New clarification request",
        )
        assert event.agent_id == "agent-001"
        assert event.event_type == "clarification_request"
        assert event.is_read is False

    def test_create_event_with_metadata(self, _db, session):
        event = create_agent_event(
            session,
            agent_id="agent-001",
            event_type="claim_released",
            task_id="task-001",
            message="Claim released",
            metadata_json='{"reason": "stale"}',
        )
        assert event.metadata_json == '{"reason": "stale"}'

    def test_create_event_no_task(self, _db, session):
        event = create_agent_event(
            session,
            agent_id="agent-001",
            event_type="system",
            message="System message",
        )
        assert event.task_id is None


class TestGetAgentEvents:
    def test_get_events_returns_list(self, _db, session):
        create_agent_event(session, agent_id="a1", event_type="t1", message="m1")
        create_agent_event(session, agent_id="a1", event_type="t2", message="m2")
        create_agent_event(session, agent_id="a2", event_type="t3", message="m3")

        events = get_agent_events(session, "a1")
        assert len(events) == 2

    def test_get_events_unread_only(self, _db, session):
        e1 = create_agent_event(session, agent_id="a1", event_type="t1", message="m1")
        create_agent_event(session, agent_id="a1", event_type="t2", message="m2")
        e1.is_read = True
        session.flush()

        events = get_agent_events(session, "a1", unread_only=True)
        assert len(events) == 1
        assert events[0].event_type == "t2"

    def test_get_events_empty(self, _db, session):
        events = get_agent_events(session, "nonexistent")
        assert events == []


class TestMarkEventRead:
    def test_mark_read(self, _db, session):
        event = create_agent_event(session, agent_id="a1", event_type="t1", message="m1")
        result = mark_event_read(session, event.id)
        assert result is not None
        assert result.is_read is True

    def test_mark_read_nonexistent(self, _db, session):
        result = mark_event_read(session, "nonexistent")
        assert result is None


class TestMarkAllRead:
    def test_mark_all_read(self, _db, session):
        create_agent_event(session, agent_id="a1", event_type="t1", message="m1")
        create_agent_event(session, agent_id="a1", event_type="t2", message="m2")
        count = mark_all_read(session, "a1")
        assert count == 2

        events = get_agent_events(session, "a1", unread_only=True)
        assert len(events) == 0

    def test_mark_all_read_no_events(self, _db, session):
        count = mark_all_read(session, "nonexistent")
        assert count == 0


class TestCountUnread:
    def test_count_unread(self, _db, session):
        create_agent_event(session, agent_id="a1", event_type="t1", message="m1")
        create_agent_event(session, agent_id="a1", event_type="t2", message="m2")
        assert count_unread(session, "a1") == 2

    def test_count_unread_after_read(self, _db, session):
        e1 = create_agent_event(session, agent_id="a1", event_type="t1", message="m1")
        e1.is_read = True
        session.flush()
        assert count_unread(session, "a1") == 0
