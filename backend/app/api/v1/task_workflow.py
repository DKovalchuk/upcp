"""Task workflow endpoints — claim, release, heartbeat, progress, reads.

TASK-0074
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.delivery.models import ClarificationRequest, Heartbeat, Task, TaskClaim
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


@router.post(
    "/tasks/{task_id}/claim",
    status_code=201,
    summary="Claim a task",
    description="Claim a ready task for an agent. Only one active claim per task is allowed.",
    responses={
        404: {"description": "Task not found"},
        409: {"description": "Task already claimed"},
    },
)
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


@router.post(
    "/tasks/{task_id}/release",
    summary="Release a task claim",
    description="Release an active claim on a task, making it available for other agents.",
    responses={
        404: {"description": "Task not found"},
        409: {"description": "No active claim to release"},
    },
)
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


@router.post(
    "/tasks/{task_id}/heartbeat",
    summary="Send a task heartbeat",
    description="Send progress update and heartbeat for an active claim. Must be sent every 30-60 seconds.",
    responses={
        404: {"description": "Task not found"},
        409: {"description": "No active claim for this task"},
    },
)
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


@router.post(
    "/tasks/{task_id}/progress",
    summary="Update task progress",
    description="Update the progress percentage for an active task claim.",
    responses={
        404: {"description": "Task not found"},
        409: {"description": "No active claim for this task"},
    },
)
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


# ── GET endpoints (read-back) ──


def _require_task(session: Session, task_id: str) -> None:
    """Raise 404 if task does not exist."""
    task = session.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"task '{task_id}' not found")


@router.get(
    "/tasks/{task_id}/claims",
    summary="List claims for a task",
    description="List all claim records for a task including active and released claims.",
    responses={404: {"description": "Task not found"}},
)
def list_claims(
    task_id: str,
    session: Session = Depends(get_session),
) -> dict[str, object]:
    _require_task(session, task_id)

    stmt = (
        select(TaskClaim).where(TaskClaim.task_id == task_id).order_by(TaskClaim.claimed_at.desc())
    )
    rows = session.execute(stmt).scalars().all()

    items = [
        {
            "id": r.id,
            "task_id": r.task_id,
            "agent_id": r.agent_id,
            "state": r.state,
            "claimed_at": r.claimed_at.isoformat() if r.claimed_at else None,
            "released_at": r.released_at.isoformat() if r.released_at else None,
            "last_heartbeat_at": (r.last_heartbeat_at.isoformat() if r.last_heartbeat_at else None),
            "context_snapshot": r.context_snapshot,
        }
        for r in rows
    ]
    return {"items": items}


@router.get(
    "/tasks/{task_id}/heartbeats",
    summary="List heartbeats for a task",
    description="List all heartbeat records for a task across all claims.",
    responses={404: {"description": "Task not found"}},
)
def list_heartbeats(
    task_id: str,
    session: Session = Depends(get_session),
) -> dict[str, object]:
    _require_task(session, task_id)

    stmt = (
        select(Heartbeat)
        .join(TaskClaim, TaskClaim.id == Heartbeat.claim_id)
        .where(TaskClaim.task_id == task_id)
        .order_by(Heartbeat.created_at.desc())
    )
    rows = session.execute(stmt).scalars().all()

    items = [
        {
            "id": r.id,
            "claim_id": r.claim_id,
            "progress_percent": r.progress_percent,
            "current_step": r.current_step,
            "next_step": r.next_step,
            "blockers": r.blockers,
            "eta": r.eta,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
    return {"items": items}


@router.get(
    "/tasks/{task_id}/clarifications",
    summary="List clarifications for a task",
    description="List all clarification requests for a task including open and answered ones.",
    responses={404: {"description": "Task not found"}},
)
def list_clarifications(
    task_id: str,
    session: Session = Depends(get_session),
) -> dict[str, object]:
    _require_task(session, task_id)

    stmt = (
        select(ClarificationRequest)
        .where(ClarificationRequest.task_id == task_id)
        .order_by(ClarificationRequest.created_at.desc())
    )
    rows = session.execute(stmt).scalars().all()

    items = [
        {
            "id": r.id,
            "task_id": r.task_id,
            "author_type": r.author_type,
            "author_id": r.author_id,
            "question": r.question,
            "context": r.context,
            "blocking": r.blocking,
            "state": r.state,
            "answer": r.answer,
            "answered_by": r.answered_by,
            "answered_at": r.answered_at.isoformat() if r.answered_at else None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
    return {"items": items}
