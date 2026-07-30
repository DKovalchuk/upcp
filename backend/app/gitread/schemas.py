from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ProviderType = Literal["github", "gitlab", "bitbucket", "local", "other"]


class GitProviderCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    provider_type: ProviderType
    url: str = Field(..., min_length=1, max_length=2048)


class GitLinkCreate(BaseModel):
    entity_type: str = Field(..., min_length=1, max_length=255)
    entity_id: str = Field(..., min_length=1, max_length=255)
    git_type: str = Field(..., min_length=1, max_length=255)
    git_id: str = Field(..., min_length=1, max_length=255)
