from pydantic import BaseModel


class ErrorResponse(BaseModel):
    error: str
    detail: str


class HealthResponse(BaseModel):
    status: str
    service: str
