"""Task lifecycle state machine — TASK-0072."""

VALID_TRANSITIONS: dict[str, set[str]] = {
    "backlog": {"ready", "cancelled"},
    "ready": {"claimed", "backlog", "cancelled"},
    "claimed": {"in_progress", "backlog"},
    "in_progress": {"done", "blocked", "needs_clarification", "ready_for_review"},
    "blocked": {"in_progress"},
    "needs_clarification": {"in_progress"},
    "ready_for_review": {"done", "changes_requested"},
    "changes_requested": {"in_progress"},
    "done": set(),
    "cancelled": set(),
}


class InvalidTransition(Exception):
    """Raised when a task status transition is not allowed."""

    def __init__(self, from_status: str, to_status: str) -> None:
        self.from_status = from_status
        self.to_status = to_status
        super().__init__(f"Cannot transition from '{from_status}' to '{to_status}'")


def validate_transition(from_status: str, to_status: str) -> None:
    """Validate that a status transition is allowed.

    Raises InvalidTransition if the transition is not in VALID_TRANSITIONS.
    """
    allowed = VALID_TRANSITIONS.get(from_status)
    if allowed is None:
        raise InvalidTransition(from_status, to_status)
    if to_status not in allowed:
        raise InvalidTransition(from_status, to_status)
