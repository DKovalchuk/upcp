"""Tests for ClarificationRequest model — TASK-0071."""

import pytest
from app.delivery.models import ClarificationRequest, Feature, Task  # noqa: F401
from app.projects.models import Project  # noqa: F401
from app.shared.database import Base

from tests.conftest import _test_engine, _TestSession


@pytest.fixture()
def _db():
    """Create tables, yield, then drop."""
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
def task(session, feature) -> Task:
    t = Task(feature_id=feature.id, title="T1", status="in_progress")
    session.add(t)
    session.flush()
    return t


class TestClarificationRequest:
    def test_create_clarification(self, _db, session, task):
        """ClarificationRequest can be created with valid fields."""
        cr = ClarificationRequest(
            task_id=task.id,
            author_type="agent",
            author_id="agent-001",
            question="What is the expected format?",
            blocking=True,
        )
        session.add(cr)
        session.flush()
        assert cr.id is not None
        assert cr.task_id == task.id
        assert cr.author_type == "agent"
        assert cr.author_id == "agent-001"
        assert cr.question == "What is the expected format?"
        assert cr.blocking is True
        assert cr.state == "open"
        assert cr.created_at is not None

    def test_default_state_open(self, _db, session, task):
        """New clarification defaults to open state."""
        cr = ClarificationRequest(
            task_id=task.id,
            author_type="agent",
            author_id="agent-001",
            question="Question?",
        )
        session.add(cr)
        session.flush()
        assert cr.state == "open"

    def test_answer_clarification(self, _db, session, task):
        """Answering a clarification updates state and fields."""
        from app.shared.text import utcnow

        cr = ClarificationRequest(
            task_id=task.id,
            author_type="agent",
            author_id="agent-001",
            question="Question?",
        )
        session.add(cr)
        session.flush()

        cr.state = "answered"
        cr.answer = "Use JSON format."
        cr.answered_by = "user-001"
        cr.answered_at = utcnow()
        session.flush()

        assert cr.state == "answered"
        assert cr.answer == "Use JSON format."
        assert cr.answered_by == "user-001"
        assert cr.answered_at is not None

    def test_resolve_clarification(self, _db, session, task):
        """Resolving a clarification updates state to resolved."""
        cr = ClarificationRequest(
            task_id=task.id,
            author_type="agent",
            author_id="agent-001",
            question="Question?",
            state="answered",
            answer="Answer.",
            answered_by="user-001",
        )
        session.add(cr)
        session.flush()

        cr.state = "resolved"
        session.flush()
        assert cr.state == "resolved"

    def test_context_field(self, _db, session, task):
        """ClarificationRequest stores context."""
        cr = ClarificationRequest(
            task_id=task.id,
            author_type="agent",
            author_id="agent-001",
            question="Question?",
            context="Relevant file: src/main.py",
        )
        session.add(cr)
        session.flush()
        assert cr.context == "Relevant file: src/main.py"

    def test_blocking_default_false(self, _db, session, task):
        """blocking defaults to False."""
        cr = ClarificationRequest(
            task_id=task.id,
            author_type="agent",
            author_id="agent-001",
            question="Question?",
        )
        session.add(cr)
        session.flush()
        assert cr.blocking is False

    def test_multiple_clarifications_per_task(self, _db, session, task):
        """Multiple clarifications can exist per task."""
        for i in range(3):
            cr = ClarificationRequest(
                task_id=task.id,
                author_type="agent",
                author_id="agent-001",
                question=f"Question {i}?",
            )
            session.add(cr)
        session.flush()

        items = session.query(ClarificationRequest).filter_by(task_id=task.id).all()
        assert len(items) == 3
