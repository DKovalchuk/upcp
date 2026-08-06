from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.projects.schemas import ProjectCreate, ProjectResponse, ProjectUpdate
from app.projects.service import ProjectService
from app.shared.database import get_session
from app.shared.pagination import PaginationParams, pagination_dependency

router = APIRouter(tags=["projects"])


@router.post(
    "/projects",
    response_model=ProjectResponse,
    status_code=201,
    summary="Create a project",
    description="Create a new project with the given name, slug, and optional description.",
    responses={422: {"description": "Validation error"}},
)
def create_project(body: ProjectCreate, session: Session = Depends(get_session)) -> ProjectResponse:  # noqa: B008
    service = ProjectService(session)
    project = service.create(
        name=body.name, slug=body.slug, description=body.description, status=body.status
    )
    return ProjectResponse(
        id=project.id,
        name=project.name,
        slug=project.slug,
        description=project.description,
        status=project.status,
        created_at=project.created_at.isoformat(),
        updated_at=project.updated_at.isoformat(),
    )


@router.get(
    "/projects/{project_id}",
    response_model=ProjectResponse,
    summary="Get a project by ID",
    description="Retrieve a single project by its unique identifier.",
    responses={404: {"description": "Project not found"}},
)
def get_project(project_id: str, session: Session = Depends(get_session)) -> ProjectResponse:  # noqa: B008
    service = ProjectService(session)
    project = service.get(project_id)
    return ProjectResponse(
        id=project.id,
        name=project.name,
        slug=project.slug,
        description=project.description,
        status=project.status,
        created_at=project.created_at.isoformat(),
        updated_at=project.updated_at.isoformat(),
    )


@router.patch(
    "/projects/{project_id}",
    response_model=ProjectResponse,
    summary="Update a project",
    description="Partially update a project. Only provided fields are changed.",
    responses={
        404: {"description": "Project not found"},
        422: {"description": "Validation error"},
    },
)
def update_project(
    project_id: str, body: ProjectUpdate, session: Session = Depends(get_session)
) -> ProjectResponse:  # noqa: B008
    service = ProjectService(session)
    fields = body.model_dump(exclude_unset=True)
    project = service.update(project_id, **fields)
    return ProjectResponse(
        id=project.id,
        name=project.name,
        slug=project.slug,
        description=project.description,
        status=project.status,
        created_at=project.created_at.isoformat(),
        updated_at=project.updated_at.isoformat(),
    )


@router.delete(
    "/projects/{project_id}",
    status_code=204,
    summary="Delete a project",
    description="Delete a project by its identifier. Returns 204 on success.",
    responses={404: {"description": "Project not found"}},
)
def delete_project(project_id: str, session: Session = Depends(get_session)) -> None:  # noqa: B008
    service = ProjectService(session)
    service.delete(project_id)


@router.get(
    "/projects",
    summary="List projects",
    description="List all projects with optional filtering, sorting, and pagination.",
)
def list_projects(
    pagination: PaginationParams = Depends(pagination_dependency),  # noqa: B008
    session: Session = Depends(get_session),  # noqa: B008
    status: str | None = Query(None),
    search: str | None = Query(None),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc"),
) -> dict[str, object]:
    service = ProjectService(session)
    projects, total = service.list_projects(
        offset=pagination.offset,
        limit=pagination.limit,
        status=status,
        search=search,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )
    items = [
        {
            "id": p.id,
            "name": p.name,
            "slug": p.slug,
            "description": p.description,
            "status": p.status,
            "created_at": p.created_at.isoformat(),
            "updated_at": p.updated_at.isoformat(),
        }
        for p in projects
    ]
    return {"items": items, "total": total, "offset": pagination.offset, "limit": pagination.limit}
