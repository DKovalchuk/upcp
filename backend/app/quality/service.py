from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.delivery.models import Feature, Task
from app.projects.models import Project
from app.quality.models import AcceptanceCriterion, DoDItem
from app.shared.errors import AppError, NotFound


class QualityError(AppError):
    error_code = "dod_failed"
    status_code = 400


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

    def list_by_task(self, task_id: str) -> list[AcceptanceCriterion]:
        return self._session.query(AcceptanceCriterion).filter_by(task_id=task_id).all()


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

    def list_by_task(self, task_id: str) -> list[DoDItem]:
        return self._session.query(DoDItem).filter_by(task_id=task_id).all()


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
