"""Agent authentication — verify X-Agent-Token header.

TASK-0175 (SPEC-0029 §3.5): verification lives in ``AgentTokenService``
— this dependency maps the service's rejection reasons onto the
historical 401 detail strings byte-for-byte and nothing else: no direct
row queries, no local token hashing (the single sha256 of the raw token
lives with the service, AC5). The service stamps ``last_used_at`` with
its commit-before-response invariant (TASK-0174 AC4) through the
request-scoped repositories.
"""

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.identity.agent_token_service import AgentTokenRejection, AgentTokenService
from app.identity.dependencies import CurrentAgent
from app.identity.repositories import AgentRepository, AgentTokenRepository
from app.shared.database import get_session

# Historical 401 details, keyed by the service's rejection reason
# (byte-parity with the pre-TASK-0175 dependency behavior).
_REJECTION_DETAILS: dict[str, str] = {
    "unknown": "Invalid agent token",
    "revoked": "Agent token has been revoked",
    "expired": "Agent token has expired",
    "agent_inactive": "Agent not found or inactive",
}


def _get_agent_token_service(db: Session = Depends(get_session)) -> AgentTokenService:
    """Request-scoped service: repositories bound to the request session,
    so the committed ``last_used_at`` touch lands before the response."""
    return AgentTokenService(AgentTokenRepository(db), AgentRepository(db))


def get_current_agent(
    x_agent_token: str | None = Header(None, alias="X-Agent-Token"),
    agent_token_service: AgentTokenService = Depends(_get_agent_token_service),
) -> CurrentAgent:
    """Validate agent token and return current agent. Raises 401 on failure."""
    if x_agent_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing agent token",
        )

    result = agent_token_service.verify_detailed(x_agent_token)
    if isinstance(result, AgentTokenRejection):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_REJECTION_DETAILS[result.reason],
        )

    return CurrentAgent(
        agent_id=result.agent_id,
        name=result.name,
        scopes=result.scopes,
    )
