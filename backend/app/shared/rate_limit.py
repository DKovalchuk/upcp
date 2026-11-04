"""Rate limiter — Redis sliding window with per-route limits.

Two layers, one implementation (SPEC-0028 D2/AC9, TASK-0173 Shape A):

- the global pre-auth IP floor lives in ``rate_limit_middleware`` (the
  historical ``DEFAULT_LIMITS`` buckets below);
- :class:`SurfaceRateLimit` is the per-surface policy attached in
  ``include_surfaces`` right AFTER the auth blanket — principal-keyed,
  thresholds from ``UPCP_RATE_LIMIT_{WEB,AGENT}_{MAX,WINDOW}``.
"""

from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, Request, status
from starlette.concurrency import run_in_threadpool

from app.shared.config import Settings, get_settings
from app.shared.logging import get_logger
from app.shared.redis import get_redis_client

logger = get_logger(__name__)

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

    Redis outage FAILS OPEN (review FIX 2 — availability posture matching
    ``identity/denylist.py``'s ``auth.denylist_unavailable`` precedent): any
    Redis exception allows the request with a structured
    ``action=ratelimit.unavailable`` warning instead of 500ing the route.
    Tradeoff: no throttling while Redis is down; the auth layer and the
    per-route logic are unaffected.

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

    try:
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
            denied = True
        else:
            denied = False
    except Exception as exc:
        logger.warning(
            "rate limiter unavailable — allowing request (fail-open): %s",
            exc,
            extra={"action": "ratelimit.unavailable", "entity_type": "rate_limit"},
        )
        return {
            "allowed": True,
            "remaining": max(0, max_req - 1),
            "retry_after": None,
            "limit": max_req,
            "window": window,
        }

    if denied:
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


class SurfaceRateLimit:
    """Per-surface rate policy dependency (SPEC-0028 AC9, TASK-0173).

    Attached in ``include_surfaces`` right AFTER the auth blanket, so it
    keys on the principal the blanket stored (``user_id``/``agent_id``) with
    an IP fallback (hermetic mode / requests without a principal). Honors
    ``settings.disable_rate_limit`` per request — the always-attached
    equivalent of the middleware's registration gate in ``main.py``. The
    result is stashed on ``request.state.surface_rate_limit`` so the outer
    floor middleware reports the surface bucket's headers, not its own.
    """

    def __init__(self, surface: str) -> None:
        if surface not in ("web", "agent"):
            raise ValueError(f"unknown api surface for rate policy: {surface!r}")
        self.surface = surface

    def _limits(self, settings: Settings) -> tuple[int, int]:
        if self.surface == "web":
            return settings.rate_limit_web_max, settings.rate_limit_web_window
        return settings.rate_limit_agent_max, settings.rate_limit_agent_window

    def _identifier(self, request: Request) -> str:
        if self.surface == "web":
            principal_attr = "user_id"
            prefix = "user"
        else:
            principal_attr = "agent_id"
            prefix = "agent"
        principal = getattr(request.state, principal_attr, None)
        if isinstance(principal, str) and principal:
            return f"{prefix}:{principal}"
        ip = request.client.host if request.client else "unknown"
        return f"ip:{ip}"

    async def __call__(self, request: Request) -> None:
        settings = get_settings()
        if settings.disable_rate_limit:
            return  # same observable parity as the middleware mount gate
        max_requests, window = self._limits(settings)
        # sync Redis I/O off the event loop (S28.2 rule, auth-deps pattern)
        result = await run_in_threadpool(
            check_rate_limit,
            self._identifier(request),
            f"surface_{self.surface}",
            max_requests=max_requests,
            window_seconds=window,
        )
        request.state.surface_rate_limit = result
        if not result["allowed"]:
            # surface_var is already set by the auth blanket (it ran first),
            # so this warning is emitted with the surface in the log record.
            logger.warning(
                "Rate limit exceeded",
                extra={"entity_type": "rate_limit", "action": "blocked"},
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests",
                headers={"Retry-After": str(result["retry_after"])},
            ) from None


def surface_rate_limit(surface: str) -> SurfaceRateLimit:
    """Composition-friendly factory for the per-surface policy dependency."""
    return SurfaceRateLimit(surface)
