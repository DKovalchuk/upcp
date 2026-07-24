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