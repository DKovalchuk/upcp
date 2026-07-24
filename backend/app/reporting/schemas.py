from pydantic import BaseModel, Field


class ReportCreate(BaseModel):
    report_type: str = Field(..., min_length=1, max_length=255, pattern=r"^[a-z_]+$")
    content: dict[str, object] | None = None


class ReportResponse(BaseModel):
    id: str = Field(..., min_length=1, max_length=255)
    project_id: str = Field(..., min_length=1, max_length=255)
    report_type: str = Field(..., min_length=1, max_length=255, pattern=r"^[a-z_]+$")
    content: dict[str, object] | None = None
    summary: str | None = Field(default=None, max_length=10000)
    created_at: str = Field(..., max_length=255)


class ReportSummary(BaseModel):
    summary: str = Field(..., min_length=1, max_length=10000)


class TaskCountsByStatus(BaseModel):
    backlog: int = 0
    in_progress: int = 0
    review: int = 0
    done: int = 0


class ProjectSummary(BaseModel):
    id: str
    name: str
    slug: str
    description: str | None = None
    status: str
    created_at: str
    updated_at: str


class AuditEventSummary(BaseModel):
    id: str
    timestamp: str
    event_type: str
    entity_type: str
    entity_id: str
    actor_type: str
    actor_id: str
    payload: dict[str, object] | None = None
    note: str | None = None


class DashboardStatsResponse(BaseModel):
    project_count: int
    task_counts_by_status: TaskCountsByStatus
    recent_projects: list[ProjectSummary]
    recent_activity: list[AuditEventSummary]