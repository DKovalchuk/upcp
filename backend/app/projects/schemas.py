from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str
    slug: str | None = None
    description: str | None = None
    status: str = "active"


class ProjectUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    status: str | None = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: str | None = None
    status: str
    created_at: str
    updated_at: str
