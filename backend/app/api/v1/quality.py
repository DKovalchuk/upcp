from typing import Any

from fastapi import APIRouter, Depends, HTTPException
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
from app.shared.database import get_session
from app.shared.errors import Conflict, NotFound

router = APIRouter(tags=["quality"])


@router.post("/tasks/{task_id}/acceptance-criteria", status_code=201)
def create_ac(
    task_id: str, body: AcceptanceCriterionCreate, session: Session = Depends(get_session)
) -> dict[str, str]:  # noqa: B008
    svc = AcceptanceCriterionService(session)
    ac = svc.create(task_id=task_id, description=body.description)
    return {"id": ac.id, "task_id": ac.task_id, "description": ac.description, "status": ac.status}


@router.get("/acceptance-criteria/{ac_id}")
def get_ac(ac_id: str, session: Session = Depends(get_session)) -> dict[str, str]:  # noqa: B008
    ac = AcceptanceCriterionService(session).get(ac_id)
    return {"id": ac.id, "task_id": ac.task_id, "description": ac.description, "status": ac.status}


@router.patch("/acceptance-criteria/{ac_id}")
def update_ac(
    ac_id: str, body: AcceptanceCriterionUpdate, session: Session = Depends(get_session)
) -> dict[str, str]:  # noqa: B008
    ac = AcceptanceCriterionService(session).update(ac_id, **body.model_dump(exclude_unset=True))
    return {"id": ac.id, "task_id": ac.task_id, "description": ac.description, "status": ac.status}


@router.delete("/acceptance-criteria/{ac_id}", status_code=204)
def delete_ac(ac_id: str, session: Session = Depends(get_session)) -> None:  # noqa: B008
    AcceptanceCriterionService(session).delete(ac_id)


@router.get("/tasks/{task_id}/acceptance-criteria")
def list_acs(task_id: str, session: Session = Depends(get_session)) -> list[dict[str, str]]:  # noqa: B008
    items = AcceptanceCriterionService(session).list_by_task(task_id)
    return [
        {"id": a.id, "task_id": a.task_id, "description": a.description, "status": a.status}
        for a in items
    ]


@router.post("/tasks/{task_id}/dod-items", status_code=201)
def create_dod(
    task_id: str, body: DoDItemCreate, session: Session = Depends(get_session)
) -> dict[str, str]:  # noqa: B008
    svc = DoDItemService(session)
    item = svc.create(task_id=task_id, name=body.name)
    return {"id": item.id, "task_id": item.task_id, "name": item.name, "status": item.status}


@router.get("/dod-items/{item_id}")
def get_dod(item_id: str, session: Session = Depends(get_session)) -> dict[str, str]:  # noqa: B008
    item = DoDItemService(session).get(item_id)
    return {"id": item.id, "task_id": item.task_id, "name": item.name, "status": item.status}


@router.patch("/dod-items/{item_id}")
def update_dod(
    item_id: str, body: DoDItemUpdate, session: Session = Depends(get_session)
) -> dict[str, str]:  # noqa: B008
    item = DoDItemService(session).update(item_id, **body.model_dump(exclude_unset=True))
    return {"id": item.id, "task_id": item.task_id, "name": item.name, "status": item.status}


@router.delete("/dod-items/{item_id}", status_code=204)
def delete_dod(item_id: str, session: Session = Depends(get_session)) -> None:  # noqa: B008
    DoDItemService(session).delete(item_id)


@router.get("/tasks/{task_id}/dod-items")
def list_dods(task_id: str, session: Session = Depends(get_session)) -> list[dict[str, str]]:  # noqa: B008
    items = DoDItemService(session).list_by_task(task_id)
    return [{"id": i.id, "task_id": i.task_id, "name": i.name, "status": i.status} for i in items]


@router.post("/tasks/{task_id}/complete")
def complete_task(task_id: str, session: Session = Depends(get_session)) -> dict[str, str]:  # noqa: B008
    task = TaskService(session).complete(task_id)
    return {"id": task.id, "status": task.status}


@router.post("/tasks/{task_id}/submit-review", status_code=201)
def submit_task_for_review(
    task_id: str,
    session: Session = Depends(get_session),
) -> dict[str, str | None]:  # noqa: B008
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


@router.get("/projects/{project_id}/quality/stats", response_model=QualityStatsResponse)
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


def _evidence_dict(e: Any) -> dict[str, str | None]:
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
        "created_by_type": e.created_by_type,
        "created_by_id": e.created_by_id,
        "verification_state": e.verification_state,
        "verified_by_type": e.verified_by_type,
        "verified_by_id": e.verified_by_id,
        "verified_at": e.verified_at.isoformat() if e.verified_at else None,
        "created_at": e.created_at.isoformat() if e.created_at else None,
    }


@router.get("/tasks/{task_id}/evidence")
def list_evidence(
    task_id: str, session: Session = Depends(get_session)
) -> dict[str, list[dict[str, str | None]]]:  # noqa: B008
    items = EvidenceService(session).list_by_task(task_id)
    return {"items": [_evidence_dict(e) for e in items]}


@router.post("/tasks/{task_id}/evidence", status_code=201)
def create_evidence(
    task_id: str, body: EvidenceCreate, session: Session = Depends(get_session)
) -> dict[str, str | None]:  # noqa: B008
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


@router.post("/evidence/{evidence_id}/agent-verify")
def agent_verify_evidence(
    evidence_id: str,
    body: EvidenceVerifyRequest | None = None,
    session: Session = Depends(get_session),
) -> dict[str, str | None]:  # noqa: B008
    svc = EvidenceService(session)
    try:
        e = svc.verify(evidence_id, verified_by_type="agent", verified_by_id="agent")
    except NotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
    except Conflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    return _evidence_dict(e)


@router.post("/evidence/{evidence_id}/human-accept")
def human_accept_evidence(
    evidence_id: str,
    session: Session = Depends(get_session),
) -> dict[str, str | None]:  # noqa: B008
    svc = EvidenceService(session)
    try:
        e = svc.accept(evidence_id, verified_by_type="human", verified_by_id="human")
    except NotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
    except Conflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    return _evidence_dict(e)


@router.post("/evidence/{evidence_id}/reject")
def reject_evidence(
    evidence_id: str,
    body: EvidenceRejectRequest | None = None,
    session: Session = Depends(get_session),
) -> dict[str, str | None]:  # noqa: B008
    svc = EvidenceService(session)
    try:
        e = svc.reject(evidence_id, verified_by_type="human", verified_by_id="human")
    except NotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
    except Conflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    return _evidence_dict(e)


# ── Review Round endpoints ──


def _review_round_dict(rr: Any) -> dict[str, str | None]:
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


@router.get("/tasks/{task_id}/review-rounds")
def list_review_rounds(
    task_id: str, session: Session = Depends(get_session)
) -> dict[str, list[dict[str, str | None]]]:  # noqa: B008
    svc = ReviewRoundService(session)
    items = svc.list_by_task(task_id)
    return {"items": [_review_round_dict(rr) for rr in items]}


@router.post("/tasks/{task_id}/review-rounds", status_code=201)
def create_review_round(
    task_id: str,
    body: ReviewRoundCreate,
    session: Session = Depends(get_session),
) -> dict[str, str | None]:  # noqa: B008
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


@router.post("/review-rounds/{round_id}/start")
def start_review_round(
    round_id: str, session: Session = Depends(get_session)
) -> dict[str, str | None]:  # noqa: B008
    svc = ReviewRoundService(session)
    try:
        rr = svc.start(round_id)
    except NotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from None
    except Conflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    return _review_round_dict(rr)


@router.post("/review-rounds/{round_id}/findings", status_code=201)
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


@router.post("/review-rounds/{round_id}/verdict")
def submit_verdict(
    round_id: str,
    body: ReviewVerdictRequest,
    session: Session = Depends(get_session),
) -> dict[str, str | None]:  # noqa: B008
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
