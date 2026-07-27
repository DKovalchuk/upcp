"""Rate limiter — Redis sliding window with per-route limits."""

from datetime import UTC, datetime
from typing import Any

from app.shared.redis import get_redis_client

# Default limits: (max_requests, window_seconds)
DEFAULT_LIMITS: dict[str, tuple[int, int]] = {
    "login": (5, 60),  # 5 attempts per minute
    "setup": (1, 86400),  # 1 attempt per day
    "refresh": (10, 60),  # 10 per minute
    "default": (100, 60),  # 100 per minute
}


def _get_client_key(identifier: str, route: str) -> str:
    return f"rate_limit:{route}:{identifier}"


def check_rate_limit(
    identifier: str,
    route: str = "default",
    max_requests: int | None = None,
    window_seconds: int | None = None,
) -> dict[str, object]:
    """Check rate limit using Redis sliding window.

    Args:
        identifier: Unique identifier (IP, user_id, etc.)
        route: Route name for per-route limits
        max_requests: Override default max requests
        window_seconds: Override default window

    Returns:
        dict with allowed (bool), remaining (int), retry_after (int|None)
    """
    limits = DEFAULT_LIMITS.get(route, DEFAULT_LIMITS["default"])
    max_req = max_requests or limits[0]
    window = window_seconds or limits[1]

    client: Any = get_redis_client()
    key = _get_client_key(identifier, route)
    now = datetime.now(UTC).timestamp()

    # Sliding window using sorted sets
    pipe = client.pipeline(transaction=True)

    # Remove entries outside window
    pipe.zremrangebyscore(key, 0, now - window)

    # Count current entries
    pipe.zcard(key)

    # Add current request
    pipe.zadd(key, {f"{now}": now})

    # Set TTL on key
    pipe.expire(key, window)

    results = pipe.execute()
    current_count = results[1]  # zcard result

    if current_count >= max_req:
        # Rate limited — remove the entry we just added
        client.zrem(key, f"{now}")
        retry_after = window  # Wait for full window to expire
        return {
            "allowed": False,
            "remaining": 0,
            "retry_after": retry_after,
            "limit": max_req,
            "window": window,
        }

    remaining = max_req - current_count - 1
    return {
        "allowed": True,
        "remaining": max(0, remaining),
        "retry_after": None,
        "limit": max_req,
        "window": window,
    }
