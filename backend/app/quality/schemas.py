from pydantic import BaseModel, Field


class AcceptanceCriterionCreate(BaseModel):
    description: str = Field(..., min_length=1, max_length=10000)


class AcceptanceCriterionUpdate(BaseModel):
    description: str | None = Field(default=None, min_length=1, max_length=10000)
    status: str | None = Field(default=None, pattern=r"^[a-z_]+$")


class DoDItemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class DoDItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    status: str | None = Field(default=None, pattern=r"^[a-z_]+$")


class QualityStatsResponse(BaseModel):
    total_tasks: int = Field(..., ge=0)
    tasks_with_ac: int = Field(..., ge=0)
    total_ac: int = Field(..., ge=0)
    passed_ac: int = Field(..., ge=0)
    total_dod: int = Field(..., ge=0)
    passed_dod: int = Field(..., ge=0)
    pass_rate: float = Field(..., ge=0, le=100)
