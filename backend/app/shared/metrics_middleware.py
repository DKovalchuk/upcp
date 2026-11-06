"""Metrics middleware — automatic HTTP request instrumentation for Prometheus."""

import time
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from app.shared.correlation import resolve_surface
from app.shared.metrics import (
    http_request_duration_seconds,
    http_requests_in_progress,
    http_requests_total,
)

# Endpoints that don't need metrics (too high volume or internal)
_SKIP_PATHS = frozenset({"/health", "/api/v1/health", "/metrics", "/docs", "/openapi.json"})


def _normalize_handler(path: str) -> str:
    """Normalize path to a stable handler label.

    /api/v1/projects/abc-123/tasks → /api/v1/projects/*/tasks
    /api/v1/tasks/abc-123/claim → /api/v1/tasks/*/claim
    """
    parts = path.strip("/").split("/")
    normalized = []
    for part in parts:
        # Treat UUIDs and numeric IDs as wildcards
        if len(part) > 8 and ("-" in part or (part.isdigit() and len(part) > 3)):
            normalized.append("*")
        else:
            normalized.append(part)
    return "/" + "/".join(normalized)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Collect HTTP request metrics for Prometheus."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        path = request.url.path

        if path in _SKIP_PATHS:
            return await call_next(request)

        handler = _normalize_handler(path)
        method = request.method

        http_requests_in_progress.labels(method=method).inc()
        start = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            status = "500"
            surface = resolve_surface(request)
            http_requests_total.labels(
                method=method, handler=handler, status=status, surface=surface
            ).inc()
            raise
        else:
            status = str(response.status_code)
            # TASK-0173: post-call_next the auth blankets have attributed
            # the request (401 denials included); unattributed → public/none.
            surface = resolve_surface(request)
            http_requests_total.labels(
                method=method, handler=handler, status=status, surface=surface
            ).inc()
            return response
        finally:
            duration = time.perf_counter() - start
            http_request_duration_seconds.labels(
                method=method, handler=handler, surface=resolve_surface(request)
            ).observe(duration)
            http_requests_in_progress.labels(method=method).dec()
