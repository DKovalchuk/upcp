from pydantic import BaseModel


class ErrorResponse(BaseModel):
    error: str
    detail: str


class HealthCheckResult(BaseModel):
    status: str
    latency_ms: float | None = None
    error: str | None = None


class HealthResponse(BaseModel):
    status: str
    service: str
    db: HealthCheckResult
    redis: HealthCheckResult
