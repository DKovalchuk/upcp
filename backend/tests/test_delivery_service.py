"""Unit tests for delivery service layer.

Tests FeatureService, TaskService, SubtaskService directly against a database session.
Uses the shared db_session fixture from conftest.py.
"""

import pytest
from app.delivery.lifecycle import InvalidTransition
from app.delivery.service import FeatureService, SubtaskService, TaskService
from app.projects.models import Project
from app.quality.models import DoDItem
from app.quality.service import QualityError
from app.shared.errors import Conflict, NotFound
from app.shared.text import slugify
from sqlalchemy.orm import Session


def _make_project(session: Session, name: str = "Test Project") -> Project:
    """Create a project for testing."""
    p = Project(name=name, slug=slugify(name), description=f"Test project {name}")
    session.add(p)
    session.flush()
    return p


# ── FeatureService Tests ──────────────────────────────────────────────────────


class TestFeatureService:
    def test_create_feature(self, db_session: Session) -> None:
        """Feature can be created with required fields."""
        project = _make_project(db_session)
        fs = FeatureService(db_session)
        feature = fs.create(project_id=str(project.id), name="Auth")
        assert feature.name == "Auth"
        assert feature.slug == "auth"
        assert feature.status == "backlog"
        assert feature.project_id == str(project.id)
        assert feature.id is not None

    def test_create_feature_with_custom_slug(self, db_session: Session) -> None:
        """Feature can be created with a custom slug."""
        project = _make_project(db_session)
        fs = FeatureService(db_session)
        feature = fs.create(project_id=str(project.id), name="Auth", slug="custom-slug")
        assert feature.slug == "custom-slug"

    def test_create_feature_duplicate_slug_raises_conflict(self, db_session: Session) -> None:
        """Creating a feature with duplicate slug in same project raises Conflict."""
        project = _make_project(db_session)
        fs = FeatureService(db_session)
        fs.create(project_id=str(project.id), name="Auth")
        db_session.commit()
        with pytest.raises(Conflict, match="slug 'auth' already exists"):
            fs.create(project_id=str(project.id), name="Auth")

    def test_get_feature(self, db_session: Session) -> None:
        """Feature can be retrieved by ID."""
        project = _make_project(db_session)
        fs = FeatureService(db_session)
        feature = fs.create(project_id=str(project.id), name="Auth")
        retrieved = fs.get(str(feature.id))
        assert retrieved.id == feature.id
        assert retrieved.name == "Auth"

    def test_get_feature_not_found(self, db_session: Session) -> None:
        """Getting a non-existent feature raises NotFound."""
        fs = FeatureService(db_session)
        with pytest.raises(NotFound, match="feature 'nonexistent' not found"):
            fs.get("nonexistent")

    def test_update_feature(self, db_session: Session) -> None:
        """Feature fields can be updated."""
        project = _make_project(db_session)
        fs = FeatureService(db_session)
        feature = fs.create(project_id=str(project.id), name="Auth")
        updated = fs.update(str(feature.id), name="Authentication", status="in_progress")
        assert updated.name == "Authentication"
        assert updated.status == "in_progress"

    def test_delete_feature(self, db_session: Session) -> None:
        """Feature can be deleted."""
        project = _make_project(db_session)
        fs = FeatureService(db_session)
        feature = fs.create(project_id=str(project.id), name="Auth")
        fs.delete(str(feature.id))
        with pytest.raises(NotFound):
            fs.get(str(feature.id))

    def test_list_features(self, db_session: Session) -> None:
        """Features can be listed with pagination."""
        project = _make_project(db_session)
        fs = FeatureService(db_session)
        for i in range(5):
            fs.create(project_id=str(project.id), name=f"Feature {i}")
        features, total = fs.list_features(str(project.id), offset=0, limit=3)
        assert total == 5
        assert len(features) == 3
        # Second page
        features2, total2 = fs.list_features(str(project.id), offset=3, limit=3)
        assert total2 == 5
        assert len(features2) == 2


# ── TaskService Tests ─────────────────────────────────────────────────────────


class TestTaskService:
    def test_create_task(self, db_session: Session) -> None:
        """Task can be created with required fields."""
        project = _make_project(db_session)
        fs = FeatureService(db_session)
        feature = fs.create(project_id=str(project.id), name="Auth")
        ts = TaskService(db_session)
        task = ts.create(feature_id=str(feature.id), title="Implement login")
        assert task.title == "Implement login"
        assert task.status == "backlog"
        assert task.priority == 0
        assert task.feature_id == str(feature.id)
        assert task.id is not None

    def test_get_task(self, db_session: Session) -> None:
        """Task can be retrieved by ID."""
        project = _make_project(db_session)
        fs = FeatureService(db_session)
        feature = fs.create(project_id=str(project.id), name="Auth")
        ts = TaskService(db_session)
        task = ts.create(feature_id=str(feature.id), title="Implement login")
        retrieved = ts.get(str(task.id))
        assert retrieved.id == task.id
        assert retrieved.title == "Implement login"

    def test_get_task_not_found(self, db_session: Session) -> None:
        """Getting a non-existent task raises NotFound."""
        ts = TaskService(db_session)
        with pytest.raises(NotFound, match="task 'nonexistent' not found"):
            ts.get("nonexistent")

    def test_update_task(self, db_session: Session) -> None:
        """Task fields can be updated."""
        project = _make_project(db_session)
        fs = FeatureService(db_session)
        feature = fs.create(project_id=str(project.id), name="Auth")
        ts = TaskService(db_session)
        task = ts.create(feature_id=str(feature.id), title="Implement login")
        updated = ts.update(str(task.id), title="Implement login flow", priority=1)
        assert updated.title == "Implement login flow"
        assert updated.priority == 1

    def test_update_task_invalid_transition(self, db_session: Session) -> None:
        """Invalid status transition raises InvalidTransition."""
        project = _make_project(db_session)
        fs = FeatureService(db_session)
        feature = fs.create(project_id=str(project.id), name="Auth")
        ts = TaskService(db_session)
        task = ts.create(feature_id=str(feature.id), title="Implement login")
        # backlog -> done is invalid
        with pytest.raises(InvalidTransition):
            ts.update(str(task.id), status="done")

    def test_delete_task(self, db_session: Session) -> None:
        """Task can be deleted."""
        project = _make_project(db_session)
        fs = FeatureService(db_session)
        feature = fs.create(project_id=str(project.id), name="Auth")
        ts = TaskService(db_session)
        task = ts.create(feature_id=str(feature.id), title="Implement login")
        ts.delete(str(task.id))
        with pytest.raises(NotFound):
            ts.get(str(task.id))

    def test_list_tasks(self, db_session: Session) -> None:
        """Tasks can be listed with pagination."""
        project = _make_project(db_session)
        fs = FeatureService(db_session)
        feature = fs.create(project_id=str(project.id), name="Auth")
        ts = TaskService(db_session)
        for i in range(5):
            ts.create(feature_id=str(feature.id), title=f"Task {i}")
        tasks, total = ts.list_tasks(str(feature.id), offset=0, limit=3)
        assert total == 5
        assert len(tasks) == 3

    def test_list_tasks_by_project(self, db_session: Session) -> None:
        """Tasks can be listed across features of a project."""
        project = _make_project(db_session)
        fs = FeatureService(db_session)
        f1 = fs.create(project_id=str(project.id), name="Auth")
        f2 = fs.create(project_id=str(project.id), name="Payment")
        ts = TaskService(db_session)
        ts.create(feature_id=str(f1.id), title="Task 1")
        ts.create(feature_id=str(f1.id), title="Task 2")
        ts.create(feature_id=str(f2.id), title="Task 3")
        tasks, total = ts.list_tasks_by_project(str(project.id))
        assert total == 3
        assert len(tasks) == 3

    def test_list_tasks_by_project_with_status_filter(self, db_session: Session) -> None:
        """list_tasks_by_project filters by status."""
        project = _make_project(db_session)
        fs = FeatureService(db_session)
        feature = fs.create(project_id=str(project.id), name="Auth")
        ts = TaskService(db_session)
        ts.create(feature_id=str(feature.id), title="Backlog task", status="backlog")
        ts.create(feature_id=str(feature.id), title="Done task", status="done")
        tasks, total = ts.list_tasks_by_project(str(project.id), status="backlog")
        assert total == 1
        assert tasks[0].title == "Backlog task"

    def test_list_tasks_by_project_with_feature_filter(self, db_session: Session) -> None:
        """list_tasks_by_project filters by feature_id."""
        project = _make_project(db_session)
        fs = FeatureService(db_session)
        f1 = fs.create(project_id=str(project.id), name="Auth")
        f2 = fs.create(project_id=str(project.id), name="Payment")
        ts = TaskService(db_session)
        ts.create(feature_id=str(f1.id), title="Task in F1")
        ts.create(feature_id=str(f2.id), title="Task in F2")
        tasks, total = ts.list_tasks_by_project(str(project.id), feature_id=str(f1.id))
        assert total == 1
        assert tasks[0].title == "Task in F1"

    def test_complete_task_without_dod_succeeds(self, db_session: Session) -> None:
        """Task can be completed when no DoD items exist."""
        project = _make_project(db_session)
        fs = FeatureService(db_session)
        feature = fs.create(project_id=str(project.id), name="Auth")
        ts = TaskService(db_session)
        task = ts.create(feature_id=str(feature.id), title="Implement login")
        completed = ts.complete(str(task.id))
        assert completed.status == "done"

    def test_complete_task_with_all_dod_passed(self, db_session: Session) -> None:
        """Task can be completed when all DoD items are passed."""
        project = _make_project(db_session)
        fs = FeatureService(db_session)
        feature = fs.create(project_id=str(project.id), name="Auth")
        ts = TaskService(db_session)
        task = ts.create(feature_id=str(feature.id), title="Implement login")
        # Create DoD items
        dod1 = DoDItem(task_id=str(task.id), name="Tests pass", status="passed")
        dod2 = DoDItem(task_id=str(task.id), name="Code reviewed", status="passed")
        db_session.add_all([dod1, dod2])
        db_session.flush()
        completed = ts.complete(str(task.id))
        assert completed.status == "done"

    def test_complete_task_fails_with_unpassed_dod(self, db_session: Session) -> None:
        """Task completion fails when some DoD items are not passed."""
        project = _make_project(db_session)
        fs = FeatureService(db_session)
        feature = fs.create(project_id=str(project.id), name="Auth")
        ts = TaskService(db_session)
        task = ts.create(feature_id=str(feature.id), title="Implement login")
        # Create DoD items with mixed status
        dod1 = DoDItem(task_id=str(task.id), name="Tests pass", status="passed")
        dod2 = DoDItem(task_id=str(task.id), name="Code reviewed", status="pending")
        db_session.add_all([dod1, dod2])
        db_session.flush()
        with pytest.raises(QualityError, match="DoD not passed"):
            ts.complete(str(task.id))

    def test_list_tasks_by_project_pagination(self, db_session: Session) -> None:
        """list_tasks_by_project respects offset/limit."""
        project = _make_project(db_session)
        fs = FeatureService(db_session)
        feature = fs.create(project_id=str(project.id), name="Auth")
        ts = TaskService(db_session)
        for i in range(5):
            ts.create(feature_id=str(feature.id), title=f"Task {i}")
        tasks, total = ts.list_tasks_by_project(str(project.id), offset=2, limit=2)
        assert total == 5
        assert len(tasks) == 2
        # Check order (by creation)
        assert tasks[0].title == "Task 2"
        assert tasks[1].title == "Task 3"


# ── SubtaskService Tests ──────────────────────────────────────────────────────


class TestSubtaskService:
    def test_create_subtask(self, db_session: Session) -> None:
        """Subtask can be created with required fields."""
        project = _make_project(db_session)
        fs = FeatureService(db_session)
        feature = fs.create(project_id=str(project.id), name="Auth")
        ts = TaskService(db_session)
        task = ts.create(feature_id=str(feature.id), title="Implement login")
        ss = SubtaskService(db_session)
        subtask = ss.create(task_id=str(task.id), title="Write unit tests")
        assert subtask.title == "Write unit tests"
        assert subtask.status == "todo"
        assert subtask.task_id == str(task.id)
        assert subtask.id is not None

    def test_get_subtask(self, db_session: Session) -> None:
        """Subtask can be retrieved by ID."""
        project = _make_project(db_session)
        fs = FeatureService(db_session)
        feature = fs.create(project_id=str(project.id), name="Auth")
        ts = TaskService(db_session)
        task = ts.create(feature_id=str(feature.id), title="Implement login")
        ss = SubtaskService(db_session)
        subtask = ss.create(task_id=str(task.id), title="Write unit tests")
        retrieved = ss.get(str(subtask.id))
        assert retrieved.id == subtask.id
        assert retrieved.title == "Write unit tests"

    def test_get_subtask_not_found(self, db_session: Session) -> None:
        """Getting a non-existent subtask raises NotFound."""
        ss = SubtaskService(db_session)
        with pytest.raises(NotFound, match="subtask 'nonexistent' not found"):
            ss.get("nonexistent")

    def test_update_subtask(self, db_session: Session) -> None:
        """Subtask fields can be updated."""
        project = _make_project(db_session)
        fs = FeatureService(db_session)
        feature = fs.create(project_id=str(project.id), name="Auth")
        ts = TaskService(db_session)
        task = ts.create(feature_id=str(feature.id), title="Implement login")
        ss = SubtaskService(db_session)
        subtask = ss.create(task_id=str(task.id), title="Write unit tests")
        updated = ss.update(str(subtask.id), status="done", description="Completed")
        assert updated.status == "done"
        assert updated.description == "Completed"

    def test_delete_subtask(self, db_session: Session) -> None:
        """Subtask can be deleted."""
        project = _make_project(db_session)
        fs = FeatureService(db_session)
        feature = fs.create(project_id=str(project.id), name="Auth")
        ts = TaskService(db_session)
        task = ts.create(feature_id=str(feature.id), title="Implement login")
        ss = SubtaskService(db_session)
        subtask = ss.create(task_id=str(task.id), title="Write unit tests")
        ss.delete(str(subtask.id))
        with pytest.raises(NotFound):
            ss.get(str(subtask.id))

    def test_list_subtasks(self, db_session: Session) -> None:
        """Subtasks can be listed with pagination."""
        project = _make_project(db_session)
        fs = FeatureService(db_session)
        feature = fs.create(project_id=str(project.id), name="Auth")
        ts = TaskService(db_session)
        task = ts.create(feature_id=str(feature.id), title="Implement login")
        ss = SubtaskService(db_session)
        for i in range(5):
            ss.create(task_id=str(task.id), title=f"Subtask {i}")
        subtasks, total = ss.list_subtasks(str(task.id), offset=0, limit=3)
        assert total == 5
        assert len(subtasks) == 3

    def test_list_subtasks_pagination(self, db_session: Session) -> None:
        """list_subtasks respects offset/limit."""
        project = _make_project(db_session)
        fs = FeatureService(db_session)
        feature = fs.create(project_id=str(project.id), name="Auth")
        ts = TaskService(db_session)
        task = ts.create(feature_id=str(feature.id), title="Implement login")
        ss = SubtaskService(db_session)
        for i in range(5):
            ss.create(task_id=str(task.id), title=f"Subtask {i}")
        subtasks, total = ss.list_subtasks(str(task.id), offset=2, limit=2)
        assert total == 5
        assert len(subtasks) == 2
        # Check order
        assert subtasks[0].title == "Subtask 2"
        assert subtasks[1].title == "Subtask 3"
