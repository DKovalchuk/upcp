"""Auth middleware — protects all /api/v1/ routes except public ones."""

import hashlib
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

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
        "/mcp/health",
    }
)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class AuthMiddleware(BaseHTTPMiddleware):
    """Check JWT or agent token on all /api/v1/ routes except public ones."""

    def __init__(self, app: ASGIApp, token_service: TokenService | None = None) -> None:
        super().__init__(app)
        self._token_service = token_service or TokenService()

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        path = request.url.path

        if path in PUBLIC_PATHS:
            return await call_next(request)

        if not path.startswith("/api/v1/") and not path.startswith("/mcp"):
            return await call_next(request)

        auth_header = request.headers.get("authorization", "")
        agent_token = request.headers.get("x-agent-token")

        if not auth_header.startswith("Bearer ") and not agent_token:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing authentication token"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify JWT token
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                payload = self._token_service.verify_access_token(token)
                request.state.user_id = payload["sub"]
                request.state.auth_type = "user"
            except ValueError:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid or expired token"},
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return await call_next(request)

        # Verify agent token
        if agent_token:
            from app.identity.agents import Agent, AgentToken
            from app.shared.database import SessionLocal

            db = SessionLocal()
            try:
                token_hash = _hash_token(agent_token)
                record = db.query(AgentToken).filter_by(token_hash=token_hash).first()

                if record is None or record.revoked_at is not None:
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "Invalid agent token"},
                    )

                if record.expires_at is not None and record.expires_at < datetime.now(UTC):
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "Agent token has expired"},
                    )

                agent = db.query(Agent).filter_by(id=record.agent_id).first()
                if agent is None or not agent.is_active:
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "Agent not found or inactive"},
                    )

                record.last_used_at = datetime.now(UTC)
                db.commit()

                request.state.agent_id = agent.id
                request.state.agent_name = agent.name
                request.state.auth_type = "agent"
            except Exception:
                db.rollback()
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid agent token"},
                )
            finally:
                db.close()

        return await call_next(request)
