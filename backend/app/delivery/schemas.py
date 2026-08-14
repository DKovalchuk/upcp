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


# ── Response schemas ──


class FeatureResponse(BaseModel):
    id: str
    project_id: str
    component_id: str | None = None
    name: str
    slug: str
    description: str | None = None
    status: str
    created_at: str
    updated_at: str


class TaskResponse(BaseModel):
    id: str
    feature_id: str
    component_id: str | None = None
    module_id: str | None = None
    title: str
    description: str | None = None
    status: str
    priority: int
    assignee_type: str | None = None
    assignee_id: str | None = None
    created_at: str
    updated_at: str


class SubtaskResponse(BaseModel):
    id: str
    task_id: str
    title: str
    description: str | None = None
    status: str
    created_at: str
    updated_at: str


class TaskListResponse(BaseModel):
    items: list[TaskResponse]
    total: int
    offset: int
    limit: int


class TaskBulkUpdates(BaseModel):
    status: str | None = Field(default=None, pattern=r"^[a-z_]+$")
    priority: int | None = Field(default=None, ge=0, le=10)
    assignee_type: str | None = Field(default=None, min_length=1, max_length=255)
    assignee_id: str | None = Field(default=None, min_length=1, max_length=255)


class BulkTaskUpdate(BaseModel):
    task_ids: list[str] = Field(..., max_length=100)
    updates: TaskBulkUpdates


class BulkTaskResponse(BaseModel):
    updated: int
