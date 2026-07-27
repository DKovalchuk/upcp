"""Attention Dashboard Service — aggregated action items.

TASK-0083
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.delivery.models import ClarificationRequest, Task, TaskClaim
from app.projects.models import Project
from app.quality.models import DoDItem, ReviewRound


class AttentionDashboardService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_attention(self) -> dict[str, list[dict[str, object]]]:
        """Return all attention sections for the dashboard."""
        return {
            "needs_review": self._needs_review(),
            "open_questions": self._open_questions(),
            "blocked_tasks": self._blocked_tasks(),
            "stale_claims": self._stale_claims(),
            "failed_dod": self._failed_dod(),
            "rejected_tasks": self._rejected_tasks(),
            "agent_verdicts_waiting": self._agent_verdicts_waiting(),
            "low_health_projects": self._low_health_projects(),
            "recent_activity": [],
        }

    def _needs_review(self) -> list[dict[str, object]]:
        """Tasks with pending review rounds."""
        rounds = self._session.query(ReviewRound).filter_by(state="pending").all()
        return [
            {
                "task_id": rr.task_id,
                "round_id": rr.id,
                "requested_by": rr.requested_by_id,
                "created_at": rr.created_at.isoformat() if rr.created_at else None,
            }
            for rr in rounds
        ]

    def _open_questions(self) -> list[dict[str, object]]:
        """Blocking open clarification requests."""
        questions = (
            self._session.query(ClarificationRequest).filter_by(blocking=True, state="open").all()
        )
        return [
            {
                "task_id": cr.task_id,
                "question_id": cr.id,
                "question": cr.question[:200],
                "author": cr.author_id,
                "created_at": cr.created_at.isoformat() if cr.created_at else None,
            }
            for cr in questions
        ]

    def _blocked_tasks(self) -> list[dict[str, object]]:
        """Tasks in blocked status."""
        tasks = self._session.query(Task).filter_by(status="blocked").all()
        return [
            {
                "task_id": t.id,
                "title": t.title,
                "feature_id": t.feature_id,
            }
            for t in tasks
        ]

    def _stale_claims(self) -> list[dict[str, object]]:
        """Claims without heartbeat for > 7 minutes."""
        cutoff = datetime.now(UTC) - timedelta(minutes=7)
        claims = (
            self._session.query(TaskClaim)
            .filter_by(state="active")
            .filter(
                TaskClaim.last_heartbeat_at.isnot(None),
                TaskClaim.last_heartbeat_at < cutoff,
            )
            .all()
        )
        return [
            {
                "task_id": c.task_id,
                "agent_id": c.agent_id,
                "last_heartbeat": c.last_heartbeat_at.isoformat() if c.last_heartbeat_at else None,
                "claimed_at": c.claimed_at.isoformat() if c.claimed_at else None,
            }
            for c in claims
        ]

    def _failed_dod(self) -> list[dict[str, object]]:
        """Tasks with failed DoD items."""
        failed = (
            self._session.query(DoDItem).filter(DoDItem.status.in_(["failed", "pending"])).all()
        )
        # Group by task_id
        by_task: dict[str, list[str]] = {}
        for d in failed:
            by_task.setdefault(d.task_id, []).append(d.name)
        return [{"task_id": tid, "failed_items": names} for tid, names in by_task.items()]

    def _rejected_tasks(self) -> list[dict[str, object]]:
        """Tasks with a reject verdict in the latest review round."""
        # Get latest completed round per task with reject verdict
        rounds = (
            self._session.query(ReviewRound).filter_by(state="completed", verdict="reject").all()
        )
        return [
            {
                "task_id": rr.task_id,
                "round_id": rr.id,
                "summary": rr.summary[:200] if rr.summary else None,
                "completed_at": rr.completed_at.isoformat() if rr.completed_at else None,
            }
            for rr in rounds
        ]

    def _agent_verdicts_waiting(self) -> list[dict[str, object]]:
        """Agent reviewer verdicts awaiting human confirmation."""
        rounds = (
            self._session.query(ReviewRound)
            .filter(
                ReviewRound.state == "completed",
                ReviewRound.reviewer_type == "agent",
                ReviewRound.requested_by_type == "human",
            )
            .all()
        )
        return [
            {
                "task_id": rr.task_id,
                "round_id": rr.id,
                "verdict": rr.verdict,
                "confidence": rr.confidence,
                "summary": rr.summary[:200] if rr.summary else None,
            }
            for rr in rounds
        ]

    def _low_health_projects(self) -> list[dict[str, object]]:
        """Projects with health score < 70."""
        projects = self._session.query(Project).all()
        low = []
        for p in projects:
            health = self.get_project_health(p.id)
            if int(str(health["score"])) < 70:
                low.append(
                    {
                        "project_id": p.id,
                        "name": p.name,
                        "score": health["score"],
                        "top_issue": health.get("top_issue", ""),
                    }
                )
        return low

    def get_project_health(self, project_id: str) -> dict[str, object]:
        """Calculate project health score."""
        # Get task IDs for project
        from app.delivery.models import Feature as FeatureModel

        task_ids = [
            t[0]
            for t in (
                self._session.query(Task.id)
                .join(FeatureModel, Task.feature_id == FeatureModel.id)
                .filter(FeatureModel.project_id == project_id)
                .all()
            )
        ]

        if not task_ids:
            return {"score": 100, "breakdown": {}, "top_issue": ""}

        blocked = (
            self._session.query(Task)
            .filter(Task.id.in_(task_ids), Task.status == "blocked")
            .count()
        )

        stale = (
            self._session.query(TaskClaim)
            .filter(
                TaskClaim.task_id.in_(task_ids),
                TaskClaim.state == "active",
                TaskClaim.last_heartbeat_at.isnot(None),
                TaskClaim.last_heartbeat_at < datetime.now(UTC) - timedelta(minutes=7),
            )
            .count()
        )

        failed_dod = (
            self._session.query(DoDItem)
            .filter(
                DoDItem.task_id.in_(task_ids),
                DoDItem.status.in_(["failed", "pending"]),
            )
            .count()
        )

        open_clarifications = (
            self._session.query(ClarificationRequest)
            .filter(
                ClarificationRequest.task_id.in_(task_ids),
                ClarificationRequest.blocking == True,  # noqa: E712
                ClarificationRequest.state == "open",
            )
            .count()
        )

        rejected = (
            self._session.query(ReviewRound)
            .filter(
                ReviewRound.task_id.in_(task_ids),
                ReviewRound.state == "completed",
                ReviewRound.verdict == "reject",
            )
            .count()
        )

        score = max(
            0,
            100
            - (blocked * 15)
            - (stale * 10)
            - (failed_dod * 10)
            - (open_clarifications * 5)
            - (rejected * 10),
        )

        # Determine top issue
        issues = [
            (blocked, "blocked tasks"),
            (stale, "stale claims"),
            (failed_dod, "failed DoD items"),
            (open_clarifications, "open clarifications"),
            (rejected, "rejected tasks"),
        ]
        top_count, top_issue = (
            max(issues, key=lambda x: x[0]) if any(i[0] for i in issues) else (0, "")
        )

        return {
            "score": score,
            "breakdown": {
                "blocked": blocked,
                "stale_claims": stale,
                "failed_dod": failed_dod,
                "open_clarifications": open_clarifications,
                "rejected": rejected,
            },
            "top_issue": top_issue,
        }
