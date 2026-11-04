"""RBAC permission gates — require_permission dependency (SPEC-0027 §3.1).

Phase A scope: admin-dangerous mutations only (projects CRUD, agent
management). DDD: identity context — routes in other contexts consume
this gate via FastAPI ``Depends`` only (no internal imports).

FastAPI runs route-level ``dependencies=[...]`` *before* the endpoint
handler, so a denied request answers without touching resource lookup —
the exact behavior the finding-1 xfail test encodes.

Fail-closed checks, in order:

1. ``UPCP_DISABLE_AUTH`` → gate inert (the auth stack is off — hermetic
   test mode; mirrors the surface auth dependencies short-circuiting
   then, TASK-0170).
2. No identity on the request (auth dependency did not run) → 401.
3. Unknown or disabled subject → 401 (a valid signature does not imply
   a live account — defense in depth under finding 2 / TASK-0146).
4. ``is_superuser`` → allowed: setup/seeder admins hold no RoleBinding
   by design. A backfill-to-Owner would also Owner-ify the deliberately
   permission-less seeder members and destroy the authz negative
   control — bypass instead (deviation recorded in SPEC-0027 §3.1).
5. No role grants the permission → 403 (structured log + metric +
   span attributes).

Permission pairs are cached (TTL 60 s) through ``AuthCacheProvider``
with the DB as fallback when the cache is unavailable; the granted-pairs
query lives in ``PermissionRepository`` (SPEC-0029 §3.5 / TASK-0175 —
this module keeps zero direct data access beyond the gate's byte-parity
subject check).
"""

from __future__ import annotations

import json
from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.identity.cache_provider import AuthCacheProvider
from app.identity.models import User
from app.identity.repositories import PermissionRepository
from app.shared.config import get_settings
from app.shared.database import get_session
from app.shared.logging import get_logger
from app.shared.metrics import rbac_denials_total

logger = get_logger(__name__)

_CACHE_TTL_SECONDS = 60


def _record_denial_span(action: str, resource: str) -> None:
    """Attach denial attributes to the active span (lazy otel import).

    opentelemetry is optional (mirrors main.py tracing guard): without
    the package the import fails here and denial logging continues.
    """
    try:
        from opentelemetry import trace
    except ImportError:  # pragma: no cover
        return
    span = trace.get_current_span()
    if span.is_recording():
        span.set_attributes(
            {
                "upcp.rbac.denied": True,
                "upcp.rbac.action": action,
                "upcp.rbac.resource": resource,
            }
        )


def _resolve_user_permissions(db: Session, user_id: str) -> set[tuple[str, str]]:
    """Cache-aside permission pairs (SPEC-0029 §3.5 / TASK-0175).

    Read through ``AuthCacheProvider`` (never raises — an outage degrades
    to a cache miss); unparseable or malformed payloads degrade to the
    granted-pairs query in ``PermissionRepository`` (defensive parsing,
    the ``subject_state`` corrupt-value precedent). Fail-closed either
    way: a cache problem can only cost a query, never open the gate.
    """
    cache = AuthCacheProvider()
    key = f"rbac:user_perms:{user_id}"
    raw = cache.get(key)
    parsed: object = None
    if raw is not None:
        try:
            parsed = json.loads(raw)
        except (TypeError, ValueError):
            parsed = None
    if isinstance(parsed, list) and all(
        isinstance(pair, list) and len(pair) == 2 for pair in parsed
    ):
        return {(pair[0], pair[1]) for pair in parsed}

    pairs = PermissionRepository(db).granted_pairs(user_id)
    cache.set(key, json.dumps(pairs), _CACHE_TTL_SECONDS)
    return {(action, resource) for action, resource in pairs}


def require_permission(action: str, resource: str) -> Callable[..., None]:
    """Route gate: the authenticated user must hold ``action:resource``.

    See the module docstring for the fail-closed check order (401s before
    the permission lookup, superuser bypass before role resolution).
    """

    def _gate(
        request: Request,
        db: Session = Depends(get_session),
    ) -> None:
        if get_settings().disable_auth:
            return  # auth stack off (hermetic mode) — gates are inert

        user_id = getattr(request.state, "user_id", None)
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user = db.get(User, str(user_id))
        if user is None or not user.is_active:
            logger.warning(
                "rbac gate: rejecting %s mutation by subject=%s (%s)",
                f"{action}:{resource}",
                user_id,
                "no such user" if user is None else "user disabled",
                extra={"action": f"{action}:{resource}", "entity_type": "rbac_gate"},
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if user.is_superuser:
            return  # superusers hold full access without RoleBindings

        if (action, resource) in _resolve_user_permissions(db, user.id):
            return

        rbac_denials_total.labels(action=action, resource=resource).inc()
        logger.warning(
            "permission denied: user=%s needs %s:%s",
            user.id,
            action,
            resource,
            extra={"action": f"{action}:{resource}", "entity_type": "rbac_gate"},
        )
        _record_denial_span(action, resource)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    return _gate
