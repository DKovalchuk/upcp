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
