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
