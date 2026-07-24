from sqlalchemy.orm import Session

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
