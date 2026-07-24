from pydantic import BaseModel, Field


class ComponentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str | None = Field(default=None, min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$")
    description: str | None = Field(default=None, max_length=10000)
    status: str = Field(default="active", pattern=r"^[a-z_]+$")


class ComponentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    slug: str | None = Field(default=None, min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$")
    description: str | None = Field(default=None, max_length=10000)
    status: str | None = Field(default=None, pattern=r"^[a-z_]+$")


class ComponentResponse(BaseModel):
    id: str = Field(..., min_length=1, max_length=255)
    project_id: str = Field(..., min_length=1, max_length=255)
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$")
    description: str | None = Field(default=None, max_length=10000)
    status: str = Field(..., pattern=r"^[a-z_]+$")
    created_at: str = Field(..., max_length=255)
    updated_at: str = Field(..., max_length=255)


class ModuleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str | None = Field(default=None, min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$")
    description: str | None = Field(default=None, max_length=10000)
    status: str = Field(default="active", pattern=r"^[a-z_]+$")


class ModuleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    slug: str | None = Field(default=None, min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$")
    description: str | None = Field(default=None, max_length=10000)
    status: str | None = Field(default=None, pattern=r"^[a-z_]+$")


class ModuleResponse(BaseModel):
    id: str = Field(..., min_length=1, max_length=255)
    component_id: str = Field(..., min_length=1, max_length=255)
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$")
    description: str | None = Field(default=None, max_length=10000)
    status: str = Field(..., pattern=r"^[a-z_]+$")
    created_at: str = Field(..., max_length=255)
    updated_at: str = Field(..., max_length=255)
