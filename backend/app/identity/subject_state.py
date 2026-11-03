"""SubjectStateService — cached subject lookup (SPEC-0029 §3.3 / TASK-0174).

Cache-aside extraction of ``middleware._user_state`` (D4 behavior
parity): key ``auth:user:{user_id}``, TTL 60 s; hit → return; miss →
``UserRepository.get_auth_state`` → best-effort cache write; the DB stays
authoritative — a cache failure never bypasses auth, it falls back to
the DB, and a cache HIT still answers when the DB is down.

Failure directions (D6 matrix):

- Redis outage / broken cache impl → DB (``AuthCacheProvider`` never
  raises; the service guards its own calls too, so ANY injected cache
  implementation degrades to the DB — ``auth.subject_state_cache_unavailable``);
- corrupt cache value (not one of the three states) → treated as a miss
  and rewritten (``permissions._cached_permissions`` parse-fail
  precedent — recorded deviation: middleware returned garbage verbatim);
- DB failure on a miss → propagates (the state cannot be invented).
"""

from __future__ import annotations

from app.identity.cache_provider import AuthCacheProvider
from app.identity.repositories import UserRepository
from app.shared.logging import get_logger

logger = get_logger(__name__)

_USER_STATE_TTL_SECONDS = 60

_VALID_STATES = frozenset({"active", "unknown", "disabled"})


class SubjectStateService:
    """``get(user_id)`` → ``"active" | "unknown" | "disabled"``.

    Single point of truth for subject state (SPEC-0028 ``web_auth`` /
    ``get_current_user`` consumers land in TASK-0169/0175).
    """

    def __init__(self, user_repository: UserRepository, cache: AuthCacheProvider) -> None:
        self._users = user_repository
        self._cache = cache

    def get(self, user_id: str) -> str:
        key = f"auth:user:{user_id}"
        cached = self._cache_get(key)
        if cached is not None and cached in _VALID_STATES:
            return cached  # hit — no DB, no write-back (middleware parity)
        state = self._users.get_auth_state(user_id)  # DB authoritative
        self._cache_set(key, state)
        return state

    def _cache_get(self, key: str) -> str | None:
        try:
            return self._cache.get(key)
        except Exception:
            logger.warning(
                "subject-state cache unavailable — reading the DB",
                extra={
                    "action": "auth.subject_state_cache_unavailable",
                    "entity_type": "subject_state",
                    "cache_key": key,
                },
            )
            return None

    def _cache_set(self, key: str, state: str) -> None:
        try:
            self._cache.set(key, state, _USER_STATE_TTL_SECONDS)
        except Exception:
            logger.warning(
                "subject-state cache write unavailable — DB stays authoritative",
                extra={
                    "action": "auth.subject_state_cache_unavailable",
                    "entity_type": "subject_state",
                    "cache_key": key,
                },
            )
