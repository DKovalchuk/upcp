from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from app.api.v1.audit import router as audit_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.delivery import router as delivery_router
from app.api.v1.gitread import router as gitread_router
from app.api.v1.projects import router as projects_router
from app.api.v1.quality import router as quality_router
from app.api.v1.reporting import router as reporting_router
from app.api.v1.search import router as search_router
from app.api.v1.structure import router as structure_router
from app.identity.agent_endpoints import router as agent_router
from app.identity.endpoints import router as auth_router
from app.identity.middleware import AuthMiddleware
from app.mcp.server import create_mcp_router
from app.shared.config import get_settings
from app.shared.correlation import CorrelationMiddleware
from app.shared.errors import register_error_handlers
from app.shared.logging import setup_logging
from app.shared.rate_limit_middleware import RateLimitMiddleware
from app.shared.tracing import setup_tracing
from app.shared.tracing_middleware import TracingMiddleware

settings = get_settings()

# Setup structured logging
setup_logging(settings.log_level)

# Setup distributed tracing
setup_tracing()

app = FastAPI(title="UPCP Backend", version="0.1.0")
register_error_handlers(app)

# Tracing middleware — creates spans for each request
app.add_middleware(TracingMiddleware)

# Correlation middleware — adds request_id to all logs
app.add_middleware(CorrelationMiddleware)

# Rate limiting middleware — Redis sliding window
if settings.env != "test":
    app.add_middleware(RateLimitMiddleware)

# Auth middleware — protects all /api/v1/ routes except public ones
if settings.env != "test":
    app.add_middleware(AuthMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.env == "local" else [],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
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
        "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'"
    )
    return response


# API routers
app.include_router(projects_router, prefix="/api/v1")
app.include_router(structure_router, prefix="/api/v1")
app.include_router(delivery_router, prefix="/api/v1")
app.include_router(quality_router, prefix="/api/v1")
app.include_router(gitread_router, prefix="/api/v1")
app.include_router(reporting_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(audit_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")
app.include_router(agent_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/auth")

# MCP server
app.include_router(create_mcp_router(), prefix="/mcp")


@app.get("/health")
def health() -> dict[str, object]:
    from app.shared.redis import check_redis_health

    redis_status = check_redis_health()
    return {
        "status": "ok" if redis_status["status"] == "ok" else "degraded",
        "service": "upcp-backend",
        "redis": redis_status["status"],
    }


@app.get("/api/v1/health")
def api_health() -> dict[str, object]:
    return health()
