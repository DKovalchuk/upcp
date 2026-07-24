from pydantic import BaseModel


class AcceptanceCriterionCreate(BaseModel):
    description: str


class AcceptanceCriterionUpdate(BaseModel):
    description: str | None = None
    status: str | None = None


class DoDItemCreate(BaseModel):
    name: str


class DoDItemUpdate(BaseModel):
    name: str | None = None
    status: str | None = None
