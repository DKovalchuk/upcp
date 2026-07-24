from fastapi import FastAPI

from app.api.v1.projects import router as projects_router
from app.shared.errors import register_error_handlers

app = FastAPI(title="UPCP Backend")
register_error_handlers(app)
app.include_router(projects_router, prefix="/api/v1")


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "upcp-backend",
    }
