from pydantic import BaseModel


class GitProviderCreate(BaseModel):
    name: str
    provider_type: str
    url: str


class GitLinkCreate(BaseModel):
    entity_type: str
    entity_id: str
    git_type: str
    git_id: str
