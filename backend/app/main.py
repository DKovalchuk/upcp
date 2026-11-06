import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.api.registry import include_surfaces
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
    version="0.22.0",
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

# Metrics middleware — Prometheus HTTP request instrumentation
try:
    from app.shared.metrics_middleware import MetricsMiddleware

    app.add_middleware(MetricsMiddleware)
except ImportError:
    pass

# Rate limiting middleware — Redis sliding window (lazy import)
try:
    from app.shared.rate_limit_middleware import RateLimitMiddleware

    if not settings.disable_rate_limit:
        app.add_middleware(RateLimitMiddleware)
except ImportError:
    pass

# Auth — per-surface dependencies (SPEC-0028 D2): the WEB and AGENT groups
# carry their auth dependency through include_surfaces(); the PUBLIC group
# and the app-level routes are declared no-auth. No path-string guard and
# no auth middleware (TASK-0170 retired AuthMiddleware/PUBLIC_PATHS).

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


# API routers — every surface declared in app/api/registry.py (SPEC-0028 §3.1)
include_surfaces(app)


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


@app.get("/metrics")
def metrics() -> Response:
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Initialize app_info metric with version and environment
try:
    from app.shared.metrics import app_info

    app_info.info({"version": "0.22.0", "environment": settings.env})
except Exception:
    pass
