"""Unit tests for WorkflowService clarification methods — TASK-0099 B1."""

import pytest
from app.delivery.models import ClarificationRequest, Feature, Task, TaskClaim  # noqa: F401
from app.delivery.workflow import WorkflowService
from app.projects.models import Project  # noqa: F401
from app.shared.database import Base
from app.shared.errors import Conflict, NotFound

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
def claimed_task(session, feature) -> Task:
    t = Task(feature_id=feature.id, title="Claimed Task", status="claimed")
    session.add(t)
    session.flush()
    return t


@pytest.fixture()
def in_progress_task(session, feature) -> Task:
    t = Task(feature_id=feature.id, title="IP Task", status="in_progress")
    session.add(t)
    session.flush()
    return t


class TestCreateClarification:
    def test_create_non_blocking(self, _db, session, claimed_task):
        svc = WorkflowService(session)
        tca = TaskClaim(
            task_id=claimed_task.id,
            agent_id="agent-001",
            state="active",
        )
        session.add(tca)
        session.flush()

        cr = svc.create_clarification(
            claimed_task.id,
            agent_id="agent-001",
            question="What format?",
            context="For CSV",
        )
        assert cr.question == "What format?"
        assert cr.blocking is False
        assert cr.state == "open"
        assert cr.author_id == "agent-001"

    def test_create_blocking_transitions_task(self, _db, session, in_progress_task):
        """Blocking clarification transitions in_progress → needs_clarification."""
        svc = WorkflowService(session)
        tca = TaskClaim(
            task_id=in_progress_task.id,
            agent_id="agent-001",
            state="active",
        )
        session.add(tca)
        session.flush()

        cr = svc.create_clarification(
            in_progress_task.id,
            agent_id="agent-001",
            question="Important?",
            blocking=True,
        )
        session.flush()
        assert cr.blocking is True
        assert in_progress_task.status == "needs_clarification"

    def test_create_no_claim_raises(self, _db, session, claimed_task):
        svc = WorkflowService(session)
        with pytest.raises(NotFound, match="no active claim"):
            svc.create_clarification(
                claimed_task.id,
                agent_id="agent-001",
                question="What?",
            )

    def test_create_wrong_agent_raises(self, _db, session, claimed_task):
        svc = WorkflowService(session)
        tca = TaskClaim(
            task_id=claimed_task.id,
            agent_id="agent-001",
            state="active",
        )
        session.add(tca)
        session.flush()

        with pytest.raises(Conflict, match="not your claim"):
            svc.create_clarification(
                claimed_task.id,
                agent_id="agent-002",
                question="What?",
            )

    def test_create_nonexistent_task_raises(self, _db, session):
        svc = WorkflowService(session)
        with pytest.raises(NotFound):
            svc.create_clarification(
                "nonexistent",
                agent_id="agent-001",
                question="What?",
            )


class TestAnswerClarification:
    def test_answer_success(self, _db, session, in_progress_task):
        svc = WorkflowService(session)
        cr = ClarificationRequest(
            task_id=in_progress_task.id,
            author_type="agent",
            author_id="agent-001",
            question="What format?",
            state="open",
        )
        session.add(cr)
        session.flush()

        result = svc.answer_clarification(
            cr.id,
            answered_by="human-001",
            answer="Use JSON",
        )
        assert result.state == "answered"
        assert result.answer == "Use JSON"
        assert result.answered_by == "human-001"
        assert result.answered_at is not None

    def test_answer_blocking_unblocks_task(self, _db, session, feature):
        svc = WorkflowService(session)
        t = Task(
            feature_id=feature.id,
            title="Blocked",
            status="needs_clarification",
        )
        session.add(t)
        session.flush()

        cr = ClarificationRequest(
            task_id=t.id,
            author_type="agent",
            author_id="agent-001",
            question="Important?",
            blocking=True,
            state="open",
        )
        session.add(cr)
        session.flush()

        svc.answer_clarification(cr.id, answered_by="human-001", answer="Yes")
        session.flush()
        assert t.status == "in_progress"

    def test_answer_nonexistent_raises(self, _db, session):
        svc = WorkflowService(session)
        with pytest.raises(NotFound):
            svc.answer_clarification("nonexistent", answered_by="h", answer="a")

    def test_answer_already_answered_raises(self, _db, session, in_progress_task):
        svc = WorkflowService(session)
        cr = ClarificationRequest(
            task_id=in_progress_task.id,
            author_type="agent",
            author_id="agent-001",
            question="Q?",
            state="answered",
            answer="old",
        )
        session.add(cr)
        session.flush()

        with pytest.raises(Conflict, match="answered"):
            svc.answer_clarification(cr.id, answered_by="h", answer="new")


class TestResolveClarification:
    def test_resolve_success(self, _db, session, in_progress_task):
        svc = WorkflowService(session)
        cr = ClarificationRequest(
            task_id=in_progress_task.id,
            author_type="agent",
            author_id="agent-001",
            question="Q?",
            state="answered",
            answer="A",
        )
        session.add(cr)
        session.flush()

        result = svc.resolve_clarification(cr.id)
        assert result.state == "resolved"

    def test_resolve_not_answered_raises(self, _db, session, in_progress_task):
        svc = WorkflowService(session)
        cr = ClarificationRequest(
            task_id=in_progress_task.id,
            author_type="agent",
            author_id="agent-001",
            question="Q?",
            state="open",
        )
        session.add(cr)
        session.flush()

        with pytest.raises(Conflict, match="answered"):
            svc.resolve_clarification(cr.id)

    def test_resolve_nonexistent_raises(self, _db, session):
        svc = WorkflowService(session)
        with pytest.raises(NotFound):
            svc.resolve_clarification("nonexistent")
