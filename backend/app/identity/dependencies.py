"""Auth dependency dataclasses + public dependency accessors — CurrentUser, CurrentAgent, get_web_auth."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


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


def get_web_auth() -> Callable[..., Any]:
    """The web-surface auth dependency (SPEC-0028 D2, TASK-0169).

    The function lives in ``app.identity.web_auth`` (it must bind
    ``auth._get_token_service`` at module level for the test override
    seam), but the composition root ``app.api.registry`` consumes it only
    through this public-surface module: reaching into ``identity.web_auth``
    from another context would be a boundary violation, and a module-level
    import here would create the ``auth → dependencies → web_auth → auth``
    cycle — hence the lazy import inside the accessor.
    """
    from app.identity.web_auth import web_auth  # lazy — acyclic by construction

    return web_auth
