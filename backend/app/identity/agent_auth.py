"""Agent authentication — verify X-Agent-Token header."""

import hashlib
from datetime import UTC, datetime

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.identity.agents import Agent, AgentToken
from app.identity.dependencies import CurrentAgent
from app.shared.database import get_session


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def get_current_agent(
    x_agent_token: str | None = Header(None, alias="X-Agent-Token"),
    db: Session = Depends(get_session),
) -> CurrentAgent:
    """Validate agent token and return current agent. Raises 401 on failure."""
    if x_agent_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing agent token",
        )

    token_hash = _hash_token(x_agent_token)
    record = db.query(AgentToken).filter_by(token_hash=token_hash).first()

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid agent token",
        )

    if record.revoked_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Agent token has been revoked",
        )

    if record.expires_at is not None and record.expires_at < datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Agent token has expired",
        )

    agent = db.query(Agent).filter_by(id=record.agent_id).first()
    if agent is None or not agent.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Agent not found or inactive",
        )

    # Update last_used_at
    record.last_used_at = datetime.now(UTC)
    db.flush()

    return CurrentAgent(
        agent_id=agent.id,
        name=agent.name,
        scopes=record.scopes,
    )
