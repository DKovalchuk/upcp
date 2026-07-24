from pydantic import BaseModel


class FeatureCreate(BaseModel):
    name: str
    slug: str | None = None
    description: str | None = None
    status: str = "backlog"
    component_id: str | None = None


class FeatureUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    status: str | None = None
    component_id: str | None = None


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    status: str = "backlog"
    priority: int = 0
    assignee_type: str | None = None
    assignee_id: str | None = None
    component_id: str | None = None
    module_id: str | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    priority: int | None = None
    assignee_type: str | None = None
    assignee_id: str | None = None
    component_id: str | None = None
    module_id: str | None = None


class SubtaskCreate(BaseModel):
    title: str
    description: str | None = None
    status: str = "todo"


class SubtaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
