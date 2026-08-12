import logging
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.delivery.models import Feature, Task
from app.projects.models import Project
from app.quality.models import (
    AcceptanceCriterion,
    DoDItem,
    Evidence,
    ReviewFinding,
    ReviewRound,
)
from app.shared.errors import AppError, Conflict, NotFound
from app.shared.text import utcnow

logger = logging.getLogger(__name__)


class QualityError(AppError):
    error_code = "dod_failed"
    status_code = 400


# Valid state transitions for evidence verification.
_EVIDENCE_TRANSITIONS: dict[str, set[str]] = {
    "unverified": {"agent_verified", "human_accepted", "rejected"},
    "agent_verified": {"human_accepted", "rejected"},
    "human_accepted": set(),
    "rejected": set(),
    "stale": {"unverified"},
}


class EvidenceService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        *,
        task_id: str,
        type: str,
        title: str,
        created_by_type: str,
        created_by_id: str,
        description: str | None = None,
        url: str | None = None,
        content_snippet: str | None = None,
        artifact_ref: str | None = None,
        dod_item_id: str | None = None,
    ) -> Evidence:
        e = Evidence(
            task_id=task_id,
            type=type,
            title=title,
            description=description,
            url=url,
            content_snippet=content_snippet,
            artifact_ref=artifact_ref,
            created_by_type=created_by_type,
            created_by_id=created_by_id,
            dod_item_id=dod_item_id,
        )
        self._session.add(e)
        self._session.flush()

        try:
            from app.reporting.trigger import NotificationTrigger

            NotificationTrigger(self._session).trigger(
                "evidence.attached",
                entity_type="task",
                entity_id=task_id,
                actor_id=created_by_id,
                metadata={"evidence_title": title},
            )
        except Exception:  # noqa: BLE001
            logger.warning("Notification trigger failed for evidence.attached", exc_info=True)

        return e

    def get(self, evidence_id: str) -> Evidence:
        e = self._session.get(Evidence, evidence_id)
        if not e:
            raise NotFound(f"evidence '{evidence_id}' not found")
        return e

    def list_by_task(
        self, task_id: str, *, offset: int = 0, limit: int = 100
    ) -> tuple[list[Evidence], int]:
        q = self._session.query(Evidence).filter_by(task_id=task_id)
        total = q.count()
        return q.offset(offset).limit(limit).all(), total

    def _transition(self, evidence: Evidence, target: str, by_type: str, by_id: str) -> None:
        allowed = _EVIDENCE_TRANSITIONS.get(evidence.verification_state, set())
        if target not in allowed:
            raise Conflict(
                f"Cannot transition evidence from '{evidence.verification_state}' to '{target}'"
            )
        evidence.verification_state = target
        evidence.verified_by_type = by_type
        evidence.verified_by_id = by_id
        evidence.verified_at = utcnow()
        self._session.flush()

    def verify(self, evidence_id: str, *, verified_by_type: str, verified_by_id: str) -> Evidence:
        e = self.get(evidence_id)
        self._transition(e, "agent_verified", verified_by_type, verified_by_id)
        return e

    def accept(self, evidence_id: str, *, verified_by_type: str, verified_by_id: str) -> Evidence:
        e = self.get(evidence_id)
        self._transition(e, "human_accepted", verified_by_type, verified_by_id)
        return e

    def reject(self, evidence_id: str, *, verified_by_type: str, verified_by_id: str) -> Evidence:
        e = self.get(evidence_id)
        self._transition(e, "rejected", verified_by_type, verified_by_id)
        return e


# Valid state transitions for review rounds.
_REVIEW_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"in_progress", "cancelled"},
    "in_progress": {"completed", "cancelled"},
    "completed": set(),
    "cancelled": set(),
}


class ReviewRoundService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        *,
        task_id: str,
        requested_by_type: str,
        requested_by_id: str,
        reviewer_type: str | None = None,
        reviewer_id: str | None = None,
    ) -> ReviewRound:
        rr = ReviewRound(
            task_id=task_id,
            requested_by_type=requested_by_type,
            requested_by_id=requested_by_id,
            reviewer_type=reviewer_type,
            reviewer_id=reviewer_id,
        )
        self._session.add(rr)
        self._session.flush()
        return rr

    def get(self, round_id: str) -> ReviewRound:
        rr = self._session.get(ReviewRound, round_id)
        if not rr:
            raise NotFound(f"review round '{round_id}' not found")
        return rr

    def list_by_task(
        self, task_id: str, *, offset: int = 0, limit: int = 100
    ) -> tuple[list[ReviewRound], int]:
        q = self._session.query(ReviewRound).filter_by(task_id=task_id)
        total = q.count()
        return q.offset(offset).limit(limit).all(), total

    def start(self, round_id: str) -> ReviewRound:
        rr = self.get(round_id)
        allowed = _REVIEW_TRANSITIONS.get(rr.state, set())
        if "in_progress" not in allowed:
            raise Conflict(f"Cannot start review round in state '{rr.state}'")
        rr.state = "in_progress"
        rr.started_at = utcnow()
        self._session.flush()
        return rr

    def add_finding(
        self,
        round_id: str,
        *,
        severity: str,
        category: str,
        message: str,
        evidence_id: str | None = None,
        dod_item_id: str | None = None,
        suggestion: str | None = None,
    ) -> ReviewFinding:
        rr = self.get(round_id)
        if rr.state not in ("pending", "in_progress"):
            raise Conflict(f"Cannot add finding to review round in state '{rr.state}'")
        f = ReviewFinding(
            review_round_id=round_id,
            severity=severity,
            category=category,
            message=message,
            evidence_id=evidence_id,
            dod_item_id=dod_item_id,
            suggestion=suggestion,
        )
        self._session.add(f)
        self._session.flush()
        return f

    def submit_verdict(
        self,
        round_id: str,
        *,
        verdict: str,
        confidence: int,
        summary: str,
    ) -> ReviewRound:
        rr = self.get(round_id)
        allowed = _REVIEW_TRANSITIONS.get(rr.state, set())
        if "completed" not in allowed:
            raise Conflict(f"Cannot submit verdict for review round in state '{rr.state}'")
        rr.state = "completed"
        rr.verdict = verdict
        rr.confidence = confidence
        rr.summary = summary
        rr.completed_at = utcnow()
        self._session.flush()

        try:
            from app.reporting.trigger import NotificationTrigger

            event_type = "review.completed" if verdict == "approve" else "review.rejected"
            NotificationTrigger(self._session).trigger(
                event_type,
                entity_type="task",
                entity_id=rr.task_id,
                actor_id=rr.reviewer_id or "system",
                metadata={"verdict": verdict},
            )
        except Exception:  # noqa: BLE001
            logger.warning("Notification trigger failed for review event", exc_info=True)

        return rr

    def list_findings(self, round_id: str) -> list[ReviewFinding]:
        return self._session.query(ReviewFinding).filter_by(review_round_id=round_id).all()


class ReviewGateError(AppError):
    error_code = "review_gate_failed"
    status_code = 400


class ReviewGateService:
    """Quality gate that blocks task review submission when criteria not met."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def submit_for_review(
        self,
        task_id: str,
        *,
        requested_by_type: str,
        requested_by_id: str,
        reviewer_type: str | None = None,
        reviewer_id: str | None = None,
    ) -> ReviewRound:
        """Submit task for review after passing quality gate checks.

        Checks:
        1. Task must be in claimed or in_progress state.
        2. All DoDItems must be passed (or no DoDItems exist).
        3. Required evidence types must be satisfied.
        4. No blocking clarification requests must be open.
        """
        from app.delivery.models import ClarificationRequest, Task

        task = self._session.get(Task, task_id)
        if task is None:
            raise NotFound(f"task '{task_id}' not found")

        errors: list[str] = []

        # 1. Task status check
        if task.status not in ("claimed", "in_progress", "ready_for_review"):
            errors.append(
                f"invalid_task_status: task is '{task.status}', must be 'claimed' or 'in_progress'"
            )

        # 2. DoD satisfaction
        from app.quality.models import DoDItem

        dod_items = self._session.query(DoDItem).filter_by(task_id=task_id).all()
        failed_dods = [d for d in dod_items if d.status != "passed"]
        if failed_dods:
            names = ", ".join(d.name for d in failed_dods)
            errors.append(f"dod_not_satisfied: {names}")

        # 3. Required evidence types
        from app.quality.models import Evidence

        required_dods = [d for d in dod_items if d.required_evidence_type]
        if required_dods:
            existing_evidence = self._session.query(Evidence).filter_by(task_id=task_id).all()
            existing_types = {e.type for e in existing_evidence}
            for d in required_dods:
                if d.required_evidence_type not in existing_types:
                    errors.append(
                        f"evidence_required: DoD '{d.name}' requires "
                        f"'{d.required_evidence_type}' evidence"
                    )

        # 4. Blocking clarifications
        blocking = (
            self._session.query(ClarificationRequest)
            .filter_by(task_id=task_id, blocking=True, state="open")
            .first()
        )
        if blocking:
            errors.append(f"clarification_blocking: '{blocking.question[:80]}'")

        if errors:
            raise ReviewGateError("; ".join(errors))

        # Create review round
        rr_svc = ReviewRoundService(self._session)
        return rr_svc.create(
            task_id=task_id,
            requested_by_type=requested_by_type,
            requested_by_id=requested_by_id,
            reviewer_type=reviewer_type,
            reviewer_id=reviewer_id,
        )


class AcceptanceCriterionService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, *, task_id: str, description: str) -> AcceptanceCriterion:
        ac = AcceptanceCriterion(task_id=task_id, description=description)
        self._session.add(ac)
        self._session.flush()
        return ac

    def get(self, ac_id: str) -> AcceptanceCriterion:
        ac = self._session.get(AcceptanceCriterion, ac_id)
        if not ac:
            raise NotFound(f"acceptance criterion '{ac_id}' not found")
        return ac

    def update(self, ac_id: str, **fields: str | None) -> AcceptanceCriterion:
        ac = self.get(ac_id)
        for k, v in fields.items():
            if v is not None:
                setattr(ac, k, v)
        self._session.flush()
        return ac

    def delete(self, ac_id: str) -> None:
        ac = self.get(ac_id)
        self._session.delete(ac)
        self._session.flush()

    def list_by_task(
        self, task_id: str, *, offset: int = 0, limit: int = 100
    ) -> tuple[list[AcceptanceCriterion], int]:
        q = self._session.query(AcceptanceCriterion).filter_by(task_id=task_id)
        total = q.count()
        return q.offset(offset).limit(limit).all(), total


class DoDItemService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, *, task_id: str, name: str) -> DoDItem:
        item = DoDItem(task_id=task_id, name=name)
        self._session.add(item)
        self._session.flush()
        return item

    def get(self, item_id: str) -> DoDItem:
        item = self._session.get(DoDItem, item_id)
        if not item:
            raise NotFound(f"doD item '{item_id}' not found")
        return item

    def update(self, item_id: str, **fields: str | None) -> DoDItem:
        item = self.get(item_id)
        for k, v in fields.items():
            if v is not None:
                setattr(item, k, v)
        self._session.flush()
        return item

    def delete(self, item_id: str) -> None:
        item = self.get(item_id)
        self._session.delete(item)
        self._session.flush()

    def list_by_task(
        self, task_id: str, *, offset: int = 0, limit: int = 100
    ) -> tuple[list[DoDItem], int]:
        q = self._session.query(DoDItem).filter_by(task_id=task_id)
        total = q.count()
        return q.offset(offset).limit(limit).all(), total


class QualityStatsService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_quality_stats(self, project_id: str) -> dict[str, Any]:
        """
        Aggregate quality statistics for a project.

        Returns:
            dict with keys: total_tasks, tasks_with_ac, total_ac, passed_ac,
                           total_dod, passed_dod, pass_rate

        Raises:
            NotFound: if project does not exist
        """
        # Verify project exists
        project = self._session.get(Project, project_id)
        if not project:
            raise NotFound(f"project '{project_id}' not found")

        # Get all task IDs for the project
        task_ids = (
            self._session.query(Task.id)
            .join(Feature, Task.feature_id == Feature.id)
            .filter(Feature.project_id == project_id)
            .all()
        )
        task_id_list = [t[0] for t in task_ids]

        if not task_id_list:
            return {
                "total_tasks": 0,
                "tasks_with_ac": 0,
                "total_ac": 0,
                "passed_ac": 0,
                "total_dod": 0,
                "passed_dod": 0,
                "pass_rate": 0.0,
            }

        # Count tasks with acceptance criteria
        tasks_with_ac = (
            self._session.query(func.count(func.distinct(AcceptanceCriterion.task_id)))
            .filter(AcceptanceCriterion.task_id.in_(task_id_list))
            .scalar()
        )

        # Count total and passed acceptance criteria
        ac_stats = (
            self._session.query(
                func.count(AcceptanceCriterion.id),
                func.count(AcceptanceCriterion.id).filter(AcceptanceCriterion.status == "passed"),
            )
            .filter(AcceptanceCriterion.task_id.in_(task_id_list))
            .one()
        )
        total_ac, passed_ac = ac_stats

        # Count total and passed DoD items
        dod_stats = (
            self._session.query(
                func.count(DoDItem.id),
                func.count(DoDItem.id).filter(DoDItem.status == "passed"),
            )
            .filter(DoDItem.task_id.in_(task_id_list))
            .one()
        )
        total_dod, passed_dod = dod_stats

        # Calculate pass rate
        total_items = total_ac + total_dod
        passed_items = passed_ac + passed_dod
        pass_rate = (passed_items / total_items * 100) if total_items > 0 else 0.0

        return {
            "total_tasks": len(task_id_list),
            "tasks_with_ac": tasks_with_ac,
            "total_ac": total_ac,
            "passed_ac": passed_ac,
            "total_dod": total_dod,
            "passed_dod": passed_dod,
            "pass_rate": round(pass_rate, 2),
        }
