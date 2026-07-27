from pydantic import BaseModel, Field


class GitProviderCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    provider_type: str = Field(..., min_length=1, max_length=255)
    url: str = Field(..., min_length=1, max_length=2048)


class GitLinkCreate(BaseModel):
    entity_type: str = Field(..., min_length=1, max_length=255)
    entity_id: str = Field(..., min_length=1, max_length=255)
    git_type: str = Field(..., min_length=1, max_length=255)
    git_id: str = Field(..., min_length=1, max_length=255)
