from unittest.mock import patch

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health_returns_ok() -> None:
    with patch(
        "app.shared.redis.check_redis_health", return_value={"status": "ok", "service": "redis"}
    ):
        response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "upcp-backend"
    assert data["redis"] == "ok"


def test_health_degraded_without_redis() -> None:
    with patch(
        "app.shared.redis.check_redis_health",
        return_value={"status": "error", "service": "redis", "error": "Connection refused"},
    ):
        response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert data["redis"] == "error"
