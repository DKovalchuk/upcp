"""Agent API endpoints — create, list, detail, tokens, metrics, detail tabs.

TASK-0068, TASK-0099 (B5, B6)
"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.delivery.service import AgentActivityService
from app.identity.agents import Agent, AgentToken
from app.identity.auth import get_current_user
from app.identity.dependencies import CurrentUser
from app.identity.permissions import require_permission
from app.quality.service import EvidenceService, ReviewRoundService
from app.shared.config import get_settings
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
    # AC7 (SPEC-0028 D1): optional explicit expiry — must be in the future;
    # when omitted, issuance falls back to settings.agent_token_ttl_days.
    expires_at: datetime | None = None


# ── Endpoints ─────────────────────────────────────────────────────


@router.post(
    "/agents",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("manage", "agent"))],
)
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
    # commit before respond — teardown runs after the response, and the
    # client chains create→POST .../tokens immediately (404 "Agent not
    # found" in gate 3296; same class as TASK-0140 create→use races)
    db.commit()

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
    agent = _require_agent(db, agent_id)

    tokens = db.query(AgentToken).filter_by(agent_id=agent_id).all()

    # ── Metrics (B5) ──
    # Cross-context reads go through delivery's public AgentActivityService
    # (TASK-0176 / AGENTS §5) — identity never queries delivery models.
    activity = AgentActivityService(db)
    completed = activity.count_claims(agent_id, state="completed")
    expired = activity.count_claims(agent_id, state="expired")
    total_finished = completed + expired
    success_rate = round(completed / total_finished * 100, 1) if total_finished > 0 else None

    active_claim = activity.get_active_claim(agent_id)

    current_task_id: str | None = None
    current_task_title: str | None = None
    current_progress: int | None = None
    last_heartbeat_at: str | None = None
    is_stale = False

    if active_claim is not None:
        current_task_id = active_claim.task_id
        tasks = activity.list_tasks_by_ids([active_claim.task_id])
        task = tasks[0] if tasks else None
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
            latest_hb = activity.get_latest_heartbeat(active_claim.id)
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
        last_activity_at = activity.last_claimed_at(agent_id)
        if last_activity_at is not None:
            offline_cutoff = datetime.now(UTC) - timedelta(hours=1)
            agent_status = "idle" if last_activity_at > offline_cutoff else "offline"
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


@router.post(
    "/agents/{agent_id}/tokens",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("manage", "agent"))],
)
def create_agent_token(
    agent_id: str,
    body: AgentTokenCreate,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> dict[str, object]:
    """Issue an agent API key — always with an expiry (AC7, TASK-0170).

    Default TTL comes from ``UPCP_AGENT_TOKEN_TTL_DAYS`` (90); an explicit
    ``expires_at`` is honored but must be in the future (422 otherwise).
    Keys issued before this rule (``expires_at IS NULL``) are grandfathered
    — the verifier only rejects non-null past expiries — until revoked.
    """
    _require_agent(db, agent_id, user.user_id)

    raw_token = secrets.token_urlsafe(48)
    token_hash = _hash_token(raw_token)

    now = datetime.now(UTC)
    if body.expires_at is None:
        expires_at = now + timedelta(days=get_settings().agent_token_ttl_days)
    else:
        expires_at = (
            body.expires_at
            if body.expires_at.tzinfo is not None
            else body.expires_at.replace(tzinfo=UTC)
        )
        if expires_at <= now:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="expires_at must be in the future",
            )

    record = AgentToken(
        id=new_id(),
        agent_id=agent_id,
        token_hash=token_hash,
        name=body.name,
        scopes=body.scopes,
        expires_at=expires_at,
    )
    db.add(record)
    db.flush()
    # commit before respond — the client uses the fresh token immediately;
    # the auth path looks the row up in a different session (TASK-0143)
    db.commit()

    return {
        "id": record.id,
        "name": record.name,
        "token": raw_token,  # Shown once, never stored
        "scopes": record.scopes,
        "expires_at": expires_at.isoformat(),
        "created_at": record.created_at.isoformat(),
    }


@router.post(
    "/agent-tokens/{token_id}/revoke",
    dependencies=[Depends(require_permission("manage", "agent"))],
)
def revoke_agent_token(
    token_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> dict[str, object]:
    from datetime import UTC, datetime

    record = db.query(AgentToken).filter_by(id=token_id).first()
    if record is None:
        raise HTTPException(status_code=404, detail="Token not found")

    # Enforce ownership: only agent owner or admin can revoke
    _require_agent(db, record.agent_id, user.user_id)

    record.revoked_at = datetime.now(UTC)
    db.flush()
    # commit before respond — a reused token must be rejected on the very
    # next request, not after the teardown (TASK-0143)
    db.commit()

    return {"ok": True}


# ── Agent detail endpoints (B6) ──────────────────────────────────


@router.get("/agents/{agent_id}/claims")
def agent_claims(
    agent_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_session),
) -> dict[str, object]:
    _require_agent(db, agent_id)

    activity = AgentActivityService(db)
    claims = activity.list_claims(agent_id, limit=100)

    # Batch-load tasks to avoid N+1
    task_ids = [c.task_id for c in claims if c.task_id]
    tasks = activity.list_tasks_by_ids(task_ids)
    task_map = {t.id: t for t in tasks}

    items = []
    for c in claims:
        task = task_map.get(c.task_id)
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
    _require_agent(db, agent_id)

    events = AgentActivityService(db).list_inbox_events(agent_id, limit=100)

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
    _require_agent(db, agent_id)

    items = EvidenceService(db).list_by_creator(agent_id, limit=100)

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
    _require_agent(db, agent_id)

    items = ReviewRoundService(db).list_by_reviewer(agent_id, limit=100)

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
    _require_agent(db, agent_id)

    items = AgentActivityService(db).list_clarifications(agent_id, limit=100)

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

    Read-only access (GET) is allowed for any authenticated user.
    Write access (token create/revoke) requires ownership or admin role.
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
                detail="Not authorized to manage this agent",
            )

    return agent
