from pydantic import BaseModel, Field


class FeatureCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str | None = Field(default=None, min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$")
    description: str | None = Field(default=None, max_length=10000)
    status: str = Field(default="backlog", pattern=r"^[a-z_]+$")
    component_id: str | None = Field(default=None, min_length=1, max_length=255)


class FeatureUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    slug: str | None = Field(default=None, min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$")
    description: str | None = Field(default=None, max_length=10000)
    status: str | None = Field(default=None, pattern=r"^[a-z_]+$")
    component_id: str | None = Field(default=None, min_length=1, max_length=255)


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=10000)
    status: str = Field(default="backlog", pattern=r"^[a-z_]+$")
    priority: int = Field(default=0, ge=0, le=10)
    assignee_type: str | None = Field(default=None, min_length=1, max_length=255)
    assignee_id: str | None = Field(default=None, min_length=1, max_length=255)
    component_id: str | None = Field(default=None, min_length=1, max_length=255)
    module_id: str | None = Field(default=None, min_length=1, max_length=255)


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=10000)
    status: str | None = Field(default=None, pattern=r"^[a-z_]+$")
    priority: int | None = Field(default=None, ge=0, le=10)
    assignee_type: str | None = Field(default=None, min_length=1, max_length=255)
    assignee_id: str | None = Field(default=None, min_length=1, max_length=255)
    component_id: str | None = Field(default=None, min_length=1, max_length=255)
    module_id: str | None = Field(default=None, min_length=1, max_length=255)


class SubtaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=10000)
    status: str = Field(default="todo", pattern=r"^[a-z_]+$")


class SubtaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=10000)
    status: str | None = Field(default=None, pattern=r"^[a-z_]+$")
