import logging

from sqlalchemy.orm import Session

from app.delivery.models import Feature, Subtask, Task
from app.shared.errors import Conflict, NotFound
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
        self, project_id: str, *, offset: int = 0, limit: int = 20
    ) -> tuple[list[Feature], int]:
        q = self._session.query(Feature).filter_by(project_id=project_id)
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
            try:
                from app.reporting.trigger import NotificationTrigger

                NotificationTrigger(self._session).trigger(
                    "task.status_changed",
                    entity_type="task",
                    entity_id=task_id,
                    actor_id=str(fields.get("assignee_id", "system")),
                    metadata={
                        "old_status": old_status,
                        "new_status": str(new_status),
                        "task_title": t.title,
                    },
                )
            except Exception:  # noqa: BLE001
                logger.warning("Notification trigger failed for task.status_changed", exc_info=True)

        return t

    def delete(self, task_id: str) -> None:
        t = self.get(task_id)
        self._session.delete(t)
        self._session.flush()

    def list_tasks(
        self, feature_id: str, *, offset: int = 0, limit: int = 20
    ) -> tuple[list[Task], int]:
        q = self._session.query(Task).filter_by(feature_id=feature_id)
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
