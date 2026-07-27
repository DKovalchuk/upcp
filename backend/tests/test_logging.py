"""Tests for correlation middleware and structured logging."""

import json
import logging
import sys

from app.shared.correlation import CorrelationMiddleware
from app.shared.logging import JSONFormatter, request_id_var, user_id_var
from fastapi import FastAPI
from fastapi.testclient import TestClient


class TestJSONFormatter:
    def test_format_basic(self) -> None:
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Hello world",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        data = json.loads(output)

        assert data["level"] == "INFO"
        assert data["logger"] == "test"
        assert data["message"] == "Hello world"
        assert "timestamp" in data

    def test_format_with_request_id(self) -> None:
        token = request_id_var.set("req-123")
        try:
            formatter = JSONFormatter()
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg="Test",
                args=(),
                exc_info=None,
            )
            output = formatter.format(record)
            data = json.loads(output)
            assert data["request_id"] == "req-123"
        finally:
            request_id_var.reset(token)

    def test_format_with_user_id(self) -> None:
        token = user_id_var.set("user-456")
        try:
            formatter = JSONFormatter()
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="",
                lineno=0,
                msg="Test",
                args=(),
                exc_info=None,
            )
            output = formatter.format(record)
            data = json.loads(output)
            assert data["user_id"] == "user-456"
        finally:
            user_id_var.reset(token)

    def test_format_exception(self) -> None:
        formatter = JSONFormatter()
        try:
            raise ValueError("Something went wrong")
        except ValueError:
            record = logging.LogRecord(
                name="test",
                level=logging.ERROR,
                pathname="",
                lineno=0,
                msg="Error occurred",
                args=(),
                exc_info=sys.exc_info(),
            )
            output = formatter.format(record)
            data = json.loads(output)
            assert data["exception"]["type"] == "ValueError"
            assert data["exception"]["message"] == "Something went wrong"


class TestCorrelationMiddleware:
    def test_generates_request_id(self) -> None:
        app = FastAPI()
        app.add_middleware(CorrelationMiddleware)

        @app.get("/test")
        async def test_route() -> dict:
            return {"request_id": request_id_var.get()}

        client = TestClient(app)
        resp = client.get("/test")
        assert resp.status_code == 200
        assert "X-Request-ID" in resp.headers
        assert len(resp.headers["X-Request-ID"]) > 0

    def test_preserves_existing_request_id(self) -> None:
        app = FastAPI()
        app.add_middleware(CorrelationMiddleware)

        @app.get("/test")
        async def test_route() -> dict:
            return {"request_id": request_id_var.get()}

        client = TestClient(app)
        resp = client.get("/test", headers={"X-Request-ID": "my-custom-id"})
        assert resp.headers["X-Request-ID"] == "my-custom-id"

    def test_request_id_in_response_header(self) -> None:
        app = FastAPI()
        app.add_middleware(CorrelationMiddleware)

        @app.get("/test")
        async def test_route() -> dict:
            return {"ok": True}

        client = TestClient(app)
        resp = client.get("/test")
        assert "X-Request-ID" in resp.headers
