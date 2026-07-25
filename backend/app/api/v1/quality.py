from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.delivery.service import TaskService
from app.quality.schemas import (
    AcceptanceCriterionCreate,
    AcceptanceCriterionUpdate,
    DoDItemCreate,
    DoDItemUpdate,
    QualityStatsResponse,
)
from app.quality.service import AcceptanceCriterionService, DoDItemService, QualityStatsService
from app.shared.database import get_session

router = APIRouter(tags=["quality"])


@router.post("/tasks/{task_id}/acceptance-criteria", status_code=201)
def create_ac(task_id: str, body: AcceptanceCriterionCreate, session: Session = Depends(get_session)) -> dict[str, str]:  # noqa: B008
    svc = AcceptanceCriterionService(session)
    ac = svc.create(task_id=task_id, description=body.description)
    return {"id": ac.id, "task_id": ac.task_id, "description": ac.description, "status": ac.status}


@router.get("/acceptance-criteria/{ac_id}")
def get_ac(ac_id: str, session: Session = Depends(get_session)) -> dict[str, str]:  # noqa: B008
    ac = AcceptanceCriterionService(session).get(ac_id)
    return {"id": ac.id, "task_id": ac.task_id, "description": ac.description, "status": ac.status}


@router.patch("/acceptance-criteria/{ac_id}")
def update_ac(ac_id: str, body: AcceptanceCriterionUpdate, session: Session = Depends(get_session)) -> dict[str, str]:  # noqa: B008
    ac = AcceptanceCriterionService(session).update(ac_id, **body.model_dump(exclude_unset=True))
    return {"id": ac.id, "task_id": ac.task_id, "description": ac.description, "status": ac.status}


@router.delete("/acceptance-criteria/{ac_id}", status_code=204)
def delete_ac(ac_id: str, session: Session = Depends(get_session)) -> None:  # noqa: B008
    AcceptanceCriterionService(session).delete(ac_id)


@router.get("/tasks/{task_id}/acceptance-criteria")
def list_acs(task_id: str, session: Session = Depends(get_session)) -> list[dict[str, str]]:  # noqa: B008
    items = AcceptanceCriterionService(session).list_by_task(task_id)
    return [{"id": a.id, "task_id": a.task_id, "description": a.description, "status": a.status} for a in items]


@router.post("/tasks/{task_id}/dod-items", status_code=201)
def create_dod(task_id: str, body: DoDItemCreate, session: Session = Depends(get_session)) -> dict[str, str]:  # noqa: B008
    svc = DoDItemService(session)
    item = svc.create(task_id=task_id, name=body.name)
    return {"id": item.id, "task_id": item.task_id, "name": item.name, "status": item.status}


@router.get("/dod-items/{item_id}")
def get_dod(item_id: str, session: Session = Depends(get_session)) -> dict[str, str]:  # noqa: B008
    item = DoDItemService(session).get(item_id)
    return {"id": item.id, "task_id": item.task_id, "name": item.name, "status": item.status}


@router.patch("/dod-items/{item_id}")
def update_dod(item_id: str, body: DoDItemUpdate, session: Session = Depends(get_session)) -> dict[str, str]:  # noqa: B008
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


@router.get("/projects/{project_id}/quality/stats", response_model=QualityStatsResponse)
def get_quality_stats(project_id: str, session: Session = Depends(get_session)) -> QualityStatsResponse:  # noqa: B008
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
