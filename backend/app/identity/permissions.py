"""RBAC permission gates — require_permission dependency (SPEC-0027 §3.1).

Phase A scope: admin-dangerous mutations only (projects CRUD, agent
management). DDD: identity context — routes in other contexts consume
this gate via FastAPI ``Depends`` only (no internal imports).

FastAPI runs route-level ``dependencies=[...]`` *before* the endpoint
handler, so a denied request answers without touching resource lookup —
the exact behavior the finding-1 xfail test encodes.

Fail-closed checks, in order:

1. ``UPCP_DISABLE_AUTH`` → gate inert (the auth stack is off — hermetic
   test mode; mirrors main.py not mounting AuthMiddleware then).
2. No identity on the request (middleware missing) → 401.
3. Unknown or disabled subject → 401 (a valid signature does not imply
   a live account — defense in depth under finding 2 / TASK-0146).
4. ``is_superuser`` → allowed: setup/seeder admins hold no RoleBinding
   by design. A backfill-to-Owner would also Owner-ify the deliberately
   permission-less seeder members and destroy the authz negative
   control — bypass instead (deviation recorded in SPEC-0027 §3.1).
5. No role grants the permission → 403 (structured log + metric +
   span attributes).

Permission pairs are cached in Redis (TTL 60 s) with the DB as
fallback when Redis is unavailable.
"""

from __future__ import annotations

import json
from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.identity.models import User
from app.identity.rbac import Permission, RoleBinding, RolePermission
from app.shared.config import get_settings
from app.shared.database import get_session
from app.shared.logging import get_logger
from app.shared.metrics import rbac_denials_total
from app.shared.redis import get_redis_client

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


def _query_permissions(db: Session, user_id: str) -> list[list[str]]:
    """Distinct (action, resource) pairs granted via the user's bindings."""
    rows = (
        db.query(Permission.action, Permission.resource)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(RoleBinding, RoleBinding.role_id == RolePermission.role_id)
        .filter(RoleBinding.user_id == user_id)
        .distinct()
        .all()
    )
    return [[action, resource] for action, resource in rows]


def _cached_permissions(user_id: str) -> list[list[str]] | None:
    """Redis read. Returns None on miss, parse failure or Redis outage."""
    try:
        raw = get_redis_client().get(f"rbac:user_perms:{user_id}")
    except Exception:
        return None  # Redis down → caller falls back to the DB
    if raw is None:
        return None
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return None
    return parsed if isinstance(parsed, list) else None


def _cache_permissions(user_id: str, perms: list[list[str]]) -> None:
    """Best-effort cache write — the DB stays authoritative."""
    try:
        get_redis_client().set(
            f"rbac:user_perms:{user_id}", json.dumps(perms), ex=_CACHE_TTL_SECONDS
        )
    except Exception:
        return


def _resolve_user_permissions(db: Session, user_id: str) -> set[tuple[str, str]]:
    cached = _cached_permissions(user_id)
    if cached is not None:
        return {(pair[0], pair[1]) for pair in cached if len(pair) == 2}
    perms = _query_permissions(db, user_id)
    _cache_permissions(user_id, perms)
    return {(action, resource) for action, resource in perms}


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
