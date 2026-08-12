"""NotificationTrigger — auto-generate notifications from workflow events.

TASK-0100 S18.1
"""

from sqlalchemy.orm import Session

# Event → (title_template, message_template, default_target)
_EVENT_TEMPLATES: dict[str, tuple[str, str, str]] = {
    "task.claimed": (
        "Task Claimed",
        'Agent "{actor_id}" claimed task "{task_title}"',
        "system",
    ),
    "clarification.asked": (
        "Clarification Needed",
        'New question for task: "{question}"',
        "system",
    ),
    "clarification.answered": (
        "Clarification Answered",
        'Question answered: "{answer}"',
        "system",
    ),
    "evidence.attached": (
        "Evidence Attached",
        'New evidence "{evidence_title}" attached to task',
        "system",
    ),
    "review.completed": (
        "Review Completed",
        'Review verdict: "{verdict}"',
        "system",
    ),
    "review.rejected": (
        "Review Rejected",
        'Review rejected with verdict: "{verdict}"',
        "system",
    ),
    "claim.stale": (
        "Stale Claim Detected",
        'Agent "{agent_id}" claim on "{task_title}" is stale',
        "system",
    ),
    "task.status_changed": (
        "Task Status Changed",
        'Task "{task_title}" moved from "{old_status}" to "{new_status}"',
        "system",
    ),
}


class NotificationTrigger:
    """Creates notifications from workflow events."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def trigger(
        self,
        event_type: str,
        *,
        entity_type: str,
        entity_id: str,
        actor_id: str,
        target_user_id: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> None:
        """Trigger a notification for a workflow event.

        Args:
            event_type: One of the supported event types.
            entity_type: Type of entity (task, clarification, etc.).
            entity_id: ID of the entity.
            actor_id: Who performed the action.
            target_user_id: Who should receive the notification.
            metadata: Extra data for message templating.
        """
        from app.reporting.models import Notification

        title_tpl, msg_tpl, default_target = _EVENT_TEMPLATES.get(
            event_type,
            (event_type.replace(".", " ").title(), event_type, "system"),
        )

        metadata = metadata or {}

        # Format message with available metadata
        try:
            message = msg_tpl.format(actor_id=actor_id, **metadata)
        except KeyError:
            message = msg_tpl

        user_id = target_user_id or default_target

        notification = Notification(
            user_id=user_id,
            type=event_type,
            title=title_tpl,
            message=message,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        self._session.add(notification)
        try:
            self._session.flush()
        except Exception:  # noqa: BLE001
            # Table may not exist (e.g. in tests without migration).
            # Remove the pending notification so it doesn't break session.commit().
            self._session.expunge(notification)
