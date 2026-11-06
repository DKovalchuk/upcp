"""Access-token denylist — logout revocation (SPEC-0027 §3.3 / TASK-0147).

Finding 3: logout revoked only the refresh token — the access JWT kept
working on every route until exp. Logout now writes
``auth:deny:{sha256(raw)}`` with TTL = exp − now (self-expiring, no
cleanup job); :func:`is_token_denied` is checked in ``web_auth``
(web-surface routes) and ``get_current_user`` (/auth/*).

Redis outage fails OPEN on read (availability over a ≤15-min
revocation window — AC5, rate-limiter precedent) with a structured
warning; write failures degrade the same way (logout still revokes the
refresh token and commits the audit). The Redis client is imported
lazily so tests can patch ``app.shared.redis.get_redis_client`` (test
seam per the lazy-session precedent).
"""

import hashlib

from app.shared.logging import get_logger
from app.shared.metrics import auth_token_denials_total

logger = get_logger(__name__)


def _fingerprint(token: str) -> str:
    """SHA-256 of the raw token — key material (payloads carry no jti)."""
    return hashlib.sha256(token.encode()).hexdigest()


def deny_access_token(token: str, ttl_seconds: int) -> None:
    """Denylist the access token for its remaining lifetime (best-effort)."""
    fingerprint = _fingerprint(token)
    try:
        from app.shared.redis import get_redis_client  # lazy — test seam

        get_redis_client().set(f"auth:deny:{fingerprint}", "1", ex=ttl_seconds)
    except Exception:
        logger.warning(
            "denylist write failed — access token stays valid until exp",
            extra={"action": "auth.denylist_write_failed", "entity_type": "access_token"},
        )


def is_token_denied(token: str) -> bool:
    """True when the token was revoked by logout; Redis down → allow (AC5)."""
    try:
        from app.shared.redis import get_redis_client  # lazy — test seam

        return get_redis_client().get(f"auth:deny:{_fingerprint(token)}") is not None
    except Exception:
        logger.warning(
            "denylist unavailable — allowing request (fail-open, AC5)",
            extra={"action": "auth.denylist_unavailable", "entity_type": "access_token"},
        )
        return False


def note_denied_token(token: str) -> None:
    """Structured denial: metric + warning (reason=logout, ≠ expiry) + span."""
    auth_token_denials_total.labels(reason="logout").inc()
    fingerprint = _fingerprint(token)
    logger.warning(
        "auth: access token denylisted by logout — rejecting",
        extra={"action": "auth.token_denied", "entity_type": "access_token"},
    )
    try:
        from opentelemetry import trace
    except ImportError:
        trace = None  # type: ignore[assignment]  # opentelemetry optional
    if trace is not None:
        span = trace.get_current_span()
        if span.is_recording():
            span.set_attributes(
                {
                    "upcp.auth.token_denied": True,
                    "upcp.auth.deny_reason": "logout",
                    "upcp.auth.token_fingerprint": fingerprint[:16],
                }
            )
