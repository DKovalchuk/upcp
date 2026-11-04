"""Agent authentication — X-Agent-Token blanket, principal, scope gate.

TASK-0170 (SPEC-0028 S28.3): three FastAPI dependencies over the single
``AgentTokenService`` verification path (TASK-0175/0174) — no direct row
queries, no local hashing (one sha256, AC5):

- ``get_current_agent`` — handler-level dependency: ALWAYS enforces the
  four canonical 401 details (it does not consult ``disable_auth`` —
  pinned by ``test_identity_agent_dependency.test_missing_header_rejected``);
- ``agent_auth`` — the AGENT-surface blanket (attached through
  ``identity.dependencies.get_agent_auth`` in ``app.api.registry``):
  short-circuits under ``disable_auth`` (parity with the retired
  middleware, which was only mounted when auth was enabled), otherwise
  resolves through the same path. Exactly ONE verification runs per
  request: whoever resolves first stores the principal on
  ``request.state`` and the others reuse it (FastAPI's dependency cache
  covers the shared ``agent_auth``/``get_current_agent`` callables; the
  ``request.state`` memo covers direct calls — verified by
  ``test_blanket_and_handler_share_one_verification``);
- ``require_agent_scope(scope)`` — factory for router-level scope gates
  (AC6). ``scopes is None`` → ALLOW (grandfathered legacy keys issued
  before enforcement existed); list → membership; dict → truthy key;
  unknown shape → deny (fail-closed). Denial emits the dedicated
  ``upcp_agent_scope_denials_total`` metric, a structured warning
  (``action=auth.scope_denied``) and span attrs, then answers
  403 ``Insufficient scope``. The gate depends on ``Depends(agent_auth)``
  (cache-shared with the blanket), NOT on ``Depends(get_current_agent)``:
  FastAPI solves sub-dependencies eagerly (0.139.2 ``solve_dependencies``),
  so a handler-level sub-dep would re-enforce under ``disable_auth`` and
  break hermetic bare-router test sites (``create_mcp_router``).

On success the dependency sets ``request.state.agent_id``,
``agent_name``, ``auth_type="agent"`` and ``api_surface="agent"``
(parity with the retired middleware + SPEC-0028 S28.3 for TASK-0171/0173).
Raw header values are never logged (AC11).
"""

from collections.abc import Awaitable, Callable

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.identity.agent_token_service import AgentTokenRejection, AgentTokenService
from app.identity.dependencies import CurrentAgent
from app.identity.repositories import AgentRepository, AgentTokenRepository
from app.shared.config import get_settings
from app.shared.database import get_session
from app.shared.logging import get_logger
from app.shared.metrics import agent_scope_denials_total

logger = get_logger(__name__)

# Historical 401 details, keyed by the service's rejection reason
# (byte-parity with the pre-TASK-0175 dependency behavior).
_REJECTION_DETAILS: dict[str, str] = {
    "unknown": "Invalid agent token",
    "revoked": "Agent token has been revoked",
    "expired": "Agent token has expired",
    "agent_inactive": "Agent not found or inactive",
}
_MISSING_DETAIL = "Missing agent token"


def _get_agent_token_service(db: Session = Depends(get_session)) -> AgentTokenService:
    """Request-scoped service: repositories bound to the request session,
    so the committed ``last_used_at`` touch lands before the response."""
    return AgentTokenService(AgentTokenRepository(db), AgentRepository(db))


def _verify_principal(raw_token: str | None, service: AgentTokenService) -> CurrentAgent:
    """Resolve a raw header value into a principal, or raise the canonical 401."""
    if raw_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_MISSING_DETAIL,
        )
    result = service.verify_detailed(raw_token)
    if isinstance(result, AgentTokenRejection):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_REJECTION_DETAILS[result.reason],
        )
    return CurrentAgent(agent_id=result.agent_id, name=result.name, scopes=result.scopes)


def _memo(request: Request) -> CurrentAgent | None:
    principal = getattr(request.state, "current_agent", None)
    return principal if isinstance(principal, CurrentAgent) else None


def _store(request: Request, agent: CurrentAgent) -> CurrentAgent:
    """Write the principal + middleware-parity state (TASK-0171 contract)."""
    request.state.current_agent = agent
    request.state.agent_id = agent.agent_id
    request.state.agent_name = agent.name
    request.state.auth_type = "agent"
    request.state.api_surface = "agent"
    return agent


def get_current_agent(
    request: Request,
    x_agent_token: str | None = Header(None, alias="X-Agent-Token"),
    agent_token_service: AgentTokenService = Depends(_get_agent_token_service),
) -> CurrentAgent:
    """Validate agent token and return current agent. Raises 401 on failure.

    ALWAYS enforces — the hermetic ``disable_auth`` flag is the blanket's
    concern only (existing consumers and their 401 pins stay unchanged);
    a principal already resolved for this request is reused (memo).
    """
    existing = _memo(request)
    if existing is not None:
        return existing
    return _store(request, _verify_principal(x_agent_token, agent_token_service))


async def agent_auth(
    request: Request,
    x_agent_token: str | None = Header(None, alias="X-Agent-Token"),
    agent_token_service: AgentTokenService = Depends(_get_agent_token_service),
) -> None:
    """AGENT-surface blanket — default deny for every route of the surface.

    Attached via ``include_surfaces`` (``dependencies=[Depends(agent_auth)]``
    through the public ``get_agent_auth`` accessor). Under ``disable_auth``
    it skips (parity: the retired ``AuthMiddleware`` was not mounted in
    hermetic mode); otherwise the verification pipeline runs in the
    threadpool (no event-loop blocking — S28.2 rule) and ``request.state``
    is written on the loop after the await.
    """
    if get_settings().disable_auth:
        return  # hermetic kill switch (AC10, documented test-only)
    if _memo(request) is not None:
        return
    agent = await run_in_threadpool(_verify_principal, x_agent_token, agent_token_service)
    _store(request, agent)


def _scope_allows(scopes: object, scope: str) -> bool:
    """Scope policy for the shape actually stored in ``agent_token.scopes``.

    - ``None`` → ALLOW: grandfathered legacy keys (enforcement did not
      exist before AC6 — documented in TASK-0170 evidence);
    - ``list`` → membership: the production write path
      (``AgentTokenCreate.scopes: list[str]``);
    - ``dict`` → truthy key: legacy/flag-shaped rows (test fixtures,
      pre-list writes) must carry the scope with a truthy value;
    - anything else → DENY (fail-closed, defensive — no write path
      produces it).
    """
    if scopes is None:
        return True
    if isinstance(scopes, list):
        return scope in scopes
    if isinstance(scopes, dict):
        return bool(scopes.get(scope))
    return False


def _observe_scope_denial(agent_id: str, scope: str) -> None:
    """Structured denial (metric + warning + span attrs) — permissions.py style."""
    agent_scope_denials_total.labels(scope=scope).inc()
    logger.warning(
        "agent scope denied: agent=%s needs %s",
        agent_id,
        scope,
        extra={"action": "auth.scope_denied", "entity_type": "agent_scope"},
    )
    try:
        from opentelemetry import trace
    except ImportError:  # pragma: no cover — opentelemetry optional
        trace = None  # type: ignore[assignment]
    if trace is not None:
        span = trace.get_current_span()
        if span.is_recording():
            span.set_attributes(
                {
                    "upcp.auth.scope_denied": True,
                    "upcp.auth.scope": scope,
                    "upcp.auth.sub": agent_id,
                }
            )


def require_agent_scope(scope: str) -> Callable[..., Awaitable[None]]:
    """Router-level gate: the authenticated agent must hold ``scope`` (AC6).

    Marking is native (``APIRouter(dependencies=[Depends(require_agent_scope(...))])``);
    the gate sub-depends on the ``agent_auth`` blanket (FastAPI dependency
    cache → single verification per request) and is inert under
    ``disable_auth`` — same hermetic policy as the RBAC gates
    (``permissions.require_permission``).
    """

    async def _gate(
        request: Request,
        _auth: None = Depends(agent_auth),
    ) -> None:
        if get_settings().disable_auth:
            return  # auth stack off (hermetic mode) — gates are inert
        agent = _memo(request)
        if agent is None:  # pragma: no cover — agent_auth resolved above
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=_MISSING_DETAIL,
            )
        if _scope_allows(agent.scopes, scope):
            return
        _observe_scope_denial(agent.agent_id, scope)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient scope",
        )

    return _gate
