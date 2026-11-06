import logging
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy.orm import Session

from app.delivery.models import (
    AgentInboxEvent,
    ClarificationRequest,
    Comment,
    Feature,
    Heartbeat,
    Subtask,
    Task,
    TaskClaim,
)
from app.shared.errors import Conflict, NotFound, ValidationError
from app.shared.events import event_bus
from app.shared.text import slugify

logger = logging.getLogger(__name__)


class FeatureService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        *,
        project_id: str,
        name: str,
        slug: str | None = None,
        description: str | None = None,
        status: str = "backlog",
        component_id: str | None = None,
    ) -> Feature:
        final_slug = slug or slugify(name)
        existing = (
            self._session.query(Feature).filter_by(project_id=project_id, slug=final_slug).first()
        )
        if existing:
            raise Conflict(f"slug '{final_slug}' already exists in project")
        f = Feature(
            project_id=project_id,
            name=name,
            slug=final_slug,
            description=description,
            status=status,
            component_id=component_id,
        )
        self._session.add(f)
        self._session.flush()
        return f

    def get(self, feature_id: str) -> Feature:
        f = self._session.get(Feature, feature_id)
        if not f:
            raise NotFound(f"feature '{feature_id}' not found")
        return f

    def update(self, feature_id: str, **fields: str | None | int) -> Feature:
        f = self.get(feature_id)
        for key, value in fields.items():
            if value is not None:
                setattr(f, key, value)
        self._session.flush()
        return f

    def delete(self, feature_id: str) -> None:
        f = self.get(feature_id)
        self._session.delete(f)
        self._session.flush()

    def list_features(
        self,
        project_id: str,
        *,
        offset: int = 0,
        limit: int = 20,
        status: str | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
    ) -> tuple[list[Feature], int]:
        q = self._session.query(Feature).filter_by(project_id=project_id)
        if status is not None:
            q = q.filter(Feature.status == status)
        if search:
            q = q.filter(Feature.name.ilike(f"%{search}%"))
        sort_col = getattr(Feature, sort_by, Feature.created_at)
        q = q.order_by(sort_col.desc() if sort_dir == "desc" else sort_col.asc())
        total = q.count()
        return q.offset(offset).limit(limit).all(), total


class TaskService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        *,
        feature_id: str,
        title: str,
        description: str | None = None,
        status: str = "backlog",
        priority: int = 0,
        assignee_type: str | None = None,
        assignee_id: str | None = None,
        component_id: str | None = None,
        module_id: str | None = None,
    ) -> Task:
        t = Task(
            feature_id=feature_id,
            title=title,
            description=description,
            status=status,
            priority=priority,
            assignee_type=assignee_type,
            assignee_id=assignee_id,
            component_id=component_id,
            module_id=module_id,
        )
        self._session.add(t)
        self._session.flush()
        return t

    def get(self, task_id: str) -> Task:
        t = self._session.get(Task, task_id)
        if not t:
            raise NotFound(f"task '{task_id}' not found")
        return t

    def update(self, task_id: str, **fields: str | None | int) -> Task:
        t = self.get(task_id)
        old_status = t.status
        new_status = fields.get("status")
        if new_status is not None and new_status != t.status:
            from app.delivery.lifecycle import validate_transition

            validate_transition(t.status, str(new_status))
        for key, value in fields.items():
            if value is not None:
                setattr(t, key, value)
        self._session.flush()

        if new_status is not None and str(new_status) != old_status:
            event_bus.publish(
                "task.status_changed",
                session=self._session,
                entity_type="task",
                entity_id=task_id,
                actor_id=str(fields.get("assignee_id", "system")),
                metadata={
                    "old_status": old_status,
                    "new_status": str(new_status),
                    "task_title": t.title,
                },
            )

        return t

    def delete(self, task_id: str) -> None:
        t = self.get(task_id)
        self._session.delete(t)
        self._session.flush()

    def bulk_update(
        self,
        task_ids: list[str],
        *,
        status: str | None = None,
        priority: int | None = None,
        assignee_type: str | None = None,
        assignee_id: str | None = None,
    ) -> int:
        """Update multiple tasks. Returns count of successfully updated tasks."""
        if not task_ids:
            return 0

        if status is not None:
            # Validate transition for first task to catch bulk-invalid transitions
            first = self._session.get(Task, task_ids[0])
            if first:
                from app.delivery.lifecycle import InvalidTransition, validate_transition

                try:
                    validate_transition(first.status, status)
                except InvalidTransition as exc:
                    raise ValidationError(str(exc)) from exc

        updated = 0
        for tid in task_ids:
            t = self._session.get(Task, tid)
            if not t:
                continue
            if status is not None:
                t.status = status
            if priority is not None:
                t.priority = priority
            if assignee_type is not None:
                t.assignee_type = assignee_type
            if assignee_id is not None:
                t.assignee_id = assignee_id
            updated += 1

        self._session.flush()
        return updated

    def list_tasks(
        self,
        feature_id: str,
        *,
        offset: int = 0,
        limit: int = 20,
        status: str | None = None,
        priority: int | None = None,
        search: str | None = None,
    ) -> tuple[list[Task], int]:
        q = self._session.query(Task).filter_by(feature_id=feature_id)
        if status is not None:
            q = q.filter(Task.status == status)
        if priority is not None:
            q = q.filter(Task.priority >= priority)
        if search:
            q = q.filter(Task.title.ilike(f"%{search}%"))
        total = q.count()
        return q.offset(offset).limit(limit).all(), total

    def list_tasks_by_project(
        self,
        project_id: str,
        *,
        offset: int = 0,
        limit: int = 20,
        status: str | None = None,
        feature_id: str | None = None,
        assignee_type: str | None = None,
        priority: int | None = None,
        search: str | None = None,
    ) -> tuple[list[Task], int]:
        """List all tasks belonging to features of a project (JOIN via Feature)."""
        q = (
            self._session.query(Task)
            .join(Feature, Task.feature_id == Feature.id)
            .filter(Feature.project_id == project_id)
        )
        if status is not None:
            q = q.filter(Task.status == status)
        if feature_id is not None:
            q = q.filter(Task.feature_id == feature_id)
        if assignee_type is not None:
            q = q.filter(Task.assignee_type == assignee_type)
        if priority is not None:
            q = q.filter(Task.priority >= priority)
        if search:
            q = q.filter(Task.title.ilike(f"%{search}%"))
        total = q.count()
        return q.offset(offset).limit(limit).all(), total

    def complete(self, task_id: str) -> Task:
        from app.quality.models import DoDItem
        from app.quality.service import QualityError

        task = self.get(task_id)
        dod_items = self._session.query(DoDItem).filter_by(task_id=task_id).all()
        if dod_items and not all(d.status == "passed" for d in dod_items):
            failed = [d.name for d in dod_items if d.status != "passed"]
            raise QualityError(f"DoD not passed: {', '.join(failed)}")
        task.status = "done"
        self._session.flush()
        return task


class SubtaskService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self, *, task_id: str, title: str, description: str | None = None, status: str = "todo"
    ) -> Subtask:
        s = Subtask(task_id=task_id, title=title, description=description, status=status)
        self._session.add(s)
        self._session.flush()
        return s

    def get(self, subtask_id: str) -> Subtask:
        s = self._session.get(Subtask, subtask_id)
        if not s:
            raise NotFound(f"subtask '{subtask_id}' not found")
        return s

    def update(self, subtask_id: str, **fields: str | None) -> Subtask:
        s = self.get(subtask_id)
        for key, value in fields.items():
            if value is not None:
                setattr(s, key, value)
        self._session.flush()
        return s

    def delete(self, subtask_id: str) -> None:
        s = self.get(subtask_id)
        self._session.delete(s)
        self._session.flush()

    def list_subtasks(
        self, task_id: str, *, offset: int = 0, limit: int = 20
    ) -> tuple[list[Subtask], int]:
        q = self._session.query(Subtask).filter_by(task_id=task_id)
        total = q.count()
        return q.offset(offset).limit(limit).all(), total


class CommentService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(
        self,
        *,
        task_id: str,
        author_type: str,
        author_id: str,
        body: str,
        parent_id: str | None = None,
    ) -> Comment:
        if parent_id:
            parent = self._session.get(Comment, parent_id)
            if not parent or parent.task_id != task_id:
                raise NotFound(f"parent comment '{parent_id}' not found")

        c = Comment(
            task_id=task_id,
            author_type=author_type,
            author_id=author_id,
            body=body,
            parent_id=parent_id,
        )
        self._session.add(c)
        self._session.flush()
        return c

    def list_by_task(self, task_id: str) -> list[Comment]:
        return (
            self._session.query(Comment)
            .filter_by(task_id=task_id)
            .order_by(Comment.created_at.asc())
            .all()
        )


class AgentActivityService:
    """Read-only agent activity views over delivery-owned data — TASK-0176.

    Public read surface consumed by ``identity/agent_endpoints.py`` and
    ``api/v1/agent_self.py``: claims, heartbeats, tasks, inbox events and
    clarification requests of a single agent. Every query stays inside the
    delivery context; consumers use this service instead of importing
    ``delivery.models`` (AGENTS §5). Pure reads — no auth/ownership
    semantics (that stays with the consuming route's gates).
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def count_claims(self, agent_id: str, *, state: str | None = None) -> int:
        """Count task claims of an agent, optionally filtered by claim state."""
        q = self._session.query(TaskClaim).filter(TaskClaim.agent_id == agent_id)
        if state is not None:
            q = q.filter(TaskClaim.state == state)
        return q.count()

    def get_active_claim(self, agent_id: str) -> TaskClaim | None:
        """The agent's current active claim, if any."""
        return (
            self._session.query(TaskClaim)
            .filter(TaskClaim.agent_id == agent_id, TaskClaim.state == "active")
            .first()
        )

    def last_claimed_at(self, agent_id: str) -> datetime | None:
        """Most recent claim time of the agent (activity marker), if any."""
        row = (
            self._session.query(TaskClaim.claimed_at)
            .filter(TaskClaim.agent_id == agent_id)
            .order_by(TaskClaim.claimed_at.desc())
            .first()
        )
        return row[0] if row is not None else None

    def list_claims(self, agent_id: str, *, limit: int = 100) -> list[TaskClaim]:
        """Claims of an agent, newest first."""
        return (
            self._session.query(TaskClaim)
            .filter(TaskClaim.agent_id == agent_id)
            .order_by(TaskClaim.claimed_at.desc())
            .limit(limit)
            .all()
        )

    def get_latest_heartbeat(self, claim_id: str) -> Heartbeat | None:
        """Most recent heartbeat of a claim, if any."""
        return (
            self._session.query(Heartbeat)
            .filter(Heartbeat.claim_id == claim_id)
            .order_by(Heartbeat.created_at.desc())
            .first()
        )

    def list_tasks_by_ids(self, task_ids: Sequence[str]) -> list[Task]:
        """Batch task lookup (no N+1); unknown ids are simply absent."""
        if not task_ids:
            return []
        return self._session.query(Task).filter(Task.id.in_(list(task_ids))).all()

    def list_inbox_events(
        self, agent_id: str, *, unread_only: bool = False, limit: int = 50
    ) -> list[AgentInboxEvent]:
        """Inbox events of an agent, newest first."""
        q = self._session.query(AgentInboxEvent).filter(AgentInboxEvent.agent_id == agent_id)
        if unread_only:
            q = q.filter(AgentInboxEvent.is_read.is_(False))
        return q.order_by(AgentInboxEvent.created_at.desc()).limit(limit).all()

    def list_clarifications(
        self, author_id: str, *, limit: int = 100
    ) -> list[ClarificationRequest]:
        """Clarification requests authored by one agent/user, newest first.

        No ``author_type`` filter — parity with the agent detail tab, which
        lists every clarification the author id matches.
        """
        return (
            self._session.query(ClarificationRequest)
            .filter(ClarificationRequest.author_id == author_id)
            .order_by(ClarificationRequest.created_at.desc())
            .limit(limit)
            .all()
        )

    def count_clarifications(
        self,
        author_id: str,
        *,
        author_type: str | None = None,
        state: str | None = None,
    ) -> int:
        """Count clarification requests authored by one agent/user."""
        q = self._session.query(ClarificationRequest).filter(
            ClarificationRequest.author_id == author_id
        )
        if author_type is not None:
            q = q.filter(ClarificationRequest.author_type == author_type)
        if state is not None:
            q = q.filter(ClarificationRequest.state == state)
        return q.count()
