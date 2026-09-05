"""Analytics service for project trends, agent performance, velocity."""

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.delivery.models import Feature, Task, TaskClaim


class AnalyticsService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_project_trends(self, project_id: str, weeks: int = 8) -> list[dict[str, Any]]:
        """Task completion rate over time."""
        now = datetime.now(UTC)
        start = now - timedelta(weeks=weeks)

        tasks = (
            self._session.query(Task)
            .join(Feature, Task.feature_id == Feature.id)
            .filter(Feature.project_id == project_id)
            .all()
        )

        weekly: dict[str, dict[str, int]] = {}
        for i in range(weeks):
            week_start = now - timedelta(weeks=i + 1)
            key = week_start.strftime("%Y-W%W")
            weekly[key] = {"completed": 0, "created": 0}

        for t in tasks:
            if t.created_at and t.created_at >= start:
                key = t.created_at.strftime("%Y-W%W")
                if key in weekly:
                    weekly[key]["created"] += 1
            if t.status == "done" and t.updated_at and t.updated_at >= start:
                key = t.updated_at.strftime("%Y-W%W")
                if key in weekly:
                    weekly[key]["completed"] += 1

        return [
            {"week": k, "completed": v["completed"], "created": v["created"]}
            for k, v in sorted(weekly.items())
        ]

    def get_agent_performance(self, agent_id: str | None = None) -> list[dict[str, Any]]:
        """Agent performance: tasks completed, success rate, avg claim time."""
        query = self._session.query(TaskClaim)
        if agent_id:
            query = query.filter(TaskClaim.agent_id == agent_id)

        claims = query.all()

        agent_stats: dict[str, dict[str, Any]] = {}
        for c in claims:
            aid = c.agent_id
            if aid not in agent_stats:
                agent_stats[aid] = {"total": 0, "completed": 0, "durations": []}
            agent_stats[aid]["total"] += 1

            task = self._session.get(Task, c.task_id)
            if task and task.status == "done":
                agent_stats[aid]["completed"] += 1
                if c.claimed_at and task.updated_at:
                    dur = (task.updated_at - c.claimed_at).total_seconds() / 3600
                    agent_stats[aid]["durations"].append(dur)

        return [
            {
                "agent_id": aid,
                "total_claims": s["total"],
                "completed": s["completed"],
                "success_rate": round(s["completed"] / s["total"] * 100, 1) if s["total"] else 0,
                "avg_hours": round(sum(s["durations"]) / len(s["durations"]), 1)
                if s["durations"]
                else None,
            }
            for aid, s in sorted(agent_stats.items())
        ]

    def get_team_velocity(self, project_id: str, weeks: int = 8) -> list[dict[str, Any]]:
        """Tasks completed per week for a project."""
        now = datetime.now(UTC)
        tasks = (
            self._session.query(Task)
            .join(Feature, Task.feature_id == Feature.id)
            .filter(Feature.project_id == project_id)
            .filter(Task.status == "done")
            .all()
        )

        weekly: dict[str, int] = {}
        for i in range(weeks):
            week_start = now - timedelta(weeks=i + 1)
            weekly[week_start.strftime("%Y-W%W")] = 0

        for t in tasks:
            if t.updated_at and t.updated_at >= now - timedelta(weeks=weeks):
                key = t.updated_at.strftime("%Y-W%W")
                if key in weekly:
                    weekly[key] += 1

        return [{"week": k, "count": v} for k, v in sorted(weekly.items())]

    def get_global_velocity(
        self, weeks: int = 8, project_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Tasks completed per week, optionally scoped to project."""
        now = datetime.now(UTC)
        query = self._session.query(Task).filter(Task.status == "done")
        if project_id:
            query = query.join(Feature, Task.feature_id == Feature.id).filter(
                Feature.project_id == project_id,
            )

        tasks = query.all()

        weekly: dict[str, int] = {}
        for i in range(weeks):
            week_start = now - timedelta(weeks=i + 1)
            weekly[week_start.strftime("%Y-W%W")] = 0

        for t in tasks:
            if t.updated_at and t.updated_at >= now - timedelta(weeks=weeks):
                key = t.updated_at.strftime("%Y-W%W")
                if key in weekly:
                    weekly[key] += 1

        return [{"week": k, "count": v} for k, v in sorted(weekly.items())]

    def get_health_history(self, project_id: str, days: int = 30) -> list[dict[str, Any]]:
        """Health score over time (simplified: tasks by status per day)."""
        now = datetime.now(UTC)
        tasks = (
            self._session.query(Task)
            .join(Feature, Task.feature_id == Feature.id)
            .filter(Feature.project_id == project_id)
            .all()
        )

        daily: dict[str, dict[str, int]] = {}
        for i in range(days):
            d = (now - timedelta(days=i)).strftime("%Y-%m-%d")
            daily[d] = {"done": 0, "total": 0}

        for t in tasks:
            if t.created_at and t.created_at >= now - timedelta(days=days):
                d = t.created_at.strftime("%Y-%m-%d")
                if d in daily:
                    daily[d]["total"] += 1
            if t.status == "done" and t.updated_at and t.updated_at >= now - timedelta(days=days):
                d = t.updated_at.strftime("%Y-%m-%d")
                if d in daily:
                    daily[d]["done"] += 1

        return [
            {
                "date": k,
                "completed": v["done"],
                "created": v["total"],
                "score": round(v["done"] / v["total"] * 100) if v["total"] else 100,
            }
            for k, v in sorted(daily.items())
        ]

    def get_agents_overview(self) -> list[dict[str, Any]]:
        """All agents summary."""
        return self.get_agent_performance()
