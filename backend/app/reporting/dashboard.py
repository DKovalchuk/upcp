"""Dashboard service for aggregated statistics."""

from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.audit.models import AuditEvent
from app.delivery.models import Task
from app.projects.models import Project


class DashboardService:
    """Service for dashboard statistics."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_stats(self) -> dict[str, Any]:
        """Get aggregated dashboard statistics."""
        # Project count
        project_count = self._session.query(Project).count()

        # Task counts by status
        task_counts = self._get_task_counts_by_status()

        # Recent projects (last 5)
        recent_projects = self._get_recent_projects(limit=5)

        # Recent activity (last 10 audit events)
        recent_activity = self._get_recent_activity(limit=10)

        return {
            "project_count": project_count,
            "task_counts_by_status": task_counts,
            "recent_projects": recent_projects,
            "recent_activity": recent_activity,
        }

    def _get_task_counts_by_status(self) -> dict[str, int]:
        """Get task counts grouped by status."""
        rows = self._session.query(Task.status, func.count(Task.id)).group_by(Task.status).all()
        counts = {row[0]: row[1] for row in rows}

        # Ensure all expected statuses are present
        return {
            "backlog": counts.get("backlog", 0),
            "in_progress": counts.get("in_progress", 0),
            "review": counts.get("review", 0),
            "done": counts.get("done", 0),
        }

    def _get_recent_projects(self, limit: int = 5) -> list[dict[str, object]]:
        """Get recent projects ordered by updated_at desc."""
        projects = (
            self._session.query(Project).order_by(Project.updated_at.desc()).limit(limit).all()
        )

        return [
            {
                "id": p.id,
                "name": p.name,
                "slug": p.slug,
                "description": p.description,
                "status": p.status,
                "created_at": p.created_at.isoformat(),
                "updated_at": p.updated_at.isoformat(),
            }
            for p in projects
        ]

    def _get_recent_activity(self, limit: int = 10) -> list[dict[str, object]]:
        """Get recent audit events ordered by timestamp desc."""
        events = (
            self._session.query(AuditEvent).order_by(AuditEvent.timestamp.desc()).limit(limit).all()
        )

        return [
            {
                "id": e.id,
                "timestamp": e.timestamp.isoformat(),
                "event_type": e.event_type,
                "entity_type": e.entity_type,
                "entity_id": e.entity_id,
                "actor_type": e.actor_type,
                "actor_id": e.actor_id,
                "payload": e.payload,
                "note": e.note,
            }
            for e in events
        ]
