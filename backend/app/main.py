from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.delivery import router as delivery_router
from app.api.v1.gitread import router as gitread_router
from app.api.v1.projects import router as projects_router
from app.api.v1.quality import router as quality_router
from app.api.v1.reporting import router as reporting_router
from app.api.v1.structure import router as structure_router
from app.mcp.server import create_mcp_router
from app.shared.config import get_settings
from app.shared.errors import register_error_handlers

settings = get_settings()

app = FastAPI(title="UPCP Backend", version="0.1.0")
register_error_handlers(app)

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
    return response


# API routers
app.include_router(projects_router, prefix="/api/v1")
app.include_router(structure_router, prefix="/api/v1")
app.include_router(delivery_router, prefix="/api/v1")
app.include_router(quality_router, prefix="/api/v1")
app.include_router(gitread_router, prefix="/api/v1")
app.include_router(reporting_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")

# MCP server
app.include_router(create_mcp_router(), prefix="/mcp")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "upcp-backend"}
