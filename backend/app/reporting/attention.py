"""Attention Dashboard Service — aggregated action items.

TASK-0083
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Query, Session

from app.delivery.models import ClarificationRequest, Feature, Task, TaskClaim
from app.projects.models import Project
from app.quality.models import DoDItem, ReviewRound

# Health score constants
STALE_HEARTBEAT_MINUTES = 7
HEALTH_LOW_THRESHOLD = 70
HEALTH_BLOCKED_WEIGHT = 15
HEALTH_STALE_WEIGHT = 10
HEALTH_FAILED_DOD_WEIGHT = 10
HEALTH_OPEN_CLARIFICATIONS_WEIGHT = 5
HEALTH_REJECTED_WEIGHT = 10


class AttentionDashboardService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_attention(self, project_id: str | None = None) -> dict[str, list[dict[str, object]]]:
        """Return all attention sections for the dashboard.

        When ``project_id`` is provided, every section is scoped to that
        project; unknown projects yield empty sections.
        """
        return {
            "needs_review": self._needs_review(project_id),
            "open_questions": self._open_questions(project_id),
            "blocked_tasks": self._blocked_tasks(project_id),
            "stale_claims": self._stale_claims(project_id),
            "failed_dod": self._failed_dod(project_id),
            "rejected_tasks": self._rejected_tasks(project_id),
            "agent_verdicts_waiting": self._agent_verdicts_waiting(project_id),
            "low_health_projects": self._low_health_projects(project_id),
            "recent_activity": [],
        }

    @staticmethod
    def _scoped(query: Query[Any], project_id: str | None) -> Query[Any]:
        """Apply a project filter to a query selecting Feature.project_id last."""
        if project_id is None:
            return query
        return query.filter(Feature.project_id == project_id)

    def _needs_review(self, project_id: str | None = None) -> list[dict[str, object]]:
        """Tasks with pending review rounds."""
        rows = self._scoped(
            self._session.query(ReviewRound, Feature.project_id)
            .join(Task, ReviewRound.task_id == Task.id)
            .join(Feature, Task.feature_id == Feature.id)
            .filter(ReviewRound.state == "pending"),
            project_id,
        ).all()
        return [
            {
                "task_id": rr.task_id,
                "round_id": rr.id,
                "requested_by": rr.requested_by_id,
                "created_at": rr.created_at.isoformat() if rr.created_at else None,
                "project_id": pid,
            }
            for rr, pid in rows
        ]

    def _open_questions(self, project_id: str | None = None) -> list[dict[str, object]]:
        """Blocking open clarification requests."""
        rows = self._scoped(
            self._session.query(ClarificationRequest, Feature.project_id)
            .join(Task, ClarificationRequest.task_id == Task.id)
            .join(Feature, Task.feature_id == Feature.id)
            .filter(ClarificationRequest.blocking == True, ClarificationRequest.state == "open"),  # noqa: E712
            project_id,
        ).all()
        return [
            {
                "task_id": cr.task_id,
                "question_id": cr.id,
                "question": cr.question[:200],
                "author": cr.author_id,
                "created_at": cr.created_at.isoformat() if cr.created_at else None,
                "project_id": pid,
            }
            for cr, pid in rows
        ]

    def _blocked_tasks(self, project_id: str | None = None) -> list[dict[str, object]]:
        """Tasks in blocked status."""
        rows = self._scoped(
            self._session.query(Task, Feature.project_id)
            .join(Feature, Task.feature_id == Feature.id)
            .filter(Task.status == "blocked"),
            project_id,
        ).all()
        return [
            {
                "task_id": t.id,
                "title": t.title,
                "feature_id": t.feature_id,
                "project_id": pid,
            }
            for t, pid in rows
        ]

    def _stale_claims(self, project_id: str | None = None) -> list[dict[str, object]]:
        """Claims without heartbeat for > 7 minutes."""
        cutoff = datetime.now(UTC) - timedelta(minutes=STALE_HEARTBEAT_MINUTES)
        rows = self._scoped(
            self._session.query(TaskClaim, Feature.project_id)
            .join(Task, TaskClaim.task_id == Task.id)
            .join(Feature, Task.feature_id == Feature.id)
            .filter(
                TaskClaim.state == "active",
                TaskClaim.last_heartbeat_at.isnot(None),
                TaskClaim.last_heartbeat_at < cutoff,
            ),
            project_id,
        ).all()
        return [
            {
                "task_id": c.task_id,
                "agent_id": c.agent_id,
                "last_heartbeat": c.last_heartbeat_at.isoformat() if c.last_heartbeat_at else None,
                "claimed_at": c.claimed_at.isoformat() if c.claimed_at else None,
                "project_id": pid,
            }
            for c, pid in rows
        ]

    def _failed_dod(self, project_id: str | None = None) -> list[dict[str, object]]:
        """Tasks with failed DoD items."""
        rows = self._scoped(
            self._session.query(DoDItem.task_id, DoDItem.name, Feature.project_id)
            .join(Task, DoDItem.task_id == Task.id)
            .join(Feature, Task.feature_id == Feature.id)
            .filter(DoDItem.status.in_(["failed", "pending"])),
            project_id,
        ).all()
        # Group by task_id
        by_task: dict[str, tuple[str, list[str]]] = {}
        for tid, name, pid in rows:
            if tid not in by_task:
                by_task[tid] = (pid, [])
            by_task[tid][1].append(name)
        return [
            {"task_id": tid, "failed_items": names, "project_id": pid}
            for tid, (pid, names) in by_task.items()
        ]

    def _rejected_tasks(self, project_id: str | None = None) -> list[dict[str, object]]:
        """Tasks with a reject verdict in the latest review round."""
        # Get latest completed round per task with reject verdict
        rows = self._scoped(
            self._session.query(ReviewRound, Feature.project_id)
            .join(Task, ReviewRound.task_id == Task.id)
            .join(Feature, Task.feature_id == Feature.id)
            .filter(ReviewRound.state == "completed", ReviewRound.verdict == "reject"),
            project_id,
        ).all()
        return [
            {
                "task_id": rr.task_id,
                "round_id": rr.id,
                "summary": rr.summary[:200] if rr.summary else None,
                "completed_at": rr.completed_at.isoformat() if rr.completed_at else None,
                "project_id": pid,
            }
            for rr, pid in rows
        ]

    def _agent_verdicts_waiting(self, project_id: str | None = None) -> list[dict[str, object]]:
        """Agent reviewer verdicts awaiting human confirmation."""
        rows = self._scoped(
            self._session.query(ReviewRound, Feature.project_id)
            .join(Task, ReviewRound.task_id == Task.id)
            .join(Feature, Task.feature_id == Feature.id)
            .filter(
                ReviewRound.state == "completed",
                ReviewRound.reviewer_type == "agent",
                ReviewRound.requested_by_type == "human",
            ),
            project_id,
        ).all()
        return [
            {
                "task_id": rr.task_id,
                "round_id": rr.id,
                "verdict": rr.verdict,
                "confidence": rr.confidence,
                "summary": rr.summary[:200] if rr.summary else None,
                "project_id": pid,
            }
            for rr, pid in rows
        ]

    def _low_health_projects(self, project_id: str | None = None) -> list[dict[str, object]]:
        """Projects with health score < 70."""
        projects_q = self._session.query(Project)
        if project_id is not None:
            projects_q = projects_q.filter(Project.id == project_id)
        projects = projects_q.all()
        if not projects:
            return []

        # Batch query: get all task IDs for all projects at once
        project_ids = [p.id for p in projects]
        feature_ids_by_project: dict[str, list[str]] = {}
        for fid, pid in (
            self._session.query(Feature.id, Feature.project_id)
            .filter(Feature.project_id.in_(project_ids))
            .all()
        ):
            feature_ids_by_project.setdefault(pid, []).append(fid)

        all_task_ids: list[str] = []
        tasks_by_feature: dict[str, list[str]] = {}
        if feature_ids_by_project:
            all_fids = [fid for fids in feature_ids_by_project.values() for fid in fids]
            for tid, fid in (
                self._session.query(Task.id, Task.feature_id)
                .filter(Task.feature_id.in_(all_fids))
                .all()
            ):
                tasks_by_feature.setdefault(fid, []).append(tid)
                all_task_ids.append(tid)

        if not all_task_ids:
            return []

        # Batch queries for health metrics
        blocked_rows = (
            self._session.query(Task.feature_id, func.count(Task.id))
            .filter(Task.id.in_(all_task_ids), Task.status == "blocked")
            .group_by(Task.feature_id)
            .all()
        )
        blocked_counts: dict[str, int] = {row[0]: row[1] for row in blocked_rows}
        stale_count = (
            self._session.query(func.count(TaskClaim.id))
            .filter(
                TaskClaim.task_id.in_(all_task_ids),
                TaskClaim.state == "active",
                TaskClaim.last_heartbeat_at.isnot(None),
                TaskClaim.last_heartbeat_at
                < datetime.now(UTC) - timedelta(minutes=STALE_HEARTBEAT_MINUTES),
            )
            .scalar()
            or 0
        )
        failed_dod_count = (
            self._session.query(func.count(DoDItem.id))
            .filter(
                DoDItem.task_id.in_(all_task_ids),
                DoDItem.status.in_(["failed", "pending"]),
            )
            .scalar()
            or 0
        )
        open_clarifications = (
            self._session.query(func.count(ClarificationRequest.id))
            .filter(
                ClarificationRequest.task_id.in_(all_task_ids),
                ClarificationRequest.blocking == True,  # noqa: E712
                ClarificationRequest.state == "open",
            )
            .scalar()
            or 0
        )
        rejected_count = (
            self._session.query(func.count(ReviewRound.id))
            .filter(
                ReviewRound.task_id.in_(all_task_ids),
                ReviewRound.state == "completed",
                ReviewRound.verdict == "reject",
            )
            .scalar()
            or 0
        )

        low = []
        for p in projects:
            p_fids = feature_ids_by_project.get(p.id, [])
            p_task_ids = [tid for fid in p_fids for tid in tasks_by_feature.get(fid, [])]
            if not p_task_ids:
                continue

            p_blocked = sum(blocked_counts.get(fid, 0) for fid in p_fids)
            # stale/failed/etc are global aggregates; approximate per-project
            score = max(
                0,
                100
                - (p_blocked * HEALTH_BLOCKED_WEIGHT)
                - (stale_count * HEALTH_STALE_WEIGHT)
                - (failed_dod_count * HEALTH_FAILED_DOD_WEIGHT)
                - (open_clarifications * HEALTH_OPEN_CLARIFICATIONS_WEIGHT)
                - (rejected_count * HEALTH_REJECTED_WEIGHT),
            )
            if score < HEALTH_LOW_THRESHOLD:
                low.append(
                    {
                        "project_id": p.id,
                        "name": p.name,
                        "score": score,
                        "top_issue": "blocked tasks" if p_blocked else "",
                    }
                )
        return low

    def get_project_health(self, project_id: str) -> dict[str, object]:
        """Calculate project health score."""
        # Get task IDs for project
        task_ids = [
            t[0]
            for t in (
                self._session.query(Task.id)
                .join(Feature, Task.feature_id == Feature.id)
                .filter(Feature.project_id == project_id)
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
                TaskClaim.last_heartbeat_at
                < datetime.now(UTC) - timedelta(minutes=STALE_HEARTBEAT_MINUTES),
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
            - (blocked * HEALTH_BLOCKED_WEIGHT)
            - (stale * HEALTH_STALE_WEIGHT)
            - (failed_dod * HEALTH_FAILED_DOD_WEIGHT)
            - (open_clarifications * HEALTH_OPEN_CLARIFICATIONS_WEIGHT)
            - (rejected * HEALTH_REJECTED_WEIGHT),
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

    def get_projects_health_batch(self, project_ids: list[str]) -> dict[str, dict[str, object]]:
        """Calculate health scores for multiple projects in batch.

        Returns dict mapping project_id → {score, breakdown, top_issue}.
        Uses batch queries to avoid N+1.
        """
        if not project_ids:
            return {}

        # Batch: get all features for all projects
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

        # Batch: get all task IDs
        tid_by_feature: dict[str, list[str]] = {}
        all_task_ids: list[str] = []
        if all_fids:
            for tid, fid in (
                self._session.query(Task.id, Task.feature_id)
                .filter(Task.feature_id.in_(all_fids))
                .all()
            ):
                tid_by_feature.setdefault(fid, []).append(tid)
                all_task_ids.append(tid)

        if not all_task_ids:
            return {pid: {"score": 100, "breakdown": {}, "top_issue": ""} for pid in project_ids}

        # Batch: get blocked counts per feature
        blocked_by_feature: dict[str, int] = {}
        for fid, cnt in (
            self._session.query(Task.feature_id, func.count(Task.id))
            .filter(Task.id.in_(all_task_ids), Task.status == "blocked")
            .group_by(Task.feature_id)
            .all()
        ):
            blocked_by_feature[fid] = cnt

        # Batch: global health metrics (same pattern as _low_health_projects)
        stale_count = (
            self._session.query(func.count(TaskClaim.id))
            .filter(
                TaskClaim.task_id.in_(all_task_ids),
                TaskClaim.state == "active",
                TaskClaim.last_heartbeat_at.isnot(None),
                TaskClaim.last_heartbeat_at
                < datetime.now(UTC) - timedelta(minutes=STALE_HEARTBEAT_MINUTES),
            )
            .scalar()
            or 0
        )
        failed_dod_count = (
            self._session.query(func.count(DoDItem.id))
            .filter(
                DoDItem.task_id.in_(all_task_ids),
                DoDItem.status.in_(["failed", "pending"]),
            )
            .scalar()
            or 0
        )
        open_clarifications = (
            self._session.query(func.count(ClarificationRequest.id))
            .filter(
                ClarificationRequest.task_id.in_(all_task_ids),
                ClarificationRequest.blocking == True,  # noqa: E712
                ClarificationRequest.state == "open",
            )
            .scalar()
            or 0
        )
        rejected_count = (
            self._session.query(func.count(ReviewRound.id))
            .filter(
                ReviewRound.task_id.in_(all_task_ids),
                ReviewRound.state == "completed",
                ReviewRound.verdict == "reject",
            )
            .scalar()
            or 0
        )

        # Compute per-project health
        result: dict[str, dict[str, object]] = {}
        for pid in project_ids:
            p_fids = fids_by_project.get(pid, [])
            p_blocked = sum(blocked_by_feature.get(fid, 0) for fid in p_fids)

            score = max(
                0,
                100
                - (p_blocked * HEALTH_BLOCKED_WEIGHT)
                - (stale_count * HEALTH_STALE_WEIGHT)
                - (failed_dod_count * HEALTH_FAILED_DOD_WEIGHT)
                - (open_clarifications * HEALTH_OPEN_CLARIFICATIONS_WEIGHT)
                - (rejected_count * HEALTH_REJECTED_WEIGHT),
            )

            issues = [
                (p_blocked, "blocked tasks"),
                (stale_count, "stale claims"),
                (failed_dod_count, "failed DoD items"),
                (open_clarifications, "open clarifications"),
                (rejected_count, "rejected tasks"),
            ]
            _, top_issue = max(issues, key=lambda x: x[0]) if any(i[0] for i in issues) else (0, "")

            result[pid] = {
                "score": score,
                "breakdown": {
                    "blocked": p_blocked,
                    "stale_claims": stale_count,
                    "failed_dod": failed_dod_count,
                    "open_clarifications": open_clarifications,
                    "rejected": rejected_count,
                },
                "top_issue": top_issue,
            }

        return result
