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
