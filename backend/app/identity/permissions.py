"""RBAC permission gates — require_permission / require_role /
require_superuser dependencies (SPEC-0027 §3.1, SPEC-0028 §3.5 / D4).

Phase A: admin-dangerous mutations (projects CRUD, agent management).
Phase B (TASK-0172): every dangerous mutation in the task inventory gets
``require_permission``; role-semantic admin routes get ``require_role``
(none yet — see the task decision table); superuser-only ops endpoints
get ``require_superuser`` (``/internal/reaper/tick``). DDD: identity
context — routes in other contexts consume these gates via FastAPI
``Depends`` only (no internal imports; the public-surface whitelist in
``tests/test_context_boundaries.py`` documents that contract).

FastAPI runs route-level ``dependencies=[...]`` *before* the endpoint
handler (after the surface auth blanket), so a denied request answers
without touching resource lookup — the exact behavior the finding-1
xfail test encodes.

Fail-closed checks, in order:

1. ``UPCP_DISABLE_AUTH`` → gate inert (the auth stack is off — hermetic
   test mode; mirrors the surface auth dependencies short-circuiting
   then, TASK-0170).
2. No identity on the request (auth dependency did not run) → 401.
3. Unknown or disabled subject → 401 (a valid signature does not imply
   a live account — defense in depth under finding 2 / TASK-0146).
4. ``is_superuser=True`` → allowed: setup/seeder admins hold no RoleBinding
   by design. A backfill-to-Owner would also Owner-ify the deliberately
   permission-less seeder members and destroy the authz negative
   control — bypass instead (deviation recorded in SPEC-0027 §3.1).
5. No role grants the permission (or the role binding does not match,
   or the subject is not a superuser where required) → 403 (structured
   log + metric + span attributes).

Permission pairs are cached (TTL 60 s) through ``AuthCacheProvider``
with the DB as fallback when the cache is unavailable; the granted-pairs
query lives in ``PermissionRepository`` (SPEC-0029 §3.5 / TASK-0175 —
this module keeps zero direct data access beyond the gate's byte-parity
subject check; role bindings resolve through
``PermissionRepository.holds_role``, SPEC-0029 D1 «presentation does
zero data access»).
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


def _live_user_or_401(request: Request, db: Session, label: str) -> User:
    """Fail-closed identity prelude shared by the three gate factories.

    Order pinned by SPEC-0027 §3.1 (MUST NOT change): no principal on the
    request (auth dependency did not run) → 401; unknown or inactive
    subject → 401 (a valid signature does not imply a live account —
    defense in depth under finding 2 / TASK-0146). The caller checks the
    ``UPCP_DISABLE_AUTH`` inert branch first, then this runs, then the
    caller's bypass/lookup (superuser bypass stays BEFORE role resolution).
    """
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
            label,
            user_id,
            "no such user" if user is None else "user disabled",
            extra={"action": label, "entity_type": "rbac_gate"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


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

        user = _live_user_or_401(request, db, f"{action}:{resource}")

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


def require_role(role: str) -> Callable[..., None]:
    """Route gate: the authenticated user must hold the named ``Role``.

    Same fail-closed order as ``require_permission`` (module docstring,
    SPEC-0027 §3.1 — 401s first, superuser bypass BEFORE role resolution
    for AC9 parity): ``UPCP_DISABLE_AUTH`` → inert; no principal → 401;
    unknown/disabled subject → 401; ``is_superuser`` → allowed; no
    RoleBinding naming ``role`` → **403** ``{"detail": "Insufficient role"}``.

    Role-semantic admin routes (D4: roles as semantics, not permission
    pairs). No production route applies it yet — TASK-0172's inventory
    found none that is role-semantic in practice; the factory ships
    unit-pinned for the first such route (see the task's decision table).
    """

    def _gate(
        request: Request,
        db: Session = Depends(get_session),
    ) -> None:
        if get_settings().disable_auth:
            return  # auth stack off (hermetic mode) — gates are inert

        user = _live_user_or_401(request, db, f"role:{role}")

        if user.is_superuser:
            return  # parity with require_permission (AC9)

        if PermissionRepository(db).holds_role(str(user.id), role):
            return

        rbac_denials_total.labels(action="role", resource=role).inc()
        logger.warning(
            "role denied: user=%s needs role=%s",
            user.id,
            role,
            extra={"action": f"role:{role}", "entity_type": "rbac_gate"},
        )
        _record_denial_span("role", role)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient role",
        )

    return _gate


def require_superuser() -> Callable[..., None]:
    """Route gate: only ``is_superuser`` accounts pass — no role resolution.

    Same fail-closed order (SPEC-0027 §3.1): ``UPCP_DISABLE_AUTH`` →
    inert; no principal → 401; unknown/disabled subject → 401; else
    **403** ``{"detail": "Superuser required"}`` for everyone who is not
    a superuser (bindings irrelevant — a superuser holds no binding by
    design, a bound Owner still fails). Applied to ``POST
    /api/v1/internal/reaper/tick`` (TASK-0172 inventory evidence: internal
    ops endpoint, no non-admin HTTP caller anywhere).
    """

    def _gate(
        request: Request,
        db: Session = Depends(get_session),
    ) -> None:
        if get_settings().disable_auth:
            return  # auth stack off (hermetic mode) — gates are inert

        user = _live_user_or_401(request, db, "superuser:route")

        if user.is_superuser:
            return

        rbac_denials_total.labels(action="superuser", resource="route").inc()
        logger.warning(
            "superuser required: user=%s hit a superuser-only route",
            user.id,
            extra={"action": "superuser:route", "entity_type": "rbac_gate"},
        )
        _record_denial_span("superuser", "route")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser required",
        )

    return _gate
