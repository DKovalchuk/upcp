"""Redis client — connection pool with graceful degradation."""

from typing import Any

from app.shared.config import get_settings


def get_redis_client() -> Any:
    """Get Redis client with connection pooling.

    Returns a Redis client configured from app settings.
    Connection is lazy — won't fail until first actual command.
    """
    import redis as redis_lib

    settings = get_settings()
    return redis_lib.Redis.from_url(
        settings.redis_url,
        decode_responses=True,
        max_connections=20,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True,
    )


def check_redis_health() -> dict[str, object]:
    """Check Redis connectivity. Returns health status."""
    try:
        import redis as redis_lib

        client = get_redis_client()
        client.ping()
        return {"status": "ok", "service": "redis"}
    except ImportError:
        return {"status": "unavailable", "service": "redis", "error": "redis package not installed"}
    except redis_lib.ConnectionError:
        return {"status": "error", "service": "redis", "error": "Connection refused"}
    except Exception as e:
        return {"status": "error", "service": "redis", "error": str(e)}
