"""Tracing middleware — creates spans for each request."""

from collections.abc import Awaitable, Callable

from opentelemetry import trace
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from app.shared.logging import request_id_var

tracer = trace.get_tracer("upcp.http")


class TracingMiddleware(BaseHTTPMiddleware):
    """Create OpenTelemetry spans for each HTTP request."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        with tracer.start_as_current_span(
            f"{request.method} {request.url.path}",
            attributes={
                "http.method": request.method,
                "http.url": str(request.url),
                "http.scheme": request.url.scheme,
                "http.host": request.url.hostname or "",
                "http.target": request.url.path,
            },
        ) as span:
            # Add correlation IDs to span
            request_id = request_id_var.get()
            if request_id:
                span.set_attribute("request.id", request_id)

            try:
                response = await call_next(request)
                span.set_attribute("http.status_code", response.status_code)
                span.set_status(
                    trace.StatusCode.OK if response.status_code < 400 else trace.StatusCode.ERROR
                )
                return response
            except Exception as e:
                span.set_status(trace.StatusCode.ERROR, str(e))
                span.record_exception(e)
                raise
