"""Agent inbox events — create, read, mark_read.

TASK-0099 (B3)
"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.delivery.models import AgentInboxEvent
from app.shared.text import new_id


def create_agent_event(
    session: Session,
    *,
    agent_id: str,
    event_type: str,
    task_id: str | None = None,
    message: str,
    metadata_json: str | None = None,
) -> AgentInboxEvent:
    """Create an inbox event for an agent."""
    event = AgentInboxEvent(
        id=new_id(),
        agent_id=agent_id,
        event_type=event_type,
        task_id=task_id,
        message=message,
        metadata_json=metadata_json,
    )
    session.add(event)
    session.flush()
    return event


def get_agent_events(
    session: Session,
    agent_id: str,
    *,
    since: datetime | None = None,
    unread_only: bool = False,
    limit: int = 50,
) -> list[AgentInboxEvent]:
    """Get inbox events for an agent, ordered by created_at desc."""
    stmt = select(AgentInboxEvent).where(AgentInboxEvent.agent_id == agent_id)
    if since is not None:
        stmt = stmt.where(AgentInboxEvent.created_at >= since)
    if unread_only:
        stmt = stmt.where(AgentInboxEvent.is_read == False)  # noqa: E712
    stmt = stmt.order_by(AgentInboxEvent.created_at.desc()).limit(limit)
    return list(session.execute(stmt).scalars().all())


def mark_event_read(session: Session, event_id: str) -> AgentInboxEvent | None:
    """Mark a single event as read. Returns None if not found."""
    event = session.get(AgentInboxEvent, event_id)
    if event is None:
        return None
    event.is_read = True
    session.flush()
    return event


def mark_all_read(session: Session, agent_id: str) -> int:
    """Mark all events for an agent as read. Returns count marked."""
    events = (
        session.query(AgentInboxEvent)
        .filter(AgentInboxEvent.agent_id == agent_id, AgentInboxEvent.is_read == False)  # noqa: E712
        .all()
    )
    count = len(events)
    for e in events:
        e.is_read = True
    if count:
        session.flush()
    return count


def count_unread(session: Session, agent_id: str) -> int:
    """Count unread events for an agent."""
    return (
        session.query(AgentInboxEvent)
        .filter(AgentInboxEvent.agent_id == agent_id, AgentInboxEvent.is_read == False)  # noqa: E712
        .count()
    )
