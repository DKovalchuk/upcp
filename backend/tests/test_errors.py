from app.shared.errors import (
    AppError,
    Conflict,
    InternalError,
    NotFound,
    ValidationError,
    register_error_handlers,
)
from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_exceptions_are_app_error_subclass() -> None:
    assert issubclass(NotFound, AppError)
    assert issubclass(ValidationError, AppError)
    assert issubclass(Conflict, AppError)
    assert issubclass(InternalError, AppError)


def test_error_handler_returns_json() -> None:
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/boom")
    def boom() -> None:
        raise NotFound("project not found")

    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/boom")

    assert resp.status_code == 404
    body = resp.json()
    assert body["error"] == "not_found"
    assert body["detail"] == "project not found"


def test_validation_error_returns_422() -> None:
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/bad")
    def bad() -> None:
        raise ValidationError("name is required")

    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/bad")

    assert resp.status_code == 422
    assert resp.json()["error"] == "validation_error"
