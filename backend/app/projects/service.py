from sqlalchemy.orm import Session

from app.projects.models import Project
from app.shared.errors import Conflict, NotFound
from app.shared.text import slugify


class ProjectService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        *,
        name: str,
        slug: str | None = None,
        description: str | None = None,
        status: str = "active",
    ) -> Project:
        final_slug = slug or slugify(name)
        existing = self._session.query(Project).filter_by(slug=final_slug).first()
        if existing:
            raise Conflict(f"slug '{final_slug}' already exists")
        project = Project(name=name, slug=final_slug, description=description, status=status)
        self._session.add(project)
        self._session.flush()
        return project

    def get(self, project_id: str) -> Project:
        project = self._session.get(Project, project_id)
        if not project:
            raise NotFound(f"project '{project_id}' not found")
        return project

    def update(self, project_id: str, **fields: str | None) -> Project:
        project = self.get(project_id)
        if "slug" in fields and fields["slug"] is not None:
            existing = (
                self._session.query(Project)
                .filter(Project.slug == fields["slug"], Project.id != project_id)
                .first()
            )
            if existing:
                raise Conflict(f"slug '{fields['slug']}' already exists")
        for key, value in fields.items():
            if value is not None:
                setattr(project, key, value)
        self._session.flush()
        return project

    def delete(self, project_id: str) -> None:
        project = self.get(project_id)
        self._session.delete(project)
        self._session.flush()

    _ALLOWED_SORT_FIELDS = {"created_at", "updated_at", "name", "status"}

    def list_projects(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        status: str | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
    ) -> tuple[list[Project], int]:
        q = self._session.query(Project)
        if status:
            q = q.filter(Project.status == status)
        if search:
            q = q.filter(Project.name.ilike(f"%{search}%"))
        total = q.count()
        if sort_by not in self._ALLOWED_SORT_FIELDS:
            sort_by = "created_at"
        col = getattr(Project, sort_by)
        q = q.order_by(col.asc() if sort_dir == "asc" else col.desc())
        projects = q.offset(offset).limit(limit).all()
        return projects, total
