"""Tests for rate limiter."""

from unittest.mock import MagicMock, patch

from app.shared.rate_limit import check_rate_limit


class TestRateLimit:
    @patch("app.shared.rate_limit.get_redis_client")
    def test_allows_first_request(self, mock_get_client: MagicMock) -> None:
        mock_client = MagicMock()
        mock_pipe = MagicMock()
        mock_client.pipeline.return_value = mock_pipe
        mock_pipe.execute.return_value = [None, 0, True, True]  # zcard returns 0
        mock_get_client.return_value = mock_client

        result = check_rate_limit("192.168.1.1", "login")

        assert result["allowed"] is True
        assert result["remaining"] == 4  # 5 - 0 - 1

    @patch("app.shared.rate_limit.get_redis_client")
    def test_blocks_when_limit_reached(self, mock_get_client: MagicMock) -> None:
        mock_client = MagicMock()
        mock_pipe = MagicMock()
        mock_client.pipeline.return_value = mock_pipe
        mock_pipe.execute.return_value = [None, 5, True, True]  # zcard returns 5 (at limit)
        mock_get_client.return_value = mock_client

        result = check_rate_limit("192.168.1.1", "login")

        assert result["allowed"] is False
        assert result["remaining"] == 0
        assert result["retry_after"] == 60

    @patch("app.shared.rate_limit.get_redis_client")
    def test_different_routes_have_different_limits(self, mock_get_client: MagicMock) -> None:
        mock_client = MagicMock()
        mock_pipe = MagicMock()
        mock_client.pipeline.return_value = mock_pipe
        mock_get_client.return_value = mock_client

        # Login route: 5 per minute
        mock_pipe.execute.return_value = [None, 4, True, True]
        result = check_rate_limit("192.168.1.1", "login")
        assert result["limit"] == 5

        # Default route: 100 per minute
        mock_pipe.execute.return_value = [None, 50, True, True]
        result2 = check_rate_limit("192.168.1.1", "default")
        assert result2["limit"] == 100

    @patch("app.shared.rate_limit.get_redis_client")
    def test_custom_limits_override_defaults(self, mock_get_client: MagicMock) -> None:
        mock_client = MagicMock()
        mock_pipe = MagicMock()
        mock_client.pipeline.return_value = mock_pipe
        mock_pipe.execute.return_value = [None, 9, True, True]
        mock_get_client.return_value = mock_client

        result = check_rate_limit("192.168.1.1", "custom", max_requests=10, window_seconds=30)

        assert result["limit"] == 10
        assert result["window"] == 30
