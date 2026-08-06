from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.shared.database import get_session
from app.shared.pagination import PaginationParams, pagination_dependency
from app.structure.models import Component, Module
from app.structure.schemas import (
    ComponentCreate,
    ComponentResponse,
    ComponentUpdate,
    ModuleCreate,
    ModuleResponse,
    ModuleUpdate,
)
from app.structure.service import ComponentService, ModuleService

router = APIRouter(tags=["structure"])


def _comp_resp(c: Component) -> ComponentResponse:
    return ComponentResponse(
        id=c.id,
        project_id=c.project_id,
        name=c.name,
        slug=c.slug,
        description=c.description,
        status=c.status,
        created_at=c.created_at.isoformat(),
        updated_at=c.updated_at.isoformat(),
    )


def _mod_resp(m: Module) -> ModuleResponse:
    return ModuleResponse(
        id=m.id,
        component_id=m.component_id,
        name=m.name,
        slug=m.slug,
        description=m.description,
        status=m.status,
        created_at=m.created_at.isoformat(),
        updated_at=m.updated_at.isoformat(),
    )


# ── Component ──


@router.post(
    "/projects/{project_id}/components",
    status_code=201,
    response_model=ComponentResponse,
    summary="Create a component",
    description="Create a new component within a project.",
    responses={422: {"description": "Validation error"}},
)
def create_component(
    project_id: str, body: ComponentCreate, session: Session = Depends(get_session)
) -> ComponentResponse:  # noqa: B008
    service = ComponentService(session)
    comp = service.create(
        project_id=project_id,
        name=body.name,
        slug=body.slug,
        description=body.description,
        status=body.status,
    )
    return _comp_resp(comp)


@router.get(
    "/components/{component_id}",
    response_model=ComponentResponse,
    summary="Get a component by ID",
    description="Retrieve a single component by its unique identifier.",
    responses={404: {"description": "Component not found"}},
)
def get_component(component_id: str, session: Session = Depends(get_session)) -> ComponentResponse:  # noqa: B008
    service = ComponentService(session)
    return _comp_resp(service.get(component_id))


@router.patch(
    "/components/{component_id}",
    response_model=ComponentResponse,
    summary="Update a component",
    description="Partially update a component. Only provided fields are changed.",
    responses={
        404: {"description": "Component not found"},
        422: {"description": "Validation error"},
    },
)
def update_component(
    component_id: str, body: ComponentUpdate, session: Session = Depends(get_session)
) -> ComponentResponse:  # noqa: B008
    service = ComponentService(session)
    comp = service.update(component_id, **body.model_dump(exclude_unset=True))
    return _comp_resp(comp)


@router.delete(
    "/components/{component_id}",
    status_code=204,
    summary="Delete a component",
    description="Delete a component by its identifier.",
    responses={404: {"description": "Component not found"}},
)
def delete_component(component_id: str, session: Session = Depends(get_session)) -> None:  # noqa: B008
    ComponentService(session).delete(component_id)


@router.get(
    "/projects/{project_id}/components",
    summary="List components for a project",
    description="List all components within a project with pagination.",
)
def list_components(
    project_id: str,
    pagination: PaginationParams = Depends(pagination_dependency),  # noqa: B008
    session: Session = Depends(get_session),  # noqa: B008
) -> dict[str, object]:
    service = ComponentService(session)
    items, total = service.list_components(
        project_id, offset=pagination.offset, limit=pagination.limit
    )
    return {
        "items": [_comp_resp(c) for c in items],
        "total": total,
        "offset": pagination.offset,
        "limit": pagination.limit,
    }


# ── Module ──


@router.post(
    "/components/{component_id}/modules",
    status_code=201,
    response_model=ModuleResponse,
    summary="Create a module",
    description="Create a new module within a component.",
    responses={422: {"description": "Validation error"}},
)
def create_module(
    component_id: str, body: ModuleCreate, session: Session = Depends(get_session)
) -> ModuleResponse:  # noqa: B008
    service = ModuleService(session)
    mod = service.create(
        component_id=component_id,
        name=body.name,
        slug=body.slug,
        description=body.description,
        status=body.status,
    )
    return _mod_resp(mod)


@router.get(
    "/modules/{module_id}",
    response_model=ModuleResponse,
    summary="Get a module by ID",
    description="Retrieve a single module by its unique identifier.",
    responses={404: {"description": "Module not found"}},
)
def get_module(module_id: str, session: Session = Depends(get_session)) -> ModuleResponse:  # noqa: B008
    service = ModuleService(session)
    return _mod_resp(service.get(module_id))


@router.patch(
    "/modules/{module_id}",
    response_model=ModuleResponse,
    summary="Update a module",
    description="Partially update a module. Only provided fields are changed.",
    responses={
        404: {"description": "Module not found"},
        422: {"description": "Validation error"},
    },
)
def update_module(
    module_id: str, body: ModuleUpdate, session: Session = Depends(get_session)
) -> ModuleResponse:  # noqa: B008
    service = ModuleService(session)
    mod = service.update(module_id, **body.model_dump(exclude_unset=True))
    return _mod_resp(mod)


@router.delete(
    "/modules/{module_id}",
    status_code=204,
    summary="Delete a module",
    description="Delete a module by its identifier.",
    responses={404: {"description": "Module not found"}},
)
def delete_module(module_id: str, session: Session = Depends(get_session)) -> None:  # noqa: B008
    ModuleService(session).delete(module_id)


@router.get(
    "/components/{component_id}/modules",
    summary="List modules for a component",
    description="List all modules within a component with pagination.",
)
def list_modules(
    component_id: str,
    pagination: PaginationParams = Depends(pagination_dependency),  # noqa: B008
    session: Session = Depends(get_session),  # noqa: B008
) -> dict[str, object]:
    service = ModuleService(session)
    items, total = service.list_modules(
        component_id, offset=pagination.offset, limit=pagination.limit
    )
    return {
        "items": [_mod_resp(m) for m in items],
        "total": total,
        "offset": pagination.offset,
        "limit": pagination.limit,
    }
