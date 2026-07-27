"""Auth dependency dataclasses — CurrentUser, CurrentAgent."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CurrentUser:
    user_id: str
    email: str
    is_superuser: bool
    org_id: str | None = None


@dataclass(frozen=True, slots=True)
class CurrentAgent:
    agent_id: str
    name: str
    scopes: dict[str, object] | None = None
