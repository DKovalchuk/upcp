from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.delivery.service import TaskService
from app.quality.schemas import (
    AcceptanceCriterionCreate,
    AcceptanceCriterionUpdate,
    DoDItemCreate,
    DoDItemUpdate,
    EvidenceCreate,
    EvidenceRejectRequest,
    EvidenceVerifyRequest,
    QualityStatsResponse,
    ReviewFindingCreate,
    ReviewRoundCreate,
    ReviewVerdictRequest,
)
from app.quality.service import (
    AcceptanceCriterionService,
    DoDItemService,
    EvidenceService,
    QualityStatsService,
    ReviewGateService,
    ReviewRoundService,
)
from app.shared.config import get_settings
from app.shared.database import get_session
from app.shared.errors import Conflict, NotFound, ValidationError
from app.shared.pagination import PaginationParams, pagination_dependency

router = APIRouter(tags=["quality"])


@router.post(
    "/tasks/{task_id}/acceptance-criteria",
    status_code=201,
    summary="Create an acceptance criterion",
    description="Create a new acceptance criterion for a task.",
    responses={422: {"description": "Validation error"}},
)
def create_ac(
    task_id: str, body: AcceptanceCriterionCreate, session: Session = Depends(get_session)
) -> dict[str, str]:  # noqa: B008
    svc = AcceptanceCriterionService(session)
    ac = svc.create(task_id=task_id, description=body.description)
    return {"id": ac.id, "task_id": ac.task_id, "description": ac.description, "status": ac.status}


@router.get(
    "/acceptance-criteria/{ac_id}",
    summary="Get an acceptance criterion",
    description="Retrieve a single acceptance criterion by its identifier.",
    responses={404: {"description": "Acceptance criterion not found"}},
)
def get_ac(ac_id: str, session: Session = Depends(get_session)) -> dict[str, str]:  # noqa: B008
    ac = AcceptanceCriterionService(session).get(ac_id)
    return {"id": ac.id, "task_id": ac.task_id, "description": ac.description, "status": ac.status}


@router.patch(
    "/acceptance-criteria/{ac_id}",
    summary="Update an acceptance criterion",
    description="Partially update an acceptance criterion.",
    responses={
        404: {"description": "Acceptance criterion not found"},
        422: {"description": "Validation error"},
    },
)
def update_ac(
    ac_id: str, body: AcceptanceCriterionUpdate, session: Session = Depends(get_session)
) -> dict[str, str]:  # noqa: B008
    ac = AcceptanceCriterionService(session).update(ac_id, **body.model_dump(exclude_unset=True))
    return {"id": ac.id, "task_id": ac.task_id, "description": ac.description, "status": ac.status}


@router.delete(
    "/acceptance-criteria/{ac_id}",
    status_code=204,
    summary="Delete an acceptance criterion",
    description="Delete an acceptance criterion by its identifier.",
    responses={404: {"description": "Acceptance criterion not found"}},
)
def delete_ac(ac_id: str, session: Session = Depends(get_session)) -> None:  # noqa: B008
    AcceptanceCriterionService(session).delete(ac_id)


@router.get(
    "/tasks/{task_id}/acceptance-criteria",
    summary="List acceptance criteria for a task",
    description="List all acceptance criteria associated with a task.",
)
def list_acs(
    task_id: str,
    pagination: PaginationParams = Depends(pagination_dependency),
    session: Session = Depends(get_session),
) -> dict[str, object]:  # noqa: B008
    items, total = AcceptanceCriterionService(session).list_by_task(
        task_id, offset=pagination.offset, limit=pagination.limit
    )
    return {
        "items": [
            {"id": a.id, "task_id": a.task_id, "description": a.description, "status": a.status}
            for a in items
        ],
        "total": total,
        "offset": pagination.offset,
        "limit": pagination.limit,
    }


@router.post(
    "/tasks/{task_id}/dod-items",
    status_code=201,
    summary="Create a DoD item",
    description="Create a new Definition of Done item for a task.",
    responses={422: {"description": "Validation error"}},
)
def create_dod(
    task_id: str, body: DoDItemCreate, session: Session = Depends(get_session)
) -> dict[str, str]:  # noqa: B008
    svc = DoDItemService(session)
    item = svc.create(task_id=task_id, name=body.name)
    return {"id": item.id, "task_id": item.task_id, "name": item.name, "status": item.status}


@router.get(
    "/dod-items/{item_id}",
    summary="Get a DoD item",
    description="Retrieve a single DoD item by its identifier.",
    responses={404: {"description": "DoD item not found"}},
)
def get_dod(item_id: str, session: Session = Depends(get_session)) -> dict[str, str]:  # noqa: B008
    item = DoDItemService(session).get(item_id)
    return {"id": item.id, "task_id": item.task_id, "name": item.name, "status": item.status}


@router.patch(
    "/dod-items/{item_id}",
    summary="Update a DoD item",
    description="Partially update a DoD item.",
    responses={
        404: {"description": "DoD item not found"},
        422: {"description": "Validation error"},
    },
)
def update_dod(
    item_id: str, body: DoDItemUpdate, session: Session = Depends(get_session)
) -> dict[str, str]:  # noqa: B008
    item = DoDItemService(session).update(item_id, **body.model_dump(exclude_unset=True))
    return {"id": item.id, "task_id": item.task_id, "name": item.name, "status": item.status}


@router.delete(
    "/dod-items/{item_id}",
    status_code=204,
    summary="Delete a DoD item",
    description="Delete a DoD item by its identifier.",
    responses={404: {"description": "DoD item not found"}},
)
def delete_dod(item_id: str, session: Session = Depends(get_session)) -> None:  # noqa: B008
    DoDItemService(session).delete(item_id)


@router.get(
    "/tasks/{task_id}/dod-items",
    summary="List DoD items for a task",
    description="List all Definition of Done items associated with a task.",
)
def list_dods(
    task_id: str,
    pagination: PaginationParams = Depends(pagination_dependency),
    session: Session = Depends(get_session),
) -> dict[str, object]:  # noqa: B008
    items, total = DoDItemService(session).list_by_task(
        task_id, offset=pagination.offset, limit=pagination.limit
    )
    return {
        "items": [
            {"id": i.id, "task_id": i.task_id, "name": i.name, "status": i.status} for i in items
        ],
        "total": total,
        "offset": pagination.offset,
        "limit": pagination.limit,
    }


@router.post(
    "/tasks/{task_id}/complete",
    summary="Mark a task as complete",
    description="Mark a task as complete, updating its status to done.",
    responses={404: {"description": "Task not found"}},
)
def complete_task(task_id: str, session: Session = Depends(get_session)) -> dict[str, str]:  # noqa: B008
    task = TaskService(session).complete(task_id)
    return {"id": task.id, "status": task.status}


@router.post(
    "/tasks/{task_id}/submit-review",
    status_code=201,
    summary="Submit a task for review",
    description="Submit a completed task for agent or human review.",
    responses={
        404: {"description": "Task not found"},
        400: {"description": "Task not eligible for review"},
    },
)
def submit_task_for_review(
    task_id: str,
    session: Session = Depends(get_session),
) -> dict[str, str | int | None]:  # noqa: B008
    svc = ReviewGateService(session)
    try:
        rr = svc.submit_for_review(
            task_id,
            requested_by_type="agent",
            requested_by_id="agent",
        )
    except NotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    return _review_round_dict(rr)


@router.get(
    "/projects/{project_id}/quality/stats",
    response_model=QualityStatsResponse,
    summary="Get quality statistics",
    description="Retrieve quality statistics for a project including task counts, AC pass rates, and DoD status.",
    responses={404: {"description": "Project not found"}},
)
def get_quality_stats(
    project_id: str, session: Session = Depends(get_session)
) -> QualityStatsResponse:  # noqa: B008
    svc = QualityStatsService(session)
    raw = svc.get_quality_stats(project_id)
    return QualityStatsResponse(
        total_tasks=raw["total_tasks"],
        tasks_with_ac=raw["tasks_with_ac"],
        total_ac=raw["total_ac"],
        passed_ac=raw["passed_ac"],
        total_dod=raw["total_dod"],
        passed_dod=raw["passed_dod"],
        pass_rate=raw["pass_rate"],
    )


# ── Evidence endpoints ──


def _evidence_dict(e: Any) -> dict[str, str | int | None]:
    return {
        "id": e.id,
        "task_id": e.task_id,
        "dod_item_id": e.dod_item_id,
        "type": e.type,
        "title": e.title,
        "description": e.description,
        "url": e.url,
        "content_snippet": e.content_snippet,
        "artifact_ref": e.artifact_ref,
        "file_name": e.file_name,
        "file_size": e.file_size,
        "content_type": e.content_type,
        "created_by_type": e.created_by_type,
        "created_by_id": e.created_by_id,
        "verification_state": e.verification_state,
        "verified_by_type": e.verified_by_type,
        "verified_by_id": e.verified_by_id,
        "verified_at": e.verified_at.isoformat() if e.verified_at else None,
        "created_at": e.created_at.isoformat() if e.created_at else None,
    }


@router.get(
    "/tasks/{task_id}/evidence",
    summary="List evidence for a task",
    description="List all evidence items attached to a task.",
)
def list_evidence(
    task_id: str,
    pagination: PaginationParams = Depends(pagination_dependency),
    session: Session = Depends(get_session),
) -> dict[str, object]:  # noqa: B008
    items, total = EvidenceService(session).list_by_task(
        task_id, offset=pagination.offset, limit=pagination.limit
    )
    return {
        "items": [_evidence_dict(e) for e in items],
        "total": total,
        "offset": pagination.offset,
        "limit": pagination.limit,
    }


@router.post(
    "/tasks/{task_id}/evidence",
    status_code=201,
    summary="Create evidence",
    description="Attach a new evidence item to a task for DoD verification.",
    responses={422: {"description": "Validation error"}},
)
def create_evidence(
    task_id: str, body: EvidenceCreate, session: Session = Depends(get_session)
) -> dict[str, str | int | None]:  # noqa: B008
    svc = EvidenceService(session)
    e = svc.create(
        task_id=task_id,
        type=body.type,
        title=body.title,
        description=body.description,
        url=body.url,
        content_snippet=body.content_snippet,
        artifact_ref=body.artifact_ref,
        dod_item_id=body.dod_item_id,
        created_by_type=body.created_by_type,
        created_by_id=body.created_by_id,
    )
    return _evidence_dict(e)


@router.post(
    "/evidence/{evidence_id}/agent-verify",
    summary="Verify evidence (agent)",
    description="Agent verifies an evidence item as valid.",
    responses={
        404: {"description": "Evidence not found"},
        409: {"description": "Evidence already verified"},
    },
)
def agent_verify_evidence(
    evidence_id: str,
    body: EvidenceVerifyRequest | None = None,
    session: Session = Depends(get_session),
) -> dict[str, str | int | None]:  # noqa: B008
    svc = EvidenceService(session)
    try:
        e = svc.verify(evidence_id, verified_by_type="agent", verified_by_id="agent")
    except NotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
    except Conflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    return _evidence_dict(e)


@router.post(
    "/evidence/{evidence_id}/human-accept",
    summary="Accept evidence (human)",
    description="Human reviewer accepts an evidence item as valid.",
    responses={
        404: {"description": "Evidence not found"},
        409: {"description": "Evidence already accepted"},
    },
)
def human_accept_evidence(
    evidence_id: str,
    session: Session = Depends(get_session),
) -> dict[str, str | int | None]:  # noqa: B008
    svc = EvidenceService(session)
    try:
        e = svc.accept(evidence_id, verified_by_type="human", verified_by_id="human")
    except NotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
    except Conflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    return _evidence_dict(e)


@router.post(
    "/evidence/{evidence_id}/reject",
    summary="Reject evidence",
    description="Reject an evidence item as invalid.",
    responses={
        404: {"description": "Evidence not found"},
        409: {"description": "Evidence already rejected"},
    },
)
def reject_evidence(
    evidence_id: str,
    body: EvidenceRejectRequest | None = None,
    session: Session = Depends(get_session),
) -> dict[str, str | int | None]:  # noqa: B008
    svc = EvidenceService(session)
    try:
        e = svc.reject(evidence_id, verified_by_type="human", verified_by_id="human")
    except NotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
    except Conflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    return _evidence_dict(e)


@router.post(
    "/tasks/{task_id}/evidence/upload",
    status_code=201,
    summary="Upload file as evidence",
    description="Upload a file attachment as evidence for a task.",
    responses={422: {"description": "Validation error"}},
)
async def upload_evidence_file(
    task_id: str,
    file: UploadFile = File(...),
    title: str = Form(...),
    created_by_type: str = Form(default="human"),
    created_by_id: str = Form(default="default"),
    dod_item_id: str | None = Form(default=None),
    session: Session = Depends(get_session),
) -> dict[str, str | int | None]:  # noqa: B008
    settings = get_settings()
    svc = EvidenceService(session)
    try:
        e = svc.upload_file(
            task_id=task_id,
            file=file,
            title=title,
            created_by_type=created_by_type,
            created_by_id=created_by_id,
            storage_dir=settings.upload_dir,
            max_size_bytes=settings.max_upload_size_bytes,
            dod_item_id=dod_item_id,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
    except NotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
    return _evidence_dict(e)


@router.get(
    "/evidence/{evidence_id}/download",
    summary="Download evidence file",
    description="Download the file attached to an evidence item.",
    responses={404: {"description": "Evidence not found or no file"}},
)
def download_evidence_file(
    evidence_id: str,
    session: Session = Depends(get_session),
) -> FileResponse:  # noqa: B008
    svc = EvidenceService(session)
    try:
        path, ct = svc.get_file(evidence_id)
    except NotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
    except ValidationError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
    return FileResponse(path=path, media_type=ct, filename=path.name)


# ── Review Round endpoints ──


def _review_round_dict(rr: Any) -> dict[str, str | int | None]:
    return {
        "id": rr.id,
        "task_id": rr.task_id,
        "requested_by_type": rr.requested_by_type,
        "requested_by_id": rr.requested_by_id,
        "reviewer_type": rr.reviewer_type,
        "reviewer_id": rr.reviewer_id,
        "state": rr.state,
        "verdict": rr.verdict,
        "confidence": rr.confidence,
        "summary": rr.summary,
        "created_at": rr.created_at.isoformat() if rr.created_at else None,
        "started_at": rr.started_at.isoformat() if rr.started_at else None,
        "completed_at": rr.completed_at.isoformat() if rr.completed_at else None,
    }


def _review_finding_dict(f: Any) -> dict[str, str | None]:
    return {
        "id": f.id,
        "review_round_id": f.review_round_id,
        "severity": f.severity,
        "category": f.category,
        "message": f.message,
        "evidence_id": f.evidence_id,
        "dod_item_id": f.dod_item_id,
        "suggestion": f.suggestion,
        "created_at": f.created_at.isoformat() if f.created_at else None,
    }


@router.get(
    "/tasks/{task_id}/review-rounds",
    summary="List review rounds for a task",
    description="List all review rounds associated with a task.",
)
def list_review_rounds(
    task_id: str,
    pagination: PaginationParams = Depends(pagination_dependency),
    session: Session = Depends(get_session),
) -> dict[str, object]:  # noqa: B008
    svc = ReviewRoundService(session)
    items, total = svc.list_by_task(task_id, offset=pagination.offset, limit=pagination.limit)
    return {
        "items": [_review_round_dict(rr) for rr in items],
        "total": total,
        "offset": pagination.offset,
        "limit": pagination.limit,
    }


@router.post(
    "/tasks/{task_id}/review-rounds",
    status_code=201,
    summary="Create a review round",
    description="Create a new review round for a task with a specified reviewer.",
    responses={404: {"description": "Task not found"}},
)
def create_review_round(
    task_id: str,
    body: ReviewRoundCreate,
    session: Session = Depends(get_session),
) -> dict[str, str | int | None]:  # noqa: B008
    svc = ReviewRoundService(session)
    try:
        rr = svc.create(
            task_id=task_id,
            requested_by_type="human",
            requested_by_id="human",
            reviewer_type=body.reviewer_type,
            reviewer_id=body.reviewer_id,
        )
    except NotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
    return _review_round_dict(rr)


@router.post(
    "/review-rounds/{round_id}/start",
    summary="Start a review round",
    description="Start a review round, transitioning it from pending to in_progress.",
    responses={
        404: {"description": "Review round not found"},
        409: {"description": "Review round not in valid state"},
    },
)
def start_review_round(
    round_id: str, session: Session = Depends(get_session)
) -> dict[str, str | int | None]:  # noqa: B008
    svc = ReviewRoundService(session)
    try:
        rr = svc.start(round_id)
    except NotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
    except Conflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    return _review_round_dict(rr)


@router.post(
    "/review-rounds/{round_id}/findings",
    status_code=201,
    summary="Add a review finding",
    description="Add a finding to a review round with severity and category.",
    responses={
        404: {"description": "Review round not found"},
        409: {"description": "Review round not in valid state"},
    },
)
def create_review_finding(
    round_id: str,
    body: ReviewFindingCreate,
    session: Session = Depends(get_session),
) -> dict[str, str | None]:  # noqa: B008
    svc = ReviewRoundService(session)
    try:
        f = svc.add_finding(
            round_id,
            severity=body.severity,
            category=body.category,
            message=body.message,
            evidence_id=body.evidence_id,
            dod_item_id=body.dod_item_id,
            suggestion=body.suggestion,
        )
    except NotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
    except Conflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    return _review_finding_dict(f)


@router.post(
    "/review-rounds/{round_id}/verdict",
    summary="Submit a review verdict",
    description="Submit the final verdict for a review round with confidence and summary.",
    responses={
        404: {"description": "Review round not found"},
        409: {"description": "Review round not in valid state"},
    },
)
def submit_verdict(
    round_id: str,
    body: ReviewVerdictRequest,
    session: Session = Depends(get_session),
) -> dict[str, str | int | None]:  # noqa: B008
    svc = ReviewRoundService(session)
    try:
        rr = svc.submit_verdict(
            round_id,
            verdict=body.verdict,
            confidence=body.confidence,
            summary=body.summary,
        )
    except NotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
    except Conflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    return _review_round_dict(rr)
