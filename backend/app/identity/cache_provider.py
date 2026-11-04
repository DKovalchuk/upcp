"""Auth cache provider — the only Redis access in the auth path (SPEC-0029 D1/S29.2).

Wraps ``app.shared.redis.get_redis_client`` for the layering pilot
(TASK-0174): identity cache access lives here and in ``shared/redis.py``
only (AC1). Contract:

- ``get`` → ``str | None`` (bytes payloads are decoded — a client without
  ``decode_responses`` must not leak ``b'...'`` into subject state);
- NEVER raises to callers: every failure degrades to a structured
  warning (``action=auth.cache_{get,set,delete}_failed``) plus a miss /
  no-op, so services fall back to the DB (no auth bypass);
- the Redis client is imported LAZILY inside each method so tests patch
  ``app.shared.redis.get_redis_client`` (the denylist seam pattern);
- TTL/eviction policy belongs to the services (D1) — the provider only
  forwards ``ttl_seconds`` as the Redis ``ex`` argument.
"""

from __future__ import annotations

from app.shared.logging import get_logger

logger = get_logger(__name__)


class AuthCacheProvider:
    """Injectable cache source for auth services (fake in tests)."""

    def get(self, key: str) -> str | None:
        """Cached value or ``None`` on miss/outage (outage = warning)."""
        try:
            from app.shared.redis import get_redis_client  # lazy — test seam

            raw = get_redis_client().get(key)
            if raw is None:
                return None
            return raw.decode() if isinstance(raw, bytes) else str(raw)
        except Exception:
            logger.warning(
                "auth cache: get failed — treating as a cache miss",
                extra={
                    "action": "auth.cache_get_failed",
                    "entity_type": "auth_cache",
                    "cache_key": key,
                },
            )
            return None

    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        """Best-effort write with TTL; failure logs and degrades (no raise)."""
        try:
            from app.shared.redis import get_redis_client  # lazy — test seam

            get_redis_client().set(key, value, ex=ttl_seconds)
        except Exception:
            logger.warning(
                "auth cache: set failed — entry stays stale until TTL/DB write",
                extra={
                    "action": "auth.cache_set_failed",
                    "entity_type": "auth_cache",
                    "cache_key": key,
                    "ttl_seconds": ttl_seconds,
                },
            )

    def delete(self, key: str) -> None:
        """Best-effort invalidation; failure logs and degrades (no raise)."""
        try:
            from app.shared.redis import get_redis_client  # lazy — test seam

            get_redis_client().delete(key)
        except Exception:
            logger.warning(
                "auth cache: delete failed — entry stays until TTL",
                extra={
                    "action": "auth.cache_delete_failed",
                    "entity_type": "auth_cache",
                    "cache_key": key,
                },
            )
