"""Agent API endpoints — create, list, detail, tokens."""

import hashlib
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.identity.agents import Agent, AgentToken
from app.identity.auth import get_current_user
from app.identity.dependencies import CurrentUser
from app.shared.database import get_session
from app.shared.text import new_id

router = APIRouter(tags=["agents"])


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


# ── Schemas ───────────────────────────────────────────────────────


class AgentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None


class AgentTokenCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    scopes: list[str] | None = None


# ── Endpoints ─────────────────────────────────────────────────────


@router.post("/agents", status_code=status.HTTP_201_CREATED)
def create_agent(
    body: AgentCreate,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> dict[str, object]:
    agent = Agent(
        name=body.name,
        description=body.description,
        created_by=user.user_id,
    )
    db.add(agent)
    db.flush()

    return {
        "id": agent.id,
        "name": agent.name,
        "description": agent.description,
        "is_active": agent.is_active,
        "created_by": agent.created_by,
        "created_at": agent.created_at.isoformat(),
    }


@router.get("/agents")
def list_agents(
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session),
    offset: int = 0,
    limit: int = 20,
) -> dict[str, object]:
    query = db.query(Agent)
    total = query.count()
    items = query.offset(offset).limit(limit).all()

    return {
        "items": [
            {
                "id": a.id,
                "name": a.name,
                "description": a.description,
                "is_active": a.is_active,
                "created_at": a.created_at.isoformat(),
            }
            for a in items
        ],
        "total": total,
        "offset": offset,
        "limit": limit,
    }


@router.get("/agents/{agent_id}")
def get_agent(
    agent_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> dict[str, object]:
    agent = db.query(Agent).filter_by(id=agent_id).first()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    tokens = db.query(AgentToken).filter_by(agent_id=agent_id).all()

    return {
        "id": agent.id,
        "name": agent.name,
        "description": agent.description,
        "is_active": agent.is_active,
        "created_by": agent.created_by,
        "created_at": agent.created_at.isoformat(),
        "tokens": [
            {
                "id": t.id,
                "name": t.name,
                "scopes": t.scopes,
                "revoked_at": t.revoked_at.isoformat() if t.revoked_at else None,
                "last_used_at": t.last_used_at.isoformat() if t.last_used_at else None,
                "created_at": t.created_at.isoformat(),
            }
            for t in tokens
        ],
    }


@router.post("/agents/{agent_id}/tokens", status_code=status.HTTP_201_CREATED)
def create_agent_token(
    agent_id: str,
    body: AgentTokenCreate,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> dict[str, object]:
    agent = db.query(Agent).filter_by(id=agent_id).first()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    raw_token = secrets.token_urlsafe(48)
    token_hash = _hash_token(raw_token)

    record = AgentToken(
        id=new_id(),
        agent_id=agent_id,
        token_hash=token_hash,
        name=body.name,
        scopes=body.scopes,
    )
    db.add(record)
    db.flush()

    return {
        "id": record.id,
        "name": record.name,
        "token": raw_token,  # Shown once, never stored
        "scopes": record.scopes,
        "created_at": record.created_at.isoformat(),
    }


@router.post("/agent-tokens/{token_id}/revoke")
def revoke_agent_token(
    token_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> dict[str, object]:
    from datetime import UTC, datetime

    record = db.query(AgentToken).filter_by(id=token_id).first()
    if record is None:
        raise HTTPException(status_code=404, detail="Token not found")

    record.revoked_at = datetime.now(UTC)
    db.flush()

    return {"ok": True}
