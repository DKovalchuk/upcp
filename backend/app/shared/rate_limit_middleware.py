"""Rate limiting middleware — protects endpoints from abuse."""

from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from app.shared.logging import get_logger
from app.shared.rate_limit import check_rate_limit

logger = get_logger(__name__)

# Routes that need stricter limits
STRICT_ROUTES = {
    "/auth/login": "login",
    "/auth/setup": "setup",
    "/auth/refresh": "refresh",
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limit all API requests using Redis sliding window."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Only rate limit API routes
        if not request.url.path.startswith("/api/v1/") and not request.url.path.startswith(
            "/auth/"
        ):
            return await call_next(request)

        # Skip health and docs
        if request.url.path in ("/health", "/api/v1/health", "/docs", "/openapi.json"):
            return await call_next(request)

        # Get client identifier (IP or user_id)
        client_ip = request.client.host if request.client else "unknown"

        # Determine route type for per-route limits
        route = "default"
        for path, route_type in STRICT_ROUTES.items():
            if request.url.path.startswith(path):
                route = route_type
                break

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

        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(result["limit"])
        response.headers["X-RateLimit-Remaining"] = str(result["remaining"])

        return response
