"""Rate limiting middleware — global pre-auth floor for EVERY request.

TASK-0173 / SPEC-0028 AC9 (Shape A): the historical implementation gated
coverage by version-prefix path strings (``/api/v1/`` / ``/auth/``) — the
finding this module kills. Coverage is now default-deny: every path
consumes an IP-keyed floor bucket except an EXACT-path public skip set
(health checks, metrics scrapers, docs). Unknown and future prefixes are
limited by default; there is no route classification here at all — the
per-surface, principal-keyed policy lives in ``rate_limit.SurfaceRateLimit``,
attached after the auth dependency (Decision D2: one implementation,
difference carried by data).

The strict buckets (login/setup/refresh) are keyed by exact full path —
the values in ``STRICT_ROUTES`` are the registered endpoints themselves.
Mounted by ``main.py`` only when ``disable_rate_limit`` is false (the
historical registration gate, pinned by test_dashboard_security E8).
"""

from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from app.shared.logging import get_logger
from app.shared.rate_limit import check_rate_limit

logger = get_logger(__name__)

# Routes that need stricter limits (exact full paths — no prefix matching)
STRICT_ROUTES = {
    "/auth/login": "login",
    "/auth/setup": "setup",
    "/auth/refresh": "refresh",
}

# Declared public infra endpoints: never consume a rate bucket
# (healthchecks, Prometheus scrape, interactive API docs). Exact paths only.
PUBLIC_SKIP_PATHS = frozenset(
    {
        "/health",
        "/api/v1/health",
        "/metrics",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/docs/oauth2-redirect",
    }
)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Global pre-auth floor: IP-keyed Redis sliding window on every path."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        path = request.url.path

        # Skip the exact public infra paths
        if path in PUBLIC_SKIP_PATHS:
            return await call_next(request)

        # Get client identifier (IP)
        client_ip = request.client.host if request.client else "unknown"

        # Determine strict bucket for exact sensitive routes
        route = STRICT_ROUTES.get(path, "default")

        # Check rate limit
        result = check_rate_limit(client_ip, route)

        if not result["allowed"]:
            logger.warning(
                "Rate limit exceeded",
                extra={"entity_type": "rate_limit", "action": "blocked", "client_ip": client_ip},
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests",
                    "retry_after": result["retry_after"],
                },
                headers={
                    "Retry-After": str(result["retry_after"]),
                    "X-RateLimit-Limit": str(result["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(result["window"]),
                },
            )

        response = await call_next(request)

        # Add rate limit headers to response: prefer the per-surface result
        # the SurfaceRateLimit dependency stashed (surface-limited responses
        # must report their own bucket), else the floor's own numbers.
        surface_result = getattr(request.state, "surface_rate_limit", None)
        shown = surface_result if isinstance(surface_result, dict) else result
        if "X-RateLimit-Limit" not in response.headers:
            response.headers["X-RateLimit-Limit"] = str(shown["limit"])
        if "X-RateLimit-Remaining" not in response.headers:
            response.headers["X-RateLimit-Remaining"] = str(shown["remaining"])

        return response
