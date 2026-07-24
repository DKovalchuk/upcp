from fastapi import FastAPI

from app.shared.errors import register_error_handlers

app = FastAPI(title="UPCP Backend")
register_error_handlers(app)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "upcp-backend",
    }
