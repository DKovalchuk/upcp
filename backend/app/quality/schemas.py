from pydantic import BaseModel, Field


class AcceptanceCriterionCreate(BaseModel):
    description: str = Field(..., min_length=1, max_length=10000)


class AcceptanceCriterionUpdate(BaseModel):
    description: str | None = Field(default=None, min_length=1, max_length=10000)
    status: str | None = Field(default=None, pattern=r"^[a-z_]+$")


class DoDItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    required_evidence_type: str | None = Field(default=None, max_length=50)


class DoDItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    status: str | None = Field(default=None, pattern=r"^[a-z_]+$")


class EvidenceCreate(BaseModel):
    type: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=10000)
    url: str | None = Field(default=None, max_length=2048)
    content_snippet: str | None = Field(default=None, max_length=50000)
    artifact_ref: str | None = Field(default=None, max_length=512)
    dod_item_id: str | None = None
    created_by_type: str = Field(..., min_length=1, max_length=50)
    created_by_id: str = Field(..., min_length=1, max_length=255)


class EvidenceVerifyRequest(BaseModel):
    notes: str | None = None


class EvidenceRejectRequest(BaseModel):
    reason: str | None = None


class ReviewRoundCreate(BaseModel):
    reviewer_type: str | None = Field(default=None, max_length=50)
    reviewer_id: str | None = Field(default=None, max_length=255)


class ReviewFindingCreate(BaseModel):
    severity: str = Field(..., pattern=r"^(critical|major|minor|nit)$")
    category: str = Field(
        ..., pattern=r"^(correctness|completeness|security|performance|style|other)$"
    )
    message: str = Field(..., min_length=1, max_length=10000)
    evidence_id: str | None = None
    dod_item_id: str | None = None
    suggestion: str | None = Field(default=None, max_length=10000)


class ReviewVerdictRequest(BaseModel):
    verdict: str = Field(..., pattern=r"^(approve|reject|needs_changes)$")
    confidence: int = Field(..., ge=0, le=100)
    summary: str = Field(..., min_length=1, max_length=10000)


class QualityStatsResponse(BaseModel):
    total_tasks: int = Field(..., ge=0)
    tasks_with_ac: int = Field(..., ge=0)
    total_ac: int = Field(..., ge=0)
    passed_ac: int = Field(..., ge=0)
    total_dod: int = Field(..., ge=0)
    passed_dod: int = Field(..., ge=0)
    pass_rate: float = Field(..., ge=0, le=100)
