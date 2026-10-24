"""Auth middleware — protects all /api/v1/ routes except public ones.

SPEC-0027 §3.2 / TASK-0146 (finding 2): a valid signature alone is not
enough — after ``verify_access_token`` the subject must exist and be
active, otherwise the token is rejected 401 (same shape as an invalid
token). Resolution: Redis negative cache ``auth:user:{sub}``
("active"/"unknown"/"disabled", TTL 60 s) with DB fallback; Redis
outage → direct DB query (no auth bypass), cache write best-effort.
Agent-token branch already DB-checks — unchanged.
"""

import contextlib
import hashlib
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from app.identity.token_service import TokenService
from app.shared.logging import get_logger
from app.shared.metrics import auth_subject_rejections_total
from app.shared.redis import get_redis_client

logger = get_logger(__name__)

_USER_STATE_TTL_SECONDS = 60

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


def _fetch_user_state(user_id: str) -> str:
    """Subject lookup → ``"active" | "unknown" | "disabled"``.

    ``SessionLocal`` is imported lazily (agent-branch pattern) so tests
    can redirect the middleware to the test DB by patching
    ``app.shared.database.SessionLocal``.
    """
    from app.identity.models import User
    from app.shared.database import SessionLocal

    db = SessionLocal()
    try:
        user = db.get(User, user_id)
    finally:
        db.close()
    if user is None:
        return "unknown"
    return "active" if user.is_active else "disabled"


def _user_state(user_id: str) -> str:
    """Cached subject lookup (SPEC-0027 §3.2): Redis, then DB fallback.

    Redis outage → DB query (no auth bypass); cache write is
    best-effort — the DB stays authoritative.
    """
    key = f"auth:user:{user_id}"
    try:
        raw = get_redis_client().get(key)
    except Exception:
        raw = None  # Redis down → fall through to the DB
    if raw is not None:
        return str(raw)
    state = _fetch_user_state(user_id)
    # best-effort cache write — the DB stays authoritative
    with contextlib.suppress(Exception):
        get_redis_client().set(key, state, ex=_USER_STATE_TTL_SECONDS)
    return state


def _reject_subject(user_id: str, reason: str) -> JSONResponse:
    """Structured denial (log + metric + span attrs) and the standard 401."""
    auth_subject_rejections_total.labels(reason=reason).inc()
    logger.warning(
        "auth middleware: rejecting valid JWT — subject=%s state=%s",
        user_id,
        reason,
        extra={"action": "auth.subject_rejected", "entity_type": "jwt_subject"},
    )
    try:
        from opentelemetry import trace
    except ImportError:
        trace = None  # type: ignore[assignment]  # opentelemetry optional
    if trace is not None:
        span = trace.get_current_span()
        if span.is_recording():
            span.set_attributes(
                {
                    "upcp.auth.subject_rejected": True,
                    "upcp.auth.subject_state": reason,
                    "upcp.auth.sub": user_id,
                }
            )
    return JSONResponse(
        status_code=401,
        content={"detail": "Invalid or expired token"},
        headers={"WWW-Authenticate": "Bearer"},
    )


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
            except ValueError:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid or expired token"},
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # SPEC-0027 §3.2: valid signature ≠ live account (finding 2)
            state = _user_state(str(payload["sub"]))
            if state != "active":
                return _reject_subject(str(payload["sub"]), state)

            request.state.user_id = payload["sub"]
            request.state.auth_type = "user"
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
