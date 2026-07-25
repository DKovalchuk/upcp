from datetime import UTC, datetime

from app.audit.models import AuditEvent
from app.audit.service import AuditService
from app.shared.database import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def _in_memory_db() -> sessionmaker:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def test_audit_event_has_required_columns() -> None:
    cols = {c.name for c in AuditEvent.__table__.columns}
    expected = {
        "id",
        "timestamp",
        "event_type",
        "entity_type",
        "entity_id",
        "actor_type",
        "actor_id",
        "payload",
    }
    assert expected.issubset(cols)


def test_log_event_inserts_row() -> None:
    SessionLocal = _in_memory_db()
    session = SessionLocal()
    service = AuditService(session)

    event = service.log_event(
        event_type="project.created",
        entity_type="project",
        entity_id="proj-1",
        actor_type="user",
        actor_id="user-1",
    )

    assert event.id is not None
    assert event.event_type == "project.created"
    assert event.timestamp <= datetime.now(UTC)
    session.close()


def test_log_event_stores_payload() -> None:
    SessionLocal = _in_memory_db()
    session = SessionLocal()
    service = AuditService(session)

    event = service.log_event(
        event_type="task.done",
        entity_type="task",
        entity_id="task-1",
        actor_type="agent",
        actor_id="agent-1",
        payload={"status": "done"},
    )

    assert event.payload == {"status": "done"}
    session.close()


def test_audit_service_has_no_update_or_delete() -> None:
    service = AuditService.__new__(AuditService)
    assert not hasattr(service, "update_event")
    assert not hasattr(service, "delete_event")


def test_list_events_empty() -> None:
    SessionLocal = _in_memory_db()
    session = SessionLocal()
    service = AuditService(session)
    events, total = service.list_events("nonexistent-project")
    assert events == []
    assert total == 0
    session.close()


def test_list_events_returns_all_for_project() -> None:
    SessionLocal = _in_memory_db()
    session = SessionLocal()
    service = AuditService(session)
    service.log_event(
        event_type="project.created",
        entity_type="project",
        entity_id="proj-1",
        actor_type="user",
        actor_id="user-1",
    )
    service.log_event(
        event_type="task.done",
        entity_type="task",
        entity_id="proj-1",
        actor_type="agent",
        actor_id="agent-1",
    )
    events, total = service.list_events("proj-1")
    assert total == 2
    assert len(events) == 2
    assert events[0].timestamp >= events[1].timestamp
    session.close()


def test_list_events_filter_by_event_type() -> None:
    SessionLocal = _in_memory_db()
    session = SessionLocal()
    service = AuditService(session)
    service.log_event(
        event_type="project.created",
        entity_type="project",
        entity_id="proj-1",
        actor_type="user",
        actor_id="user-1",
    )
    service.log_event(
        event_type="task.done",
        entity_type="task",
        entity_id="proj-1",
        actor_type="agent",
        actor_id="agent-1",
    )
    events, total = service.list_events("proj-1", event_type="project.created")
    assert total == 1
    assert events[0].event_type == "project.created"
    session.close()


def test_list_events_filter_by_entity_type() -> None:
    SessionLocal = _in_memory_db()
    session = SessionLocal()
    service = AuditService(session)
    service.log_event(
        event_type="project.created",
        entity_type="project",
        entity_id="proj-1",
        actor_type="user",
        actor_id="user-1",
    )
    service.log_event(
        event_type="task.done",
        entity_type="task",
        entity_id="proj-1",
        actor_type="agent",
        actor_id="agent-1",
    )
    events, total = service.list_events("proj-1", entity_type="task")
    assert total == 1
    assert events[0].entity_type == "task"
    session.close()


def test_list_events_filter_by_date_range() -> None:
    SessionLocal = _in_memory_db()
    session = SessionLocal()
    service = AuditService(session)
    service.log_event(
        event_type="project.created",
        entity_type="project",
        entity_id="proj-1",
        actor_type="user",
        actor_id="user-1",
    )
    from datetime import datetime, timedelta

    future = datetime.now(UTC) + timedelta(days=1)
    events, total = service.list_events("proj-1", date_from=future)
    assert total == 0
    session.close()


def test_list_events_pagination() -> None:
    SessionLocal = _in_memory_db()
    session = SessionLocal()
    service = AuditService(session)
    for i in range(5):
        service.log_event(
            event_type=f"event{i}",
            entity_type="entity",
            entity_id="proj-1",
            actor_type="user",
            actor_id="user-1",
        )
    events1, total1 = service.list_events("proj-1", offset=0, limit=2)
    assert total1 == 5
    assert len(events1) == 2
    events2, total2 = service.list_events("proj-1", offset=2, limit=2)
    assert total2 == 5
    assert len(events2) == 2
    ids1 = {e.id for e in events1}
    ids2 = {e.id for e in events2}
    assert ids1.isdisjoint(ids2)
    session.close()
