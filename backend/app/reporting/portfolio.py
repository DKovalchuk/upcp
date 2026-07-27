"""Portfolio Service — aggregate stats across all projects.

TASK-0087
"""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.delivery.models import Feature, Task
from app.projects.models import Project
from app.reporting.attention import AttentionDashboardService


class PortfolioService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_overview(self) -> dict[str, object]:
        """Return portfolio-level overview with per-project summaries."""
        projects = self._session.query(Project).all()
        attn_svc = AttentionDashboardService(self._session)

        project_summaries: list[dict[str, object]] = []
        total_tasks = 0
        tasks_by_status: dict[str, int] = {}

        for p in projects:
            feature_ids = [
                f[0]
                for f in self._session.query(Feature.id).filter(Feature.project_id == p.id).all()
            ]

            task_count = 0
            project_status_counts: dict[str, int] = {}
            if feature_ids:
                rows = (
                    self._session.query(Task.status, func.count(Task.id))
                    .filter(Task.feature_id.in_(feature_ids))
                    .group_by(Task.status)
                    .all()
                )
                project_status_counts = {row[0]: row[1] for row in rows}
                task_count = sum(project_status_counts.values())

            total_tasks += task_count
            for status, count in project_status_counts.items():
                tasks_by_status[status] = tasks_by_status.get(status, 0) + count

            health = attn_svc.get_project_health(p.id)
            project_summaries.append(
                {
                    "id": p.id,
                    "name": p.name,
                    "slug": p.slug,
                    "task_count": task_count,
                    "health_score": health["score"],
                    "top_issue": health.get("top_issue", ""),
                }
            )

        return {
            "total_projects": len(projects),
            "total_tasks": total_tasks,
            "tasks_by_status": tasks_by_status,
            "projects": project_summaries,
        }
