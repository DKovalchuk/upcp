"""Portfolio Service — aggregate stats across all projects.

TASK-0087
"""

from sqlalchemy.orm import Session

from app.delivery.models import Feature, Task
from app.projects.models import Project
from app.reporting.attention import AttentionDashboardService


class PortfolioService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_overview(self) -> dict[str, object]:
        """Return portfolio-level overview with per-project summaries.

        Uses batch queries to avoid N+1: one query for projects,
        one for all features, one for all tasks, one batch health call.
        """
        projects = self._session.query(Project).all()
        if not projects:
            return {
                "total_projects": 0,
                "total_tasks": 0,
                "tasks_by_status": {},
                "projects": [],
            }

        project_ids = [p.id for p in projects]

        # Batch query: all features for all projects at once
        feature_rows = (
            self._session.query(Feature.id, Feature.project_id)
            .filter(Feature.project_id.in_(project_ids))
            .all()
        )
        fids_by_project: dict[str, list[str]] = {}
        all_fids: list[str] = []
        for fid, pid in feature_rows:
            fids_by_project.setdefault(pid, []).append(fid)
            all_fids.append(fid)

        # Batch query: all tasks for all features at once
        tasks_by_feature: dict[str, int] = {}
        total_tasks = 0
        tasks_by_status: dict[str, int] = {}
        if all_fids:
            task_rows = (
                self._session.query(Task.feature_id, Task.status)
                .filter(Task.feature_id.in_(all_fids))
                .all()
            )
            for fid, status in task_rows:
                tasks_by_feature[fid] = tasks_by_feature.get(fid, 0) + 1
                total_tasks += 1
                tasks_by_status[status] = tasks_by_status.get(status, 0) + 1

        # Batch health query for all projects at once
        attn_svc = AttentionDashboardService(self._session)
        health_batch = attn_svc.get_projects_health_batch(project_ids)

        # Build per-project summaries
        project_summaries: list[dict[str, object]] = []
        for p in projects:
            p_fids = fids_by_project.get(p.id, [])
            p_task_count = sum(tasks_by_feature.get(fid, 0) for fid in p_fids)
            health = health_batch.get(p.id, {"score": 100, "top_issue": ""})
            project_summaries.append(
                {
                    "id": p.id,
                    "name": p.name,
                    "slug": p.slug,
                    "task_count": p_task_count,
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
