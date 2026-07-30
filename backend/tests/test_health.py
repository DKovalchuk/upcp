from unittest.mock import patch

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health_returns_ok() -> None:
    with (
        patch(
            "app.shared.redis.check_redis_health",
            return_value={"status": "ok", "service": "redis"},
        ),
        patch(
            "app.main.check_db_health",
            return_value={"status": "ok", "latency_ms": 1.23},
        ),
    ):
        response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "upcp-backend"
    assert data["status"] == "ok"
    assert data["redis"]["status"] == "ok"
    assert data["db"]["status"] == "ok"
    assert "latency_ms" in data["db"]


def test_health_degraded_without_redis() -> None:
    with (
        patch(
            "app.shared.redis.check_redis_health",
            return_value={"status": "error", "service": "redis", "error": "Connection refused"},
        ),
        patch(
            "app.main.check_db_health",
            return_value={"status": "ok", "latency_ms": 1.0},
        ),
    ):
        response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert data["redis"]["status"] == "error"
    assert data["redis"]["error"] == "Connection refused"
    assert data["db"]["status"] == "ok"


def test_health_degraded_without_db() -> None:
    with (
        patch(
            "app.shared.redis.check_redis_health",
            return_value={"status": "ok", "service": "redis"},
        ),
        patch(
            "app.main.check_db_health",
            return_value={"status": "error", "error": "Connection refused"},
        ),
    ):
        response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert data["redis"]["status"] == "ok"
    assert data["db"]["status"] == "error"
    assert data["db"]["error"] == "Connection refused"


def test_health_error_when_both_fail() -> None:
    with (
        patch(
            "app.shared.redis.check_redis_health",
            return_value={"status": "error", "service": "redis", "error": "Connection refused"},
        ),
        patch(
            "app.main.check_db_health",
            return_value={"status": "error", "error": "Connection refused"},
        ),
    ):
        response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert data["redis"]["status"] == "error"
    assert data["db"]["status"] == "error"


def test_api_health_endpoint_returns_same_shape() -> None:
    with (
        patch(
            "app.shared.redis.check_redis_health",
            return_value={"status": "ok", "service": "redis"},
        ),
        patch(
            "app.main.check_db_health",
            return_value={"status": "ok", "latency_ms": 0.5},
        ),
    ):
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "upcp-backend"
    assert data["status"] == "ok"
    assert "db" in data
    assert "redis" in data
