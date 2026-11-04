"""Request ID correlation middleware — adds request_id to all logs.

TASK-0173 (SPEC-0028 §3.6 / AC9): the response header carries the API
surface prefix — ``web:<id>`` / ``agent:<id>`` (set by the auth blankets
on ``request.state.api_surface``), ``public:<id>`` for a request that
reached a declared route without surface attribution (health/docs/metrics/
auth-public), ``none:<id>`` only when the request resolved to no route at
all (404 — nothing to attribute it to). The rule reads the ASGI scope only:
no registry import (shared → api would be a context-boundary violation).

Incoming client ``X-Request-ID`` values are preserved but SANITIZED
(log-injection hardening): ``[A-Za-z0-9._-]{1,64}`` or a fresh uuid4 —
newline/ANSI/overlong payloads never round-trip.
"""

import re
import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from app.shared.logging import agent_id_var, request_id_var, surface_var, user_id_var

_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
_SURFACE_VALUES = frozenset({"web", "agent", "public", "none"})


def sanitize_request_id(raw: str | None) -> str:
    """Accept the client's ``X-Request-ID`` only if it is safe, else mint one."""
    if raw is not None and _REQUEST_ID_RE.match(raw):
        return raw
    return str(uuid.uuid4())


def resolve_surface(request: Request) -> str:
    """Surface of an already-dispatched request: ``web|agent|public|none``.

    ``request.state.api_surface`` (auth blankets) wins; otherwise a request
    that reached a declared route is ``public`` (the PUBLIC group and the
    app-level health/docs/metrics routes carry no auth dependency), and only
    an unresolved request (no ``scope["route"]`` — e.g. 404) is ``none``.
    """
    state = getattr(request.state, "api_surface", None)
    if isinstance(state, str) and state in _SURFACE_VALUES:
        return state
    if request.scope.get("route") is not None:
        return "public"
    return "none"


class CorrelationMiddleware(BaseHTTPMiddleware):
    """Add request_id to context vars for structured logging."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Use an existing (sanitized) X-Request-ID header or generate new one
        request_id = sanitize_request_id(request.headers.get("x-request-id"))
        token = request_id_var.set(request_id)

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = f"{resolve_surface(request)}:{request_id}"
            return response
        finally:
            request_id_var.reset(token)
            # Clear user/agent/surface context after request
            user_id_var.set(None)
            agent_id_var.set(None)
            surface_var.set(None)
