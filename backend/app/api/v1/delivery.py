from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.delivery.models import Feature, Subtask, Task
from app.delivery.schemas import (
    FeatureCreate,
    FeatureUpdate,
    SubtaskCreate,
    SubtaskUpdate,
    TaskCreate,
    TaskUpdate,
)
from app.delivery.service import FeatureService, SubtaskService, TaskService
from app.shared.database import get_session
from app.shared.pagination import PaginationParams, pagination_dependency

router = APIRouter(tags=["delivery"])


def _feat_resp(f: Feature) -> dict[str, str | None]:
    return {
        "id": f.id,
        "project_id": f.project_id,
        "component_id": f.component_id,
        "name": f.name,
        "slug": f.slug,
        "description": f.description,
        "status": f.status,
        "created_at": f.created_at.isoformat(),
        "updated_at": f.updated_at.isoformat(),
    }


def _task_resp(t: Task) -> dict[str, str | None | int]:
    return {
        "id": t.id,
        "feature_id": t.feature_id,
        "component_id": t.component_id,
        "module_id": t.module_id,
        "title": t.title,
        "description": t.description,
        "status": t.status,
        "priority": t.priority,
        "assignee_type": t.assignee_type,
        "assignee_id": t.assignee_id,
        "created_at": t.created_at.isoformat(),
        "updated_at": t.updated_at.isoformat(),
    }


def _sub_resp(s: Subtask) -> dict[str, str | None]:
    return {
        "id": s.id,
        "task_id": s.task_id,
        "title": s.title,
        "description": s.description,
        "status": s.status,
        "created_at": s.created_at.isoformat(),
        "updated_at": s.updated_at.isoformat(),
    }


# ── Feature ──


@router.post("/projects/{project_id}/features", status_code=201)
def create_feature(
    project_id: str, body: FeatureCreate, session: Session = Depends(get_session)
) -> dict[str, str | None]:  # noqa: B008
    svc = FeatureService(session)
    return _feat_resp(
        svc.create(
            project_id=project_id,
            name=body.name,
            slug=body.slug,
            description=body.description,
            status=body.status,
            component_id=body.component_id,
        )
    )


@router.get("/features/{feature_id}")
def get_feature(feature_id: str, session: Session = Depends(get_session)) -> dict[str, str | None]:  # noqa: B008
    return _feat_resp(FeatureService(session).get(feature_id))


@router.patch("/features/{feature_id}")
def update_feature(
    feature_id: str, body: FeatureUpdate, session: Session = Depends(get_session)
) -> dict[str, str | None]:  # noqa: B008
    return _feat_resp(
        FeatureService(session).update(feature_id, **body.model_dump(exclude_unset=True))
    )


@router.delete("/features/{feature_id}", status_code=204)
def delete_feature(feature_id: str, session: Session = Depends(get_session)) -> None:  # noqa: B008
    FeatureService(session).delete(feature_id)


@router.get("/projects/{project_id}/features")
def list_features(
    project_id: str,
    pagination: PaginationParams = Depends(pagination_dependency),
    session: Session = Depends(get_session),
) -> dict[str, object]:  # noqa: B008
    svc = FeatureService(session)
    items, total = svc.list_features(project_id, offset=pagination.offset, limit=pagination.limit)
    return {
        "items": [_feat_resp(f) for f in items],
        "total": total,
        "offset": pagination.offset,
        "limit": pagination.limit,
    }


# ── Task ──


@router.post("/features/{feature_id}/tasks", status_code=201)
def create_task(
    feature_id: str, body: TaskCreate, session: Session = Depends(get_session)
) -> dict[str, str | None | int]:  # noqa: B008
    svc = TaskService(session)
    return _task_resp(
        svc.create(
            feature_id=feature_id,
            title=body.title,
            description=body.description,
            status=body.status,
            priority=body.priority,
            assignee_type=body.assignee_type,
            assignee_id=body.assignee_id,
            component_id=body.component_id,
            module_id=body.module_id,
        )
    )


@router.get("/tasks/{task_id}")
def get_task(task_id: str, session: Session = Depends(get_session)) -> dict[str, str | None | int]:  # noqa: B008
    return _task_resp(TaskService(session).get(task_id))


@router.patch("/tasks/{task_id}")
def update_task(
    task_id: str, body: TaskUpdate, session: Session = Depends(get_session)
) -> dict[str, str | None | int]:  # noqa: B008
    return _task_resp(TaskService(session).update(task_id, **body.model_dump(exclude_unset=True)))


@router.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: str, session: Session = Depends(get_session)) -> None:  # noqa: B008
    TaskService(session).delete(task_id)


@router.get("/features/{feature_id}/tasks")
def list_tasks(
    feature_id: str,
    pagination: PaginationParams = Depends(pagination_dependency),
    session: Session = Depends(get_session),
) -> dict[str, object]:  # noqa: B008
    svc = TaskService(session)
    items, total = svc.list_tasks(feature_id, offset=pagination.offset, limit=pagination.limit)
    return {
        "items": [_task_resp(t) for t in items],
        "total": total,
        "offset": pagination.offset,
        "limit": pagination.limit,
    }


# ── Subtask ──


@router.post("/tasks/{task_id}/subtasks", status_code=201)
def create_subtask(
    task_id: str, body: SubtaskCreate, session: Session = Depends(get_session)
) -> dict[str, str | None]:  # noqa: B008
    svc = SubtaskService(session)
    return _sub_resp(
        svc.create(
            task_id=task_id, title=body.title, description=body.description, status=body.status
        )
    )


@router.get("/subtasks/{subtask_id}")
def get_subtask(subtask_id: str, session: Session = Depends(get_session)) -> dict[str, str | None]:  # noqa: B008
    return _sub_resp(SubtaskService(session).get(subtask_id))


@router.patch("/subtasks/{subtask_id}")
def update_subtask(
    subtask_id: str, body: SubtaskUpdate, session: Session = Depends(get_session)
) -> dict[str, str | None]:  # noqa: B008
    return _sub_resp(
        SubtaskService(session).update(subtask_id, **body.model_dump(exclude_unset=True))
    )


@router.delete("/subtasks/{subtask_id}", status_code=204)
def delete_subtask(subtask_id: str, session: Session = Depends(get_session)) -> None:  # noqa: B008
    SubtaskService(session).delete(subtask_id)


@router.get("/tasks/{task_id}/subtasks")
def list_subtasks(
    task_id: str,
    pagination: PaginationParams = Depends(pagination_dependency),
    session: Session = Depends(get_session),
) -> dict[str, object]:  # noqa: B008
    svc = SubtaskService(session)
    items, total = svc.list_subtasks(task_id, offset=pagination.offset, limit=pagination.limit)
    return {
        "items": [_sub_resp(s) for s in items],
        "total": total,
        "offset": pagination.offset,
        "limit": pagination.limit,
    }
