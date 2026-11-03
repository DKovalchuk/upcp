"""web_auth — FastAPI-native default-deny for the web surface (SPEC-0028 S28.2, TASK-0169).

Route-dependency replacement for ``AuthMiddleware``'s JWT branch: Bearer
extract → ``TokenService.verify_access_token`` → logout denylist →
``SubjectStateService`` liveness → ``request.state`` principal. The 401
shapes and the subject-rejection observability (metric + structured
warning + span attributes) are byte-parity with the middleware — including
the historical ``"auth middleware: rejecting valid JWT"`` warning text,
kept verbatim so existing log/alert queries stay valid across the TASK-0170
retirement. The middleware stays mounted until TASK-0170 (both surfaces
must carry dependencies before the string guard is removed).

S28.2 performance rule (documented deviation from the middleware): the
WHOLE synchronous pipeline (signature verify, denylist Redis read,
subject-state cache/DB read) runs in a single ``run_in_threadpool`` call —
the middleware ran the same I/O inline and blocked the event loop
(SPEC-0028 finding 6). ``request.state`` is set on the event loop AFTER
the await; rejection observability also runs on the loop so span
attributes land on the request's active span.

Test seams preserved by construction: session-less ``SubjectStateService``
(lazy ``SessionLocal``) and the denylist's lazy ``get_redis_client``;
``Depends(_get_token_service)`` keeps the existing
``app.dependency_overrides[_get_token_service]`` secret seam. This module
must never import ``app.api.registry`` (composition root imports it).
"""

from typing import Literal

from fastapi import Depends, HTTPException, Request, status
from starlette.concurrency import run_in_threadpool

from app.identity.auth import _get_subject_state_service, _get_token_service
from app.identity.denylist import is_token_denied, note_denied_token
from app.identity.token_service import TokenService
from app.shared.config import get_settings
from app.shared.logging import get_logger
from app.shared.metrics import auth_subject_rejections_total

logger = get_logger(__name__)

_DenyReason = Literal["invalid", "denied", "subject"]


class _Denied(Exception):
    """Internal rejection signal raised inside the threadpool pipeline."""

    def __init__(self, reason: _DenyReason, subject: str = "", state: str = "") -> None:
        super().__init__(reason)
        self.reason = reason
        self.subject = subject
        self.state = state


def _verify_and_authorize(token: str, token_service: TokenService) -> dict[str, object]:
    """Sync pipeline (runs in the threadpool): verify → denylist → liveness.

    Order matches ``AuthMiddleware.dispatch`` byte-for-byte; a rejection
    raises :class:`_Denied` and is mapped to the historical 401 on the
    event loop.
    """
    try:
        payload = token_service.verify_access_token(token)
    except ValueError:
        raise _Denied("invalid") from None

    # SPEC-0027 §3.3: logout-denylisted token (finding 3) — fail-open inside
    if is_token_denied(token):
        raise _Denied("denied")

    # SPEC-0027 §3.2: valid signature ≠ live account (finding 2)
    subject = str(payload["sub"])
    state = _get_subject_state_service().get(subject)
    if state != "active":
        raise _Denied("subject", subject, state)
    return payload


def _reject_subject(user_id: str, reason: str) -> None:
    """Structured denial (metric + warning + span attrs) — copy of the
    middleware's ``_reject_subject``, observability only (the caller
    raises the standard 401)."""
    auth_subject_rejections_total.labels(reason=reason).inc()
    logger.warning(
        "auth middleware: rejecting valid JWT — subject=%s state=%s",
        user_id,
        reason,
        extra={"action": "auth.subject_rejected", "entity_type": "jwt_subject"},
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
                    "upcp.auth.subject_rejected": True,
                    "upcp.auth.subject_state": reason,
                    "upcp.auth.sub": user_id,
                }
            )


async def web_auth(
    request: Request,
    token_service: TokenService = Depends(_get_token_service),
) -> None:
    """Deny every web-surface request without a live JWT (SPEC-0028 D2/AC1).

    Blanket-attached via ``include_surfaces`` (``dependencies=[Depends(web_auth)]``)
    so a new web route is denied by default; raises the historical 401
    shapes (missing / invalid / denylisted / dead subject), all with
    ``WWW-Authenticate: Bearer``.
    """
    if get_settings().disable_auth:
        return  # hermetic kill switch (AC10, documented test-only — main.py parity)

    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = auth_header[7:]

    try:
        payload = await run_in_threadpool(_verify_and_authorize, token, token_service)
    except _Denied as denied:
        if denied.reason == "denied":
            note_denied_token(token)
        elif denied.reason == "subject":
            _reject_subject(denied.subject, denied.state)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    request.state.user_id = payload["sub"]
    request.state.auth_type = "user"
    request.state.api_surface = "web"
