"""Task workflow endpoints — claim, release, heartbeat, progress.

TASK-0074
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.delivery.workflow import WorkflowService
from app.identity.agent_auth import get_current_agent
from app.identity.dependencies import CurrentAgent
from app.shared.database import get_session
from app.shared.errors import Conflict, NotFound

router = APIRouter(tags=["workflow"])


# ── Schemas ──


class ClaimRequest(BaseModel):
    context_snapshot: str | None = None


class HeartbeatRequest(BaseModel):
    progress_percent: int = Field(ge=0, le=100)
    current_step: str = Field(min_length=1, max_length=255)
    next_step: str = Field(min_length=1, max_length=255)
    blockers: str | None = None
    eta: str | None = None


class ProgressRequest(BaseModel):
    progress_percent: int = Field(ge=0, le=100)


# ── Endpoints ──


@router.post("/tasks/{task_id}/claim", status_code=201)
def claim_task(
    task_id: str,
    body: ClaimRequest | None = None,
    agent: CurrentAgent = Depends(get_current_agent),
    session: Session = Depends(get_session),
) -> dict[str, str | None]:
    svc = WorkflowService(session)
    try:
        claim = svc.claim(
            task_id,
            agent_id=agent.agent_id,
            context_snapshot=body.context_snapshot if body else None,
        )
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e)) from None
    except Conflict as e:
        raise HTTPException(status_code=409, detail=str(e)) from None

    return {
        "id": claim.id,
        "task_id": claim.task_id,
        "agent_id": claim.agent_id,
        "state": claim.state,
        "claimed_at": claim.claimed_at.isoformat() if claim.claimed_at else None,
    }


@router.post("/tasks/{task_id}/release")
def release_task(
    task_id: str,
    agent: CurrentAgent = Depends(get_current_agent),
    session: Session = Depends(get_session),
) -> dict[str, bool]:
    svc = WorkflowService(session)
    try:
        svc.release(task_id, agent_id=agent.agent_id)
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e)) from None
    except Conflict as e:
        raise HTTPException(status_code=409, detail=str(e)) from None

    return {"ok": True}


@router.post("/tasks/{task_id}/heartbeat")
def heartbeat_task(
    task_id: str,
    body: HeartbeatRequest,
    agent: CurrentAgent = Depends(get_current_agent),
    session: Session = Depends(get_session),
) -> dict[str, bool]:
    svc = WorkflowService(session)
    try:
        svc.heartbeat(
            task_id,
            agent_id=agent.agent_id,
            progress_percent=body.progress_percent,
            current_step=body.current_step,
            next_step=body.next_step,
            blockers=body.blockers,
            eta=body.eta,
        )
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e)) from None
    except Conflict as e:
        raise HTTPException(status_code=409, detail=str(e)) from None

    return {"ok": True}


@router.post("/tasks/{task_id}/progress")
def progress_task(
    task_id: str,
    body: ProgressRequest,
    agent: CurrentAgent = Depends(get_current_agent),
    session: Session = Depends(get_session),
) -> dict[str, bool]:
    svc = WorkflowService(session)
    try:
        svc.progress(
            task_id,
            agent_id=agent.agent_id,
            progress_percent=body.progress_percent,
        )
    except NotFound as e:
        raise HTTPException(status_code=404, detail=str(e)) from None
    except Conflict as e:
        raise HTTPException(status_code=409, detail=str(e)) from None

    return {"ok": True}
