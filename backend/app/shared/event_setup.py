"""Wire event bus to NotificationTrigger and SSE broadcast.

Call `setup_event_handlers()` once at app startup.
"""

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.shared.events import event_bus

logger = logging.getLogger(__name__)

# All event types that trigger notifications
_SUBSCRIBED_EVENTS = [
    "task.claimed",
    "task.status_changed",
    "task.completed",
    "clarification.asked",
    "clarification.answered",
    "claim.expired",
    "claim.stale",
    "evidence.attached",
    "review.completed",
    "review.rejected",
]

# Critical events that should trigger toasts on the frontend
_CRITICAL_EVENTS = frozenset(
    {
        "clarification.asked",
        "review.completed",
        "review.rejected",
    }
)


def _handle_notification(event_type: str, session: Session, **kwargs: Any) -> None:
    """Forward event to NotificationTrigger and broadcast via SSE."""
    from app.reporting.sse import sse_manager
    from app.reporting.trigger import NotificationTrigger

    NotificationTrigger(session).trigger(event_type, **kwargs)

    # Broadcast to SSE clients
    sse_manager.broadcast(
        "notification",
        {
            "event_type": event_type,
            "critical": event_type in _CRITICAL_EVENTS,
            **{k: str(v) for k, v in kwargs.items() if k != "session"},
        },
    )


def setup_event_handlers() -> None:
    """Subscribe the notification handler to all workflow events."""
    for evt in _SUBSCRIBED_EVENTS:
        event_bus.subscribe(evt, _handle_notification)


def teardown_event_handlers() -> None:
    """Unsubscribe all handlers. Useful for testing."""
    event_bus.clear()
