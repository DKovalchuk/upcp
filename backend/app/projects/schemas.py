from pydantic import BaseModel, Field, field_validator


def _reject_nul(value: str | None) -> str | None:
    # PostgreSQL rejects NUL (0x00) in text — an unhandled DB error surfaces
    # as 500; fail fast at the boundary with 422 instead (TASK-0142).
    if value is not None and "\x00" in value:
        raise ValueError("must not contain NUL bytes")
    return value


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str | None = Field(default=None, min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$")
    description: str | None = Field(default=None, max_length=10000)
    status: str = Field(default="active", pattern=r"^[a-z_]+$")

    @field_validator("name", "description")
    @classmethod
    def _no_nul(cls, value: str | None) -> str | None:
        return _reject_nul(value)


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    slug: str | None = Field(default=None, min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$")
    description: str | None = Field(default=None, max_length=10000)
    status: str | None = Field(default=None, pattern=r"^[a-z_]+$")

    @field_validator("name", "description")
    @classmethod
    def _no_nul(cls, value: str | None) -> str | None:
        return _reject_nul(value)


class ProjectResponse(BaseModel):
    id: str = Field(..., min_length=1, max_length=255)
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$")
    description: str | None = Field(default=None, max_length=10000)
    status: str = Field(..., pattern=r"^[a-z_]+$")
    created_at: str = Field(..., max_length=255)
    updated_at: str = Field(..., max_length=255)
