"""Agent API endpoints — create, list, detail, tokens, metrics, detail tabs.

TASK-0068, TASK-0099 (B5, B6)
"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.delivery.models import (
    AgentInboxEvent,
    ClarificationRequest,
    Task,
    TaskClaim,
)
from app.identity.agents import Agent, AgentToken
from app.identity.auth import get_current_user
from app.identity.dependencies import CurrentUser
from app.quality.models import Evidence, ReviewRound
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
    agent = _require_agent(db, agent_id, user.user_id)

    tokens = db.query(AgentToken).filter_by(agent_id=agent_id).all()

    # ── Metrics (B5) ──
    completed = (
        db.query(TaskClaim)
        .filter(TaskClaim.agent_id == agent_id, TaskClaim.state == "completed")
        .count()
    )
    expired = (
        db.query(TaskClaim)
        .filter(TaskClaim.agent_id == agent_id, TaskClaim.state == "expired")
        .count()
    )
    total_finished = completed + expired
    success_rate = round(completed / total_finished * 100, 1) if total_finished > 0 else None

    active_claim = (
        db.query(TaskClaim)
        .filter(TaskClaim.agent_id == agent_id, TaskClaim.state == "active")
        .first()
    )

    current_task_id: str | None = None
    current_task_title: str | None = None
    current_progress: int | None = None
    last_heartbeat_at: str | None = None
    is_stale = False

    if active_claim is not None:
        current_task_id = active_claim.task_id
        task = db.get(Task, active_claim.task_id)
        if task is not None:
            current_task_title = task.title

        if active_claim.last_heartbeat_at is not None:
            last_heartbeat_at = active_claim.last_heartbeat_at.isoformat()
            # Handle both naive (SQLite) and aware (PostgreSQL) datetimes
            hb_dt = active_claim.last_heartbeat_at
            now_utc = datetime.now(UTC)
            if hb_dt.tzinfo is None:
                now_utc = now_utc.replace(tzinfo=None)
            stale_cutoff = now_utc - timedelta(minutes=5)
            is_stale = hb_dt < stale_cutoff

            # Get latest heartbeat for progress
            from app.delivery.models import Heartbeat

            latest_hb = (
                db.query(Heartbeat)
                .filter(Heartbeat.claim_id == active_claim.id)
                .order_by(Heartbeat.created_at.desc())
                .first()
            )
            if latest_hb is not None:
                current_progress = latest_hb.progress_percent
        else:
            # Never heartbeated — check if stale from claim time
            claimed_dt = active_claim.claimed_at
            now_utc = datetime.now(UTC)
            if claimed_dt.tzinfo is None:
                now_utc = now_utc.replace(tzinfo=None)
            stale_cutoff = now_utc - timedelta(minutes=5)
            is_stale = claimed_dt < stale_cutoff

    # Status calculation
    if active_claim is not None and not is_stale:
        agent_status = "working"
    elif active_claim is not None and is_stale:
        agent_status = "stale"
    else:
        # Check last activity
        last_activity = (
            db.query(TaskClaim.claimed_at)
            .filter(TaskClaim.agent_id == agent_id)
            .order_by(TaskClaim.claimed_at.desc())
            .first()
        )
        if last_activity is not None and last_activity[0] is not None:
            offline_cutoff = datetime.now(UTC) - timedelta(hours=1)
            agent_status = "idle" if last_activity[0] > offline_cutoff else "offline"
        else:
            agent_status = "idle"

    return {
        "id": agent.id,
        "name": agent.name,
        "description": agent.description,
        "is_active": agent.is_active,
        "created_by": agent.created_by,
        "created_at": agent.created_at.isoformat(),
        "metrics": {
            "tasks_completed": completed,
            "tasks_failed": expired,
            "success_rate": success_rate,
            "current_task_id": current_task_id,
            "current_task_title": current_task_title,
            "current_progress_percent": current_progress,
            "last_heartbeat_at": last_heartbeat_at,
            "is_stale": is_stale,
            "status": agent_status,
        },
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


# ── Agent detail endpoints (B6) ──────────────────────────────────


@router.get("/agents/{agent_id}/claims")
def agent_claims(
    agent_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> dict[str, object]:
    _require_agent(db, agent_id, user.user_id)

    claims = (
        db.query(TaskClaim)
        .filter(TaskClaim.agent_id == agent_id)
        .order_by(TaskClaim.claimed_at.desc())
        .limit(100)
        .all()
    )

    items = []
    for c in claims:
        task = db.get(Task, c.task_id)
        items.append(
            {
                "id": c.id,
                "task_id": c.task_id,
                "task_title": task.title if task else None,
                "state": c.state,
                "claimed_at": c.claimed_at.isoformat() if c.claimed_at else None,
                "released_at": c.released_at.isoformat() if c.released_at else None,
                "last_heartbeat_at": c.last_heartbeat_at.isoformat()
                if c.last_heartbeat_at
                else None,
            }
        )

    return {"items": items}


@router.get("/agents/{agent_id}/activity")
def agent_activity(
    agent_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> dict[str, object]:
    _require_agent(db, agent_id, user.user_id)

    events = (
        db.query(AgentInboxEvent)
        .filter(AgentInboxEvent.agent_id == agent_id)
        .order_by(AgentInboxEvent.created_at.desc())
        .limit(100)
        .all()
    )

    return {
        "items": [
            {
                "id": e.id,
                "event_type": e.event_type,
                "task_id": e.task_id,
                "message": e.message,
                "is_read": e.is_read,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in events
        ]
    }


@router.get("/agents/{agent_id}/evidence")
def agent_evidence(
    agent_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> dict[str, object]:
    _require_agent(db, agent_id, user.user_id)

    items = (
        db.query(Evidence)
        .filter(Evidence.created_by_id == agent_id)
        .order_by(Evidence.created_at.desc())
        .limit(100)
        .all()
    )

    return {
        "items": [
            {
                "id": e.id,
                "task_id": e.task_id,
                "type": e.type,
                "title": e.title,
                "verification_state": e.verification_state,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in items
        ]
    }


@router.get("/agents/{agent_id}/reviews")
def agent_reviews(
    agent_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> dict[str, object]:
    _require_agent(db, agent_id, user.user_id)

    items = (
        db.query(ReviewRound)
        .filter(ReviewRound.reviewer_id == agent_id)
        .order_by(ReviewRound.created_at.desc())
        .limit(100)
        .all()
    )

    return {
        "items": [
            {
                "id": r.id,
                "task_id": r.task_id,
                "state": r.state,
                "verdict": r.verdict,
                "confidence": r.confidence,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in items
        ]
    }


@router.get("/agents/{agent_id}/clarifications")
def agent_clarifications(
    agent_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> dict[str, object]:
    _require_agent(db, agent_id, user.user_id)

    items = (
        db.query(ClarificationRequest)
        .filter(ClarificationRequest.author_id == agent_id)
        .order_by(ClarificationRequest.created_at.desc())
        .limit(100)
        .all()
    )

    return {
        "items": [
            {
                "id": c.id,
                "task_id": c.task_id,
                "question": c.question,
                "state": c.state,
                "blocking": c.blocking,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in items
        ]
    }


def _require_agent(db: Session, agent_id: str, user_id: str | None = None) -> Agent:
    """Return agent if found; enforce ownership when *user_id* is given.

    A non-admin user may only access agents they created.
    Superusers bypass the ownership check.
    """
    agent = db.query(Agent).filter_by(id=agent_id).first()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    if user_id is not None:
        from app.identity.models import User

        user = db.query(User).filter_by(id=user_id).first()
        is_admin = user is not None and user.is_superuser
        if agent.created_by != user_id and not is_admin:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to access this agent",
            )

    return agent
