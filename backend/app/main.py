import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from app.api.v1.agent_self import router as agent_self_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.audit import router as audit_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.delivery import router as delivery_router
from app.api.v1.gitread import router as gitread_router
from app.api.v1.notification_channels import router as notification_channels_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.projects import router as projects_router
from app.api.v1.quality import router as quality_router
from app.api.v1.reaper import router as reaper_router
from app.api.v1.reporting import router as reporting_router
from app.api.v1.search import router as search_router
from app.api.v1.structure import router as structure_router
from app.api.v1.task_workflow import router as workflow_router
from app.identity.agent_endpoints import router as agent_router
from app.identity.endpoints import router as auth_router
from app.identity.middleware import AuthMiddleware
from app.mcp.server import create_mcp_router
from app.shared.config import get_settings
from app.shared.correlation import CorrelationMiddleware
from app.shared.database import check_db_health
from app.shared.errors import register_error_handlers
from app.shared.logging import setup_logging

settings = get_settings()

# Setup structured logging
setup_logging(settings.log_level)

# Setup distributed tracing (lazy import to avoid CI failures)
try:
    from app.shared.tracing import setup_tracing

    setup_tracing()
except ImportError:
    pass


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:  # noqa: ARG001
    """Application lifespan — start background tasks on startup, cancel on shutdown."""
    from app.delivery.stale_reaper import stale_reaper_loop
    from app.shared.database import SessionLocal
    from app.shared.event_setup import setup_event_handlers

    setup_event_handlers()
    reaper_task = asyncio.create_task(stale_reaper_loop(SessionLocal))
    try:
        yield
    finally:
        reaper_task.cancel()


app = FastAPI(
    title="UPCP Backend",
    version="0.1.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "projects", "description": "Project CRUD operations"},
        {"name": "structure", "description": "Components and modules within projects"},
        {"name": "delivery", "description": "Features, tasks, and subtasks"},
        {"name": "quality", "description": "Acceptance criteria and DoD items"},
        {"name": "gitread", "description": "Git provider integration"},
        {"name": "reports", "description": "Project reports and daily summaries"},
        {"name": "dashboard", "description": "Dashboard stats and attention overview"},
        {"name": "audit", "description": "Audit event timeline"},
        {"name": "search", "description": "Global search across entities"},
        {
            "name": "workflow",
            "description": "Agent task workflow (claims, heartbeats, clarifications)",
        },
        {"name": "agent-self", "description": "Agent self-service endpoints"},
        {"name": "notifications", "description": "User notifications"},
    ],
)
register_error_handlers(app)

# Tracing middleware — creates spans for each request (lazy import)
try:
    from app.shared.tracing_middleware import TracingMiddleware

    app.add_middleware(TracingMiddleware)
except ImportError:
    pass

# Correlation middleware — adds request_id to all logs
app.add_middleware(CorrelationMiddleware)

# Rate limiting middleware — Redis sliding window (lazy import)
try:
    from app.shared.rate_limit_middleware import RateLimitMiddleware

    if not settings.disable_rate_limit:
        app.add_middleware(RateLimitMiddleware)
except ImportError:
    pass

# Auth middleware — protects all /api/v1/ and /mcp/ routes except public ones
if not settings.disable_auth:
    app.add_middleware(AuthMiddleware)

# CORS — configured via UPCP_CORS_ORIGINS and UPCP_CORS_ALLOW_HEADERS env vars
app.add_middleware(
    CORSMiddleware,
    allow_origins=getattr(settings, "cors_origins_list", []),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=getattr(settings, "cors_allow_headers_list", []),
)


# Security headers
@app.middleware("http")
async def security_headers(request: Request, call_next: object) -> Response:
    response: Response = await call_next(request)  # type: ignore[operator]
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'"
    )
    return response


# API routers
app.include_router(projects_router, prefix="/api/v1")
app.include_router(structure_router, prefix="/api/v1")
app.include_router(workflow_router, prefix="/api/v1")
app.include_router(delivery_router, prefix="/api/v1")
app.include_router(quality_router, prefix="/api/v1")
app.include_router(gitread_router, prefix="/api/v1")
app.include_router(reporting_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(audit_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")
app.include_router(agent_self_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")
app.include_router(notification_channels_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(agent_router, prefix="/api/v1")
app.include_router(reaper_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/auth")

# MCP server
app.include_router(create_mcp_router(), prefix="/mcp")


@app.get("/health")
def health() -> dict[str, object]:
    # Check Redis
    try:
        from app.shared.redis import check_redis_health

        redis_status = check_redis_health()
    except ImportError:
        redis_status = {"status": "unavailable", "service": "redis"}

    # Check PostgreSQL
    db_status = check_db_health()

    # Compute overall status
    statuses = [redis_status["status"], db_status["status"]]
    if statuses.count("ok") == 2:
        overall = "ok"
    elif statuses.count("ok") == 0:
        overall = "error"
    else:
        overall = "degraded"

    return {
        "status": overall,
        "service": "upcp-backend",
        "db": db_status,
        "redis": redis_status,
    }


@app.get("/api/v1/health")
def api_health() -> dict[str, object]:
    return health()
