from datetime import datetime

from sqlalchemy.orm import Session

from app.audit.models import AuditEvent


class AuditService:
    """Append-only audit event logger."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def log_event(
        self,
        *,
        event_type: str,
        entity_type: str,
        entity_id: str,
        actor_type: str,
        actor_id: str,
        payload: dict[str, object] | None = None,
        note: str | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_type=actor_type,
            actor_id=actor_id,
            payload=payload,
            note=note,
        )
        self._session.add(event)
        self._session.flush()
        return event

    def list_events(
        self,
        project_id: str,
        *,
        event_type: str | None = None,
        entity_type: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[AuditEvent], int]:
        """List audit events for a project with optional filters and pagination."""
        q = self._session.query(AuditEvent).filter_by(entity_id=project_id)
        if event_type:
            q = q.filter(AuditEvent.event_type == event_type)
        if entity_type:
            q = q.filter(AuditEvent.entity_type == entity_type)
        if date_from:
            q = q.filter(AuditEvent.timestamp >= date_from)
        if date_to:
            q = q.filter(AuditEvent.timestamp <= date_to)
        total = q.count()
        events = q.order_by(AuditEvent.timestamp.desc()).offset(offset).limit(limit).all()
        return events, total