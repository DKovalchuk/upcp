from pydantic import BaseModel


class ReportCreate(BaseModel):
    report_type: str  # daily, weekly, etc.
    content: dict[str, object] | None = None


class ReportResponse(BaseModel):
    id: str
    project_id: str
    report_type: str
    content: dict[str, object] | None = None
    summary: str | None = None
    created_at: str


class ReportSummary(BaseModel):
    summary: str