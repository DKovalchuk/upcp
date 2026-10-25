"""Tests for Notification model and API — TASK-0085."""

import pytest
from app.projects.models import Project  # noqa: F401
from app.reporting.models import Notification
from app.reporting.service import NotificationService
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
def session(_db):
    s = _TestSession()
    yield s
    s.close()


class TestNotificationModel:
    def test_create_notification(self, session):
        n = Notification(
            user_id="user-1",
            type="task_claimed",
            title="Task claimed",
            message="Agent claimed TASK-001",
            entity_type="task",
            entity_id="task-1",
        )
        session.add(n)
        session.flush()
        assert n.id is not None
        assert n.is_read is False
        assert n.created_at is not None

    def test_notification_optional_fields(self, session):
        n = Notification(
            user_id="user-1",
            type="info",
            title="Info",
            message="Something happened",
        )
        session.add(n)
        session.flush()
        assert n.entity_type is None
        assert n.entity_id is None


class TestNotificationService:
    def test_create(self, session):
        svc = NotificationService(session)
        n = svc.create(
            user_id="user-1",
            type="task_claimed",
            title="Task claimed",
            message="Agent claimed TASK-001",
            entity_type="task",
            entity_id="task-1",
        )
        assert n.id is not None
        assert n.is_read is False

    def test_list_by_user(self, session):
        svc = NotificationService(session)
        svc.create(user_id="user-1", type="a", title="A", message="msg1")
        svc.create(user_id="user-1", type="b", title="B", message="msg2")
        svc.create(user_id="user-2", type="c", title="C", message="msg3")
        items = svc.list_by_user("user-1")
        assert len(items) == 2

    def test_mark_read(self, session):
        svc = NotificationService(session)
        n = svc.create(user_id="u1", type="a", title="A", message="msg")
        result = svc.mark_read(n.id)
        assert result.is_read is True

    def test_mark_read_not_found(self, session):
        svc = NotificationService(session)
        with pytest.raises(NotFound):
            svc.mark_read("nonexistent")

    def test_mark_all_read(self, session):
        svc = NotificationService(session)
        svc.create(user_id="u1", type="a", title="A", message="msg1")
        svc.create(user_id="u1", type="b", title="B", message="msg2")
        count = svc.mark_all_read("u1")
        assert count == 2
        items = svc.list_by_user("u1")
        assert all(n.is_read for n in items)

    def test_unread_count(self, session):
        svc = NotificationService(session)
        n1 = svc.create(user_id="u1", type="a", title="A", message="msg1")
        svc.create(user_id="u1", type="b", title="B", message="msg2")
        assert svc.unread_count("u1") == 2
        svc.mark_read(n1.id)
        assert svc.unread_count("u1") == 1

    def test_list_by_user_with_unread_only(self, session):
        svc = NotificationService(session)
        n1 = svc.create(user_id="u1", type="a", title="A", message="msg1")
        svc.create(user_id="u1", type="b", title="B", message="msg2")
        svc.mark_read(n1.id)
        unread = svc.list_by_user("u1", unread_only=True)
        assert len(unread) == 1
