from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Base for all UPCP typed errors."""

    error_code: str = "internal_error"
    status_code: int = 500

    def __init__(self, detail: str = "") -> None:
        self.detail = detail


class NotFound(AppError):
    error_code = "not_found"
    status_code = 404


class ValidationError(AppError):
    error_code = "validation_error"
    status_code = 422


class Conflict(AppError):
    error_code = "conflict"
    status_code = 409


class InternalError(AppError):
    error_code = "internal_error"
    status_code = 500


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.error_code, "detail": exc.detail},
        )
