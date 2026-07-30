from sqlalchemy.orm import Session

from app.gitread.models import GitBranch, GitCommit, GitLink, GitProvider
from app.shared.errors import NotFound


class GitProviderService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, *, project_id: str, name: str, provider_type: str, url: str) -> GitProvider:
        gp = GitProvider(project_id=project_id, name=name, provider_type=provider_type, url=url)
        self._session.add(gp)
        self._session.flush()
        return gp

    def get(self, provider_id: str) -> GitProvider:
        gp = self._session.get(GitProvider, provider_id)
        if not gp:
            raise NotFound(f"git provider '{provider_id}' not found")
        return gp

    def list_by_project(self, project_id: str) -> list[GitProvider]:
        return self._session.query(GitProvider).filter_by(project_id=project_id).all()

    def delete(self, provider_id: str) -> None:
        gp = self.get(provider_id)
        self._session.delete(gp)
        self._session.flush()

    def update(
        self,
        provider_id: str,
        *,
        name: str | None = None,
        provider_type: str | None = None,
        url: str | None = None,
    ) -> GitProvider:
        gp = self.get(provider_id)
        if name is not None:
            gp.name = name
        if provider_type is not None:
            gp.provider_type = provider_type
        if url is not None:
            gp.url = url
        self._session.flush()
        return gp


class GitBranchService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def sync_branches(self, provider_id: str, branches: list[GitBranch]) -> int:
        existing = {
            b.name: b
            for b in self._session.query(GitBranch).filter_by(provider_id=provider_id).all()
        }
        count = 0
        for b in branches:
            if b.name in existing:
                existing[b.name].last_commit_sha = b.last_commit_sha
                existing[b.name].is_default = b.is_default
            else:
                gb = GitBranch(
                    provider_id=provider_id,
                    name=b.name,
                    last_commit_sha=b.last_commit_sha,
                    is_default=b.is_default,
                )
                self._session.add(gb)
                count += 1
        self._session.flush()
        return count

    def list_by_provider(self, provider_id: str) -> list[GitBranch]:
        return self._session.query(GitBranch).filter_by(provider_id=provider_id).all()


class GitCommitService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def sync_commits(self, provider_id: str, commits: list[GitCommit]) -> int:
        existing_shas = {
            c.sha for c in self._session.query(GitCommit).filter_by(provider_id=provider_id).all()
        }
        count = 0
        for c in commits:
            if c.sha not in existing_shas:
                gc = GitCommit(
                    provider_id=provider_id,
                    sha=c.sha,
                    message=c.message,
                    author=c.author,
                    committed_at=c.committed_at,
                )
                self._session.add(gc)
                count += 1
        self._session.flush()
        return count

    def list_by_provider(self, provider_id: str, limit: int = 20) -> list[GitCommit]:
        return (
            self._session.query(GitCommit)
            .filter_by(provider_id=provider_id)
            .order_by(GitCommit.committed_at.desc())
            .limit(limit)
            .all()
        )


class GitLinkService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, *, entity_type: str, entity_id: str, git_type: str, git_id: str) -> GitLink:
        link = GitLink(
            entity_type=entity_type, entity_id=entity_id, git_type=git_type, git_id=git_id
        )
        self._session.add(link)
        self._session.flush()
        return link

    def list_by_entity(self, entity_type: str, entity_id: str) -> list[GitLink]:
        return (
            self._session.query(GitLink)
            .filter_by(entity_type=entity_type, entity_id=entity_id)
            .all()
        )

    def delete(self, link_id: str) -> None:
        link = self._session.get(GitLink, link_id)
        if not link:
            raise NotFound(f"git link '{link_id}' not found")
        self._session.delete(link)
        self._session.flush()
