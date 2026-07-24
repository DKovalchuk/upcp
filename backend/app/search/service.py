from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.delivery.models import Feature, Task
from app.projects.models import Project


class SearchService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def search(self, query: str, limit: int = 20) -> list[dict[str, str]]:
        q = f"%{query}%"
        results: list[dict[str, str]] = []

        projects = (
            self.session.query(Project)
            .filter(or_(Project.name.ilike(q), Project.description.ilike(q)))
            .limit(limit)
            .all()
        )
        for p in projects:
            results.append(
                {"entity_type": "project", "id": p.id, "title": p.name, "subtitle": p.description or "", "url": f"/projects/{p.id}"}
            )

        remaining = limit - len(results)
        if remaining > 0:
            features = (
                self.session.query(Feature)
                .filter(or_(Feature.name.ilike(q), Feature.description.ilike(q)))
                .limit(remaining)
                .all()
            )
            for f in features:
                results.append(
                    {"entity_type": "feature", "id": f.id, "title": f.name, "subtitle": f.description or "", "url": f"/projects/{f.project_id}/delivery"}
                )

        remaining = limit - len(results)
        if remaining > 0:
            tasks = (
                self.session.query(Task)
                .filter(or_(Task.title.ilike(q), Task.description.ilike(q)))
                .limit(remaining)
                .all()
            )
            for t in tasks:
                results.append(
                    {"entity_type": "task", "id": t.id, "title": t.title, "subtitle": t.description or "", "url": f"/projects/{t.feature_id}/delivery"}
                )

        return results
