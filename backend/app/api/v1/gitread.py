from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.gitread.schemas import GitLinkCreate, GitProviderCreate
from app.gitread.service import (
    GitBranchService,
    GitCommitService,
    GitLinkService,
    GitProviderService,
)
from app.shared.database import get_session

router = APIRouter(tags=["gitread"])


@router.post("/projects/{project_id}/git-providers", status_code=201)
def create_provider(
    project_id: str, body: GitProviderCreate, session: Session = Depends(get_session)
) -> dict[str, str]:  # noqa: B008
    svc = GitProviderService(session)
    gp = svc.create(
        project_id=project_id, name=body.name, provider_type=body.provider_type, url=body.url
    )
    return {
        "id": gp.id,
        "name": gp.name,
        "provider_type": gp.provider_type,
        "url": gp.url,
        "status": gp.status,
    }


@router.get("/git-providers/{provider_id}")
def get_provider(provider_id: str, session: Session = Depends(get_session)) -> dict[str, str]:  # noqa: B008
    gp = GitProviderService(session).get(provider_id)
    return {
        "id": gp.id,
        "name": gp.name,
        "provider_type": gp.provider_type,
        "url": gp.url,
        "status": gp.status,
    }


@router.get("/projects/{project_id}/git-providers")
def list_providers(
    project_id: str, session: Session = Depends(get_session)
) -> list[dict[str, str]]:  # noqa: B008
    items = GitProviderService(session).list_by_project(project_id)
    return [
        {
            "id": p.id,
            "name": p.name,
            "provider_type": p.provider_type,
            "url": p.url,
            "status": p.status,
        }
        for p in items
    ]


@router.delete("/git-providers/{provider_id}", status_code=204)
def delete_provider(provider_id: str, session: Session = Depends(get_session)) -> None:  # noqa: B008
    GitProviderService(session).delete(provider_id)


@router.get("/git-providers/{provider_id}/branches")
def list_branches(
    provider_id: str, session: Session = Depends(get_session)
) -> list[dict[str, str | bool | None]]:  # noqa: B008
    items = GitBranchService(session).list_by_provider(provider_id)
    return [
        {
            "id": b.id,
            "name": b.name,
            "last_commit_sha": b.last_commit_sha,
            "is_default": b.is_default,
        }
        for b in items
    ]


@router.get("/git-providers/{provider_id}/commits")
def list_commits(
    provider_id: str, limit: int = Query(20), session: Session = Depends(get_session)
) -> list[dict[str, str | int]]:  # noqa: B008
    items = GitCommitService(session).list_by_provider(provider_id, limit=limit)
    return [
        {
            "id": c.id,
            "sha": c.sha,
            "message": c.message,
            "author": c.author,
            "committed_at": c.committed_at.isoformat(),
        }
        for c in items
    ]


@router.post("/git-links", status_code=201)
def create_link(body: GitLinkCreate, session: Session = Depends(get_session)) -> dict[str, str]:  # noqa: B008
    link = GitLinkService(session).create(
        entity_type=body.entity_type,
        entity_id=body.entity_id,
        git_type=body.git_type,
        git_id=body.git_id,
    )
    return {
        "id": link.id,
        "entity_type": link.entity_type,
        "entity_id": link.entity_id,
        "git_type": link.git_type,
        "git_id": link.git_id,
    }


@router.get("/git-links")
def list_links(
    entity_type: str = Query(...),
    entity_id: str = Query(...),
    session: Session = Depends(get_session),
) -> list[dict[str, str]]:  # noqa: B008
    items = GitLinkService(session).list_by_entity(entity_type, entity_id)
    return [
        {
            "id": link.id,
            "entity_type": link.entity_type,
            "entity_id": link.entity_id,
            "git_type": link.git_type,
            "git_id": link.git_id,
        }
        for link in items
    ]


@router.delete("/git-links/{link_id}", status_code=204)
def delete_link(link_id: str, session: Session = Depends(get_session)) -> None:  # noqa: B008
    GitLinkService(session).delete(link_id)
