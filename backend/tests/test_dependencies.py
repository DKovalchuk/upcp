"""Tests for TaskDependency model — TASK-0073."""

import pytest
from app.delivery.models import Feature, Task, TaskDependency  # noqa: F401
from app.projects.models import Project  # noqa: F401
from app.shared.database import Base
from sqlalchemy.exc import IntegrityError

from tests.conftest import _test_engine, _TestSession


@pytest.fixture()
def _db():
    import app.audit.models  # noqa: F401
    import app.delivery.models  # noqa: F401
    import app.gitread.models  # noqa: F401
    import app.identity.agents  # noqa: F401
    import app.identity.models  # noqa: F401
    import app.identity.rbac  # noqa: F401
    import app.projects.models  # noqa: F401
    import app.quality.models  # noqa: F401
    import app.reporting.models  # noqa: F401
    import app.structure.models  # noqa: F401

    Base.metadata.create_all(bind=_test_engine)
    yield
    Base.metadata.drop_all(bind=_test_engine)


@pytest.fixture()
def session():
    s = _TestSession()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


@pytest.fixture()
def project(session) -> Project:
    p = Project(name="Test", slug="test")
    session.add(p)
    session.flush()
    return p


@pytest.fixture()
def feature(session, project) -> Feature:
    f = Feature(project_id=project.id, name="F1", slug="f1")
    session.add(f)
    session.flush()
    return f


@pytest.fixture()
def tasks(session, feature) -> list[Task]:
    """Create 4 tasks for dependency testing."""
    tasks = []
    for i in range(4):
        t = Task(feature_id=feature.id, title=f"T{i}", status="ready")
        session.add(t)
        tasks.append(t)
    session.flush()
    return tasks


class TestTaskDependency:
    def test_create_dependency(self, _db, session, tasks):
        """TaskDependency can be created."""
        dep = TaskDependency(task_id=tasks[1].id, blocked_by_task_id=tasks[0].id)
        session.add(dep)
        session.flush()
        assert dep.id is not None
        assert dep.task_id == tasks[1].id
        assert dep.blocked_by_task_id == tasks[0].id

    def test_no_self_dependency(self, _db, session, tasks):
        """Self-dependency should fail."""
        dep = TaskDependency(task_id=tasks[0].id, blocked_by_task_id=tasks[0].id)
        session.add(dep)
        with pytest.raises(IntegrityError):
            session.flush()
        session.rollback()
        session.begin_nested()

    def test_unique_dependency_pair(self, _db, session, tasks):
        """Duplicate dependency pair should fail."""
        dep1 = TaskDependency(task_id=tasks[1].id, blocked_by_task_id=tasks[0].id)
        session.add(dep1)
        session.flush()

        dep2 = TaskDependency(task_id=tasks[1].id, blocked_by_task_id=tasks[0].id)
        session.add(dep2)
        with pytest.raises(IntegrityError):
            session.flush()
        session.rollback()
        session.begin_nested()

    def test_multiple_dependencies(self, _db, session, tasks):
        """A task can depend on multiple other tasks."""
        dep1 = TaskDependency(task_id=tasks[2].id, blocked_by_task_id=tasks[0].id)
        dep2 = TaskDependency(task_id=tasks[2].id, blocked_by_task_id=tasks[1].id)
        session.add(dep1)
        session.add(dep2)
        session.flush()

        deps = session.query(TaskDependency).filter_by(task_id=tasks[2].id).all()
        assert len(deps) == 2

    def test_circular_dependency_detection(self, _db, session, tasks):
        """Circular dependency: T0 -> T1 -> T2 -> T0."""
        from app.delivery.dependencies import detect_cycle

        dep1 = TaskDependency(task_id=tasks[1].id, blocked_by_task_id=tasks[0].id)
        dep2 = TaskDependency(task_id=tasks[2].id, blocked_by_task_id=tasks[1].id)
        dep3 = TaskDependency(task_id=tasks[0].id, blocked_by_task_id=tasks[2].id)
        session.add_all([dep1, dep2, dep3])
        session.flush()

        deps = session.query(TaskDependency).all()
        assert detect_cycle(deps) is True

    def test_no_cycle_linear_chain(self, _db, session, tasks):
        """Linear chain: T0 <- T1 <- T2 (no cycle)."""
        from app.delivery.dependencies import detect_cycle

        dep1 = TaskDependency(task_id=tasks[1].id, blocked_by_task_id=tasks[0].id)
        dep2 = TaskDependency(task_id=tasks[2].id, blocked_by_task_id=tasks[1].id)
        session.add_all([dep1, dep2])
        session.flush()

        deps = session.query(TaskDependency).all()
        assert detect_cycle(deps) is False

    def test_empty_deps_no_cycle(self, _db, session):
        """No dependencies = no cycle."""
        from app.delivery.dependencies import detect_cycle

        assert detect_cycle([]) is False
