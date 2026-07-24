from pydantic import BaseModel


class ComponentCreate(BaseModel):
    name: str
    slug: str | None = None
    description: str | None = None
    status: str = "active"


class ComponentUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    status: str | None = None


class ComponentResponse(BaseModel):
    id: str
    project_id: str
    name: str
    slug: str
    description: str | None = None
    status: str
    created_at: str
    updated_at: str


class ModuleCreate(BaseModel):
    name: str
    slug: str | None = None
    description: str | None = None
    status: str = "active"


class ModuleUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    status: str | None = None


class ModuleResponse(BaseModel):
    id: str
    component_id: str
    name: str
    slug: str
    description: str | None = None
    status: str
    created_at: str
    updated_at: str
