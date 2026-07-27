"""Auth middleware — protects all /api/v1/ routes except public ones."""

from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from app.identity.token_service import TokenService

PUBLIC_PATHS = frozenset(
    {
        "/health",
        "/api/v1/health",
        "/auth/setup",
        "/auth/login",
        "/auth/refresh",
        "/docs",
        "/openapi.json",
        "/redoc",
    }
)


class AuthMiddleware(BaseHTTPMiddleware):
    """Check JWT on all /api/v1/ routes except public ones."""

    def __init__(self, app: ASGIApp, token_service: TokenService | None = None) -> None:
        super().__init__(app)
        self._token_service = token_service or TokenService()

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        path = request.url.path

        # Skip auth for public paths
        if path in PUBLIC_PATHS:
            return await call_next(request)

        # Skip auth for non-API routes
        if not path.startswith("/api/v1/"):
            return await call_next(request)

        # Skip auth for MCP endpoint
        if path.startswith("/mcp"):
            return await call_next(request)

        # Extract token from Authorization header
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing authentication token"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = auth_header[7:]  # Remove "Bearer " prefix

        # Also check X-Agent-Token header
        agent_token = request.headers.get("x-agent-token")

        if not token and not agent_token:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing authentication token"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify JWT token
        if token:
            try:
                payload = self._token_service.verify_access_token(token)
                # Attach user info to request state
                request.state.user_id = payload["sub"]
                request.state.auth_type = "user"
            except ValueError:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid or expired token"},
                    headers={"WWW-Authenticate": "Bearer"},
                )

        # TODO: Verify agent token (TASK-0068)
        if agent_token:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid agent token"},
            )

        return await call_next(request)
