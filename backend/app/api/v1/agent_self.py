"""Agent self-service endpoints — me, inbox, playbook.

TASK-0075
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.delivery.models import AgentInboxEvent, ClarificationRequest, TaskClaim
from app.identity.agent_auth import get_current_agent, require_agent_scope
from app.identity.agents import Agent
from app.identity.dependencies import CurrentAgent
from app.shared.database import get_session

router = APIRouter(tags=["agent-self"], dependencies=[Depends(require_agent_scope("agent:self"))])

_DEFAULT_PLAYBOOK = """# Agent Playbook

## How to Work with Tasks

1. **Claim a task**: Use `POST /tasks/{id}/claim` to claim a ready task.
2. **Send heartbeats**: Every 30-60 seconds, send progress via `POST /tasks/{id}/heartbeat`.
3. **Ask questions**: If blocked, use `POST /tasks/{id}/clarifications` to request clarification.
4. **Submit for review**: When done, attach evidence and submit via `POST /tasks/{id}/submit-review`.

## Status Flow

```
backlog → ready → claimed → in_progress → done
```

## Rules

- Always send heartbeats to avoid stale detection.
- Release tasks you cannot complete.
- Provide evidence for every completed task.
"""


@router.get(
    "/agent/me",
    summary="Get agent profile",
    description="Return the current agent's profile, scopes, and inbox count.",
    responses={404: {"description": "Agent not found"}},
)
def agent_me(
    agent: CurrentAgent = Depends(get_current_agent),
    db: Session = Depends(get_session),
) -> dict[str, object]:
    """Return agent profile, scopes, and inbox count."""
    db_agent = db.query(Agent).filter_by(id=agent.agent_id).first()
    if db_agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    active_claims = db.query(TaskClaim).filter_by(agent_id=agent.agent_id, state="active").count()
    open_clarifications = (
        db.query(ClarificationRequest)
        .filter(
            ClarificationRequest.author_id == agent.agent_id,
            ClarificationRequest.author_type == "agent",
            ClarificationRequest.state == "open",
        )
        .count()
    )
    inbox_count = active_claims + open_clarifications

    return {
        "id": db_agent.id,
        "name": db_agent.name,
        "description": db_agent.description,
        "is_active": db_agent.is_active,
        "scopes": agent.scopes,
        "inbox_count": inbox_count,
        "created_at": db_agent.created_at.isoformat(),
    }


@router.get(
    "/agent/inbox",
    summary="Get agent inbox",
    description="Return pending events and notifications for the current agent.",
)
def agent_inbox(
    agent: CurrentAgent = Depends(get_current_agent),
    db: Session = Depends(get_session),
    unread_only: bool = False,
) -> dict[str, list[dict[str, object]]]:
    """Return agent events (inbox) from AgentInboxEvent table."""
    query = db.query(AgentInboxEvent).filter_by(agent_id=agent.agent_id)
    if unread_only:
        query = query.filter_by(is_read=False)
    events = query.order_by(AgentInboxEvent.created_at.desc()).limit(50).all()

    return {
        "events": [
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


@router.get(
    "/agent/playbook",
    summary="Get agent playbook",
    description="Return the agent playbook with instructions on task handling and workflows.",
)
def agent_playbook(
    agent: CurrentAgent = Depends(get_current_agent),
) -> dict[str, str]:
    """Return the agent playbook content."""
    return {"content": _DEFAULT_PLAYBOOK}
