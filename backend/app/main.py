from fastapi import FastAPI

from app.api.v1.delivery import router as delivery_router
from app.api.v1.gitread import router as gitread_router
from app.api.v1.projects import router as projects_router
from app.api.v1.quality import router as quality_router
from app.api.v1.structure import router as structure_router
from app.shared.errors import register_error_handlers

app = FastAPI(title="UPCP Backend")
register_error_handlers(app)
app.include_router(projects_router, prefix="/api/v1")
app.include_router(structure_router, prefix="/api/v1")
app.include_router(delivery_router, prefix="/api/v1")
app.include_router(quality_router, prefix="/api/v1")
app.include_router(gitread_router, prefix="/api/v1")


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "upcp-backend",
    }
