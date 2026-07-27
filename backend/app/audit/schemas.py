from pydantic import BaseModel, Field


class AuditEventResponse(BaseModel):
    id: str = Field(..., min_length=1, max_length=36)
    timestamp: str = Field(..., max_length=255)
    event_type: str = Field(..., min_length=1, max_length=255)
    entity_type: str = Field(..., min_length=1, max_length=255)
    entity_id: str = Field(..., min_length=1, max_length=36)
    actor_type: str = Field(..., min_length=1, max_length=50)
    actor_id: str = Field(..., min_length=1, max_length=36)
    payload: dict[str, object] | None = None
    note: str | None = None
