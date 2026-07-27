"""Tests for Redis client and health check."""

from unittest.mock import MagicMock, patch

from app.shared.redis import check_redis_health


class TestRedisHealth:
    @patch("app.shared.redis.get_redis_client")
    def test_check_redis_health_ok(self, mock_get_client: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_get_client.return_value = mock_client

        result = check_redis_health()
        assert result["status"] == "ok"
        assert result["service"] == "redis"

    @patch("app.shared.redis.get_redis_client")
    def test_check_redis_health_connection_error(self, mock_get_client: MagicMock) -> None:
        import redis as redis_lib

        mock_get_client.side_effect = redis_lib.ConnectionError("Connection refused")

        result = check_redis_health()
        assert result["status"] == "error"
        assert "Connection refused" in result["error"]

    @patch("app.shared.redis.get_redis_client")
    def test_check_redis_health_generic_error(self, mock_get_client: MagicMock) -> None:
        mock_get_client.side_effect = RuntimeError("Something went wrong")

        result = check_redis_health()
        assert result["status"] == "error"
        assert "Something went wrong" in result["error"]
