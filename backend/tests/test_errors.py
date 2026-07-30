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


# ── Catch-all handler tests ───────────────────────────────────────


def test_catch_all_returns_sanitized_message() -> None:
    """Unhandled exceptions should NOT expose internal details."""
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/explode")
    def explode() -> None:
        raise RuntimeError("secret database password is xyz")

    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/explode")

    assert resp.status_code == 500
    body = resp.json()
    assert body["error"] == "internal_error"
    assert "secret database" not in body["detail"]
    assert body["detail"] == "An unexpected error occurred"


def test_catch_all_does_not_leak_stack_trace() -> None:
    """Response should not contain file paths or traceback info."""
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/crash")
    def crash() -> None:
        raise ValueError("/home/admin/supersecret/path")

    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/crash")

    assert resp.status_code == 500
    body = resp.json()
    assert "/home/admin" not in str(body)
    assert body["detail"] == "An unexpected error occurred"


def test_app_errors_still_return_detail() -> None:
    """AppError subclasses should still return their specific detail."""
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/notfound")
    def notfound() -> None:
        raise NotFound("project xyz not found")

    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/notfound")

    assert resp.status_code == 404
    assert resp.json()["detail"] == "project xyz not found"
