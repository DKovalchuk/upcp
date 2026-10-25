"""Unit tests for TaskService lifecycle enforcement — TASK-0099 B4."""

import pytest
from app.delivery.lifecycle import InvalidTransition
from app.delivery.models import Feature, Task  # noqa: F401
from app.delivery.service import TaskService
from app.projects.models import Project  # noqa: F401
from app.shared.database import Base
from app.shared.errors import NotFound

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

    Base.metadata.drop_all(bind=_test_engine)
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


class TestTaskServiceUpdateLifecycle:
    def test_valid_transition_passes(self, _db, session, feature):
        t = Task(feature_id=feature.id, title="T1", status="backlog")
        session.add(t)
        session.flush()

        svc = TaskService(session)
        result = svc.update(t.id, status="ready")
        assert result.status == "ready"

    def test_invalid_transition_raises(self, _db, session, feature):
        t = Task(feature_id=feature.id, title="T1", status="backlog")
        session.add(t)
        session.flush()

        svc = TaskService(session)
        with pytest.raises(InvalidTransition):
            svc.update(t.id, status="done")

    def test_same_status_no_validate(self, _db, session, feature):
        t = Task(feature_id=feature.id, title="T1", status="backlog")
        session.add(t)
        session.flush()

        svc = TaskService(session)
        result = svc.update(t.id, title="T1 Updated")
        assert result.title == "T1 Updated"
        assert result.status == "backlog"

    def test_status_change_validates(self, _db, session, feature):
        t = Task(feature_id=feature.id, title="T1", status="ready")
        session.add(t)
        session.flush()

        svc = TaskService(session)
        result = svc.update(t.id, status="claimed")
        assert result.status == "claimed"

    def test_full_lifecycle(self, _db, session, feature):
        t = Task(feature_id=feature.id, title="T1", status="backlog")
        session.add(t)
        session.flush()

        svc = TaskService(session)
        svc.update(t.id, status="ready")
        svc.update(t.id, status="claimed")
        svc.update(t.id, status="in_progress")
        svc.update(t.id, status="ready_for_review")
        svc.update(t.id, status="done")
        assert t.status == "done"

    def test_update_nonexistent_raises(self, _db, session):
        svc = TaskService(session)
        with pytest.raises(NotFound):
            svc.update("nonexistent", status="ready")

    def test_update_without_status_no_validate(self, _db, session, feature):
        t = Task(feature_id=feature.id, title="T1", status="backlog")
        session.add(t)
        session.flush()

        svc = TaskService(session)
        result = svc.update(t.id, title="New Title", priority=5)
        assert result.title == "New Title"
        assert result.priority == 5
        assert result.status == "backlog"
