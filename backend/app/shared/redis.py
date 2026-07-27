"""Redis client — connection pool with graceful degradation."""

from functools import lru_cache

import redis

from app.shared.config import get_settings


@lru_cache(maxsize=1)
def get_redis_client() -> redis.Redis:
    """Get Redis client with connection pooling.

    Returns a Redis client configured from app settings.
    Connection is lazy — won't fail until first actual command.
    """
    settings = get_settings()
    return redis.Redis.from_url(
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
        client = get_redis_client()
        client.ping()
        return {"status": "ok", "service": "redis"}
    except redis.ConnectionError:
        return {"status": "error", "service": "redis", "error": "Connection refused"}
    except Exception as e:
        return {"status": "error", "service": "redis", "error": str(e)}
