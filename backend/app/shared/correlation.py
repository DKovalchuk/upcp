"""Request ID correlation middleware — adds request_id to all logs."""

import uuid
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from app.shared.logging import agent_id_var, request_id_var, user_id_var


class CorrelationMiddleware(BaseHTTPMiddleware):
    """Add request_id to context vars for structured logging."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Use existing X-Request-ID header or generate new one
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        token = request_id_var.set(request_id)

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            request_id_var.reset(token)
            # Clear user/agent context after request
            user_id_var.set(None)
            agent_id_var.set(None)
