"""Dashboard service for aggregated statistics."""

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.audit.models import AuditEvent
from app.delivery.models import Heartbeat, Task, TaskClaim
from app.identity.agents import Agent
from app.projects.models import Project
from app.shared.text import utcnow


def _ensure_aware(dt: datetime | None) -> datetime | None:
    """Ensure a datetime is timezone-aware (UTC). SQLite returns naive datetimes."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def _is_stale(last_heartbeat_at: datetime | None, threshold: datetime) -> bool:
    """Check if a heartbeat is stale (older than threshold)."""
    aware = _ensure_aware(last_heartbeat_at)
    return aware is not None and aware < threshold


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

    def active_agents(self) -> list[dict[str, object]]:
        """Get active agents with their current task, progress, and heartbeat status.

        Returns a list of dicts, one per active TaskClaim, with agent info,
        task info, latest heartbeat data, and a staleness flag (heartbeat > 7 min).
        """
        now = utcnow()
        stale_threshold = now - timedelta(minutes=7)

        # Subquery: latest heartbeat id per claim
        latest_hb_sq = (
            self._session.query(
                Heartbeat.claim_id,
                func.max(Heartbeat.id).label("latest_hb_id"),
            )
            .group_by(Heartbeat.claim_id)
            .subquery()
        )

        rows = (
            self._session.query(
                Agent.id.label("agent_id"),
                Agent.name.label("agent_name"),
                Task.id.label("task_id"),
                Task.title.label("task_title"),
                TaskClaim.claimed_at,
                TaskClaim.last_heartbeat_at,
                Heartbeat.progress_percent,
                Heartbeat.current_step,
            )
            .join(TaskClaim, TaskClaim.agent_id == Agent.id)
            .join(Task, Task.id == TaskClaim.task_id)
            .outerjoin(latest_hb_sq, latest_hb_sq.c.claim_id == TaskClaim.id)
            .outerjoin(Heartbeat, Heartbeat.id == latest_hb_sq.c.latest_hb_id)
            .filter(TaskClaim.state == "active")
            .all()
        )

        return [
            {
                "agent_id": row.agent_id,
                "agent_name": row.agent_name,
                "task_id": row.task_id,
                "task_title": row.task_title,
                "claimed_at": row.claimed_at.isoformat() if row.claimed_at else None,
                "last_heartbeat_at": (
                    row.last_heartbeat_at.isoformat() if row.last_heartbeat_at else None
                ),
                "progress_percent": row.progress_percent or 0,
                "current_step": row.current_step or "",
                "is_stale": _is_stale(row.last_heartbeat_at, stale_threshold),
            }
            for row in rows
        ]
