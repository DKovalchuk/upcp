from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.delivery.lifecycle import InvalidTransition
from app.delivery.models import Feature, Subtask, Task
from app.delivery.schemas import (
    BulkTaskUpdate,
    FeatureCreate,
    FeatureResponse,
    FeatureUpdate,
    SubtaskCreate,
    SubtaskResponse,
    SubtaskUpdate,
    TaskCreate,
    TaskListResponse,
    TaskResponse,
    TaskUpdate,
)
from app.delivery.service import CommentService, FeatureService, SubtaskService, TaskService
from app.shared.database import get_session
from app.shared.errors import NotFound, ValidationError
from app.shared.pagination import PaginationParams, pagination_dependency

router = APIRouter(tags=["delivery"])


def _feat_resp(f: Feature) -> FeatureResponse:
    return FeatureResponse(
        id=f.id,
        project_id=f.project_id,
        component_id=f.component_id,
        name=f.name,
        slug=f.slug,
        description=f.description,
        status=f.status,
        created_at=f.created_at.isoformat(),
        updated_at=f.updated_at.isoformat(),
    )


def _task_resp(t: Task) -> TaskResponse:
    return TaskResponse(
        id=t.id,
        feature_id=t.feature_id,
        component_id=t.component_id,
        module_id=t.module_id,
        title=t.title,
        description=t.description,
        status=t.status,
        priority=t.priority,
        assignee_type=t.assignee_type,
        assignee_id=t.assignee_id,
        created_at=t.created_at.isoformat(),
        updated_at=t.updated_at.isoformat(),
    )


def _sub_resp(s: Subtask) -> SubtaskResponse:
    return SubtaskResponse(
        id=s.id,
        task_id=s.task_id,
        title=s.title,
        description=s.description,
        status=s.status,
        created_at=s.created_at.isoformat(),
        updated_at=s.updated_at.isoformat(),
    )


# ── Feature ──


@router.post(
    "/projects/{project_id}/features",
    status_code=201,
    response_model=FeatureResponse,
    summary="Create a feature",
    description="Create a new feature within a project, optionally linked to a component.",
    responses={422: {"description": "Validation error"}},
)
def create_feature(
    project_id: str, body: FeatureCreate, session: Session = Depends(get_session)
) -> FeatureResponse:  # noqa: B008
    svc = FeatureService(session)
    feature = svc.create(
        project_id=project_id,
        name=body.name,
        slug=body.slug,
        description=body.description,
        status=body.status,
        component_id=body.component_id,
    )
    # Commit BEFORE responding: get_session's teardown commit runs after
    # the 201 is sent, so a client chaining create → use(id) races the
    # commit and gets FK 500s (TASK-0140 probe: 37/40 rows not visible
    # to another connection at response time).
    session.commit()
    return _feat_resp(feature)


@router.get(
    "/features/{feature_id}",
    response_model=FeatureResponse,
    summary="Get a feature by ID",
    description="Retrieve a single feature by its unique identifier.",
    responses={404: {"description": "Feature not found"}},
)
def get_feature(feature_id: str, session: Session = Depends(get_session)) -> FeatureResponse:  # noqa: B008
    return _feat_resp(FeatureService(session).get(feature_id))


@router.patch(
    "/features/{feature_id}",
    response_model=FeatureResponse,
    summary="Update a feature",
    description="Partially update a feature. Only provided fields are changed.",
    responses={
        404: {"description": "Feature not found"},
        422: {"description": "Validation error"},
    },
)
def update_feature(
    feature_id: str, body: FeatureUpdate, session: Session = Depends(get_session)
) -> FeatureResponse:  # noqa: B008
    return _feat_resp(
        FeatureService(session).update(feature_id, **body.model_dump(exclude_unset=True))
    )


@router.delete(
    "/features/{feature_id}",
    status_code=204,
    summary="Delete a feature",
    description="Delete a feature by its identifier.",
    responses={404: {"description": "Feature not found"}},
)
def delete_feature(feature_id: str, session: Session = Depends(get_session)) -> None:  # noqa: B008
    FeatureService(session).delete(feature_id)


@router.get(
    "/projects/{project_id}/features",
    summary="List features for a project",
    description="List all features within a project with pagination.",
)
def list_features(
    project_id: str,
    status: str | None = None,
    search: str | None = None,
    sort_by: str = "created_at",
    sort_dir: str = "desc",
    pagination: PaginationParams = Depends(pagination_dependency),
    session: Session = Depends(get_session),
) -> dict[str, object]:  # noqa: B008
    svc = FeatureService(session)
    items, total = svc.list_features(
        project_id,
        offset=pagination.offset,
        limit=pagination.limit,
        status=status,
        search=search,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    return {
        "items": [_feat_resp(f) for f in items],
        "total": total,
        "offset": pagination.offset,
        "limit": pagination.limit,
    }


# ── Task ──


@router.post(
    "/features/{feature_id}/tasks",
    status_code=201,
    response_model=TaskResponse,
    summary="Create a task",
    description="Create a new task within a feature with optional priority and assignee.",
    responses={422: {"description": "Validation error"}},
)
def create_task(
    feature_id: str, body: TaskCreate, session: Session = Depends(get_session)
) -> TaskResponse:  # noqa: B008
    svc = TaskService(session)
    task = svc.create(
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
    # Commit before responding — same create→use(id) race as create_feature.
    session.commit()
    return _task_resp(task)


@router.patch(
    "/tasks/bulk",
    summary="Bulk update tasks",
    description="Update multiple tasks at once with status, priority, or assignee changes.",
)
def bulk_update_tasks(
    body: BulkTaskUpdate,
    session: Session = Depends(get_session),
) -> dict[str, int]:  # noqa: B008
    svc = TaskService(session)
    try:
        count = svc.bulk_update(
            body.task_ids,
            status=body.updates.status,
            priority=body.updates.priority,
            assignee_type=body.updates.assignee_type,
            assignee_id=body.updates.assignee_id,
        )
    except ValidationError as exc:
        from fastapi import HTTPException

        raise HTTPException(status_code=422, detail=str(exc)) from None
    return {"updated": count}


@router.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    summary="Get a task by ID",
    description="Retrieve a single task by its unique identifier.",
    responses={404: {"description": "Task not found"}},
)
def get_task(task_id: str, session: Session = Depends(get_session)) -> TaskResponse:  # noqa: B008
    return _task_resp(TaskService(session).get(task_id))


@router.patch(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    summary="Update a task",
    description="Partially update a task. Only provided fields are changed.",
    responses={
        404: {"description": "Task not found"},
        422: {"description": "Validation error"},
    },
)
def update_task(
    task_id: str, body: TaskUpdate, session: Session = Depends(get_session)
) -> TaskResponse:  # noqa: B008
    try:
        task = TaskService(session).update(task_id, **body.model_dump(exclude_unset=True))
    except InvalidTransition as exc:
        # Same mapping as bulk_update_tasks: a forbidden lifecycle edge is a
        # client error (422), not an unhandled exception (500).
        from fastapi import HTTPException

        raise HTTPException(status_code=422, detail=str(exc)) from None
    return _task_resp(task)


@router.delete(
    "/tasks/{task_id}",
    status_code=204,
    summary="Delete a task",
    description="Delete a task by its identifier.",
    responses={404: {"description": "Task not found"}},
)
def delete_task(task_id: str, session: Session = Depends(get_session)) -> None:  # noqa: B008
    TaskService(session).delete(task_id)


@router.get(
    "/features/{feature_id}/tasks",
    response_model=TaskListResponse,
    summary="List tasks for a feature",
    description="List all tasks within a feature with pagination.",
)
def list_tasks(
    feature_id: str,
    status: str | None = None,
    priority: int | None = None,
    search: str | None = None,
    pagination: PaginationParams = Depends(pagination_dependency),
    session: Session = Depends(get_session),
) -> TaskListResponse:  # noqa: B008
    svc = TaskService(session)
    items, total = svc.list_tasks(
        feature_id,
        offset=pagination.offset,
        limit=pagination.limit,
        status=status,
        priority=priority,
        search=search,
    )
    return TaskListResponse(
        items=[_task_resp(t) for t in items],
        total=total,
        offset=pagination.offset,
        limit=pagination.limit,
    )


# ── Project-level tasks ──


@router.get(
    "/projects/{project_id}/tasks",
    response_model=TaskListResponse,
    summary="List tasks for a project",
    description="List all tasks across features within a project, with optional filtering and pagination.",
)
def list_tasks_by_project(
    project_id: str,
    pagination: PaginationParams = Depends(pagination_dependency),  # noqa: B008
    status: str | None = None,
    feature_id: str | None = None,
    assignee_type: str | None = None,
    priority: int | None = None,
    search: str | None = None,
    session: Session = Depends(get_session),  # noqa: B008
) -> TaskListResponse:
    svc = TaskService(session)
    items, total = svc.list_tasks_by_project(
        project_id,
        offset=pagination.offset,
        limit=pagination.limit,
        status=status,
        feature_id=feature_id,
        assignee_type=assignee_type,
        priority=priority,
        search=search,
    )
    return TaskListResponse(
        items=[_task_resp(t) for t in items],
        total=total,
        offset=pagination.offset,
        limit=pagination.limit,
    )


# ── Subtask ──


@router.post(
    "/tasks/{task_id}/subtasks",
    status_code=201,
    response_model=SubtaskResponse,
    summary="Create a subtask",
    description="Create a new subtask within a task.",
    responses={422: {"description": "Validation error"}},
)
def create_subtask(
    task_id: str, body: SubtaskCreate, session: Session = Depends(get_session)
) -> SubtaskResponse:  # noqa: B008
    svc = SubtaskService(session)
    return _sub_resp(
        svc.create(
            task_id=task_id, title=body.title, description=body.description, status=body.status
        )
    )


@router.get(
    "/subtasks/{subtask_id}",
    response_model=SubtaskResponse,
    summary="Get a subtask by ID",
    description="Retrieve a single subtask by its unique identifier.",
    responses={404: {"description": "Subtask not found"}},
)
def get_subtask(subtask_id: str, session: Session = Depends(get_session)) -> SubtaskResponse:  # noqa: B008
    return _sub_resp(SubtaskService(session).get(subtask_id))


@router.patch(
    "/subtasks/{subtask_id}",
    response_model=SubtaskResponse,
    summary="Update a subtask",
    description="Partially update a subtask. Only provided fields are changed.",
    responses={
        404: {"description": "Subtask not found"},
        422: {"description": "Validation error"},
    },
)
def update_subtask(
    subtask_id: str, body: SubtaskUpdate, session: Session = Depends(get_session)
) -> SubtaskResponse:  # noqa: B008
    return _sub_resp(
        SubtaskService(session).update(subtask_id, **body.model_dump(exclude_unset=True))
    )


@router.delete(
    "/subtasks/{subtask_id}",
    status_code=204,
    summary="Delete a subtask",
    description="Delete a subtask by its identifier.",
    responses={404: {"description": "Subtask not found"}},
)
def delete_subtask(subtask_id: str, session: Session = Depends(get_session)) -> None:  # noqa: B008
    SubtaskService(session).delete(subtask_id)


@router.get(
    "/tasks/{task_id}/subtasks",
    summary="List subtasks for a task",
    description="List all subtasks within a task with pagination.",
)
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


# ── Comment endpoints ──


@router.post(
    "/tasks/{task_id}/comments",
    status_code=201,
    summary="Create a comment on a task",
    description="Add a comment or reply to a task.",
)
def create_comment(
    task_id: str,
    body: str = "",
    author_type: str = "human",
    author_id: str = "default",
    parent_id: str | None = None,
    session: Session = Depends(get_session),
) -> dict[str, str | None]:  # noqa: B008
    svc = CommentService(session)
    try:
        c = svc.create(
            task_id=task_id,
            author_type=author_type,
            author_id=author_id,
            body=body,
            parent_id=parent_id,
        )
    except NotFound as exc:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail=str(exc)) from None
    return {
        "id": c.id,
        "task_id": c.task_id,
        "author_type": c.author_type,
        "author_id": c.author_id,
        "body": c.body,
        "parent_id": c.parent_id,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


@router.get(
    "/tasks/{task_id}/comments",
    summary="List comments for a task",
    description="List all comments on a task, ordered by creation time.",
)
def list_comments(
    task_id: str,
    session: Session = Depends(get_session),
) -> dict[str, list[dict[str, str | None]]]:  # noqa: B008
    svc = CommentService(session)
    comments = svc.list_by_task(task_id)
    return {
        "items": [
            {
                "id": c.id,
                "task_id": c.task_id,
                "author_type": c.author_type,
                "author_id": c.author_id,
                "body": c.body,
                "parent_id": c.parent_id,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in comments
        ]
    }
