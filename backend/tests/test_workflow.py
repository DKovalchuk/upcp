"""Tests for agent workflow endpoints — TASK-0074."""

import pytest
from app.delivery.models import Feature, Heartbeat, Task, TaskClaim  # noqa: F401
from app.delivery.workflow import WorkflowService
from app.projects.models import Project  # noqa: F401
from app.shared.database import Base
from app.shared.errors import Conflict, NotFound

from tests.conftest import _test_engine, _TestSession


@pytest.fixture()
def _db():
    import app.audit.models  # noqa: F401
    import app.auth.models  # noqa: F401
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
def ready_task(session, feature) -> Task:
    t = Task(feature_id=feature.id, title="Ready Task", status="ready")
    session.add(t)
    session.flush()
    return t


@pytest.fixture()
def in_progress_task(session, feature) -> Task:
    t = Task(feature_id=feature.id, title="IP Task", status="in_progress")
    session.add(t)
    session.flush()
    return t


class TestClaimTask:
    def test_claim_ready_task(self, _db, session, ready_task):
        """Agent can claim a ready task."""
        svc = WorkflowService(session)
        claim = svc.claim(ready_task.id, agent_id="agent-001")
        assert claim.task_id == ready_task.id
        assert claim.agent_id == "agent-001"
        assert claim.state == "active"

    def test_claim_updates_task_status(self, _db, session, ready_task):
        """Claiming a task transitions it to 'claimed'."""
        svc = WorkflowService(session)
        svc.claim(ready_task.id, agent_id="agent-001")
        session.flush()
        assert ready_task.status == "claimed"

    def test_claim_already_claimed_raises(self, _db, session, ready_task):
        """Cannot claim a task already claimed by another agent."""
        svc = WorkflowService(session)
        svc.claim(ready_task.id, agent_id="agent-001")
        session.flush()

        with pytest.raises(Conflict):
            svc.claim(ready_task.id, agent_id="agent-002")

    def test_claim_not_ready_raises(self, _db, session, in_progress_task):
        """Cannot claim a task not in 'ready' status."""
        svc = WorkflowService(session)
        with pytest.raises(Conflict):
            svc.claim(in_progress_task.id, agent_id="agent-001")

    def test_claim_nonexistent_task(self, _db, session):
        """Claiming a nonexistent task raises NotFound."""
        svc = WorkflowService(session)
        with pytest.raises(NotFound):
            svc.claim("nonexistent", agent_id="agent-001")

    def test_claim_with_context(self, _db, session, ready_task):
        """Claim with context snapshot."""
        svc = WorkflowService(session)
        claim = svc.claim(ready_task.id, agent_id="agent-001", context_snapshot="snap123")
        assert claim.context_snapshot == "snap123"


class TestReleaseTask:
    def test_release_own_claim(self, _db, session, ready_task):
        """Agent can release their own claim."""
        svc = WorkflowService(session)
        claim = svc.claim(ready_task.id, agent_id="agent-001")
        svc.release(ready_task.id, agent_id="agent-001")
        session.flush()
        assert claim.state == "released"
        assert ready_task.status == "backlog"

    def test_release_other_agent_claim_raises(self, _db, session, ready_task):
        """Cannot release another agent's claim."""
        svc = WorkflowService(session)
        svc.claim(ready_task.id, agent_id="agent-001")
        session.flush()

        with pytest.raises(Conflict):
            svc.release(ready_task.id, agent_id="agent-002")

    def test_release_no_claim_raises(self, _db, session, ready_task):
        """Releasing a task with no claim raises NotFound."""
        svc = WorkflowService(session)
        with pytest.raises(NotFound):
            svc.release(ready_task.id, agent_id="agent-001")


class TestHeartbeat:
    def test_send_heartbeat(self, _db, session, ready_task):
        """Agent can send a heartbeat on claimed task."""
        svc = WorkflowService(session)
        svc.claim(ready_task.id, agent_id="agent-001")
        session.flush()

        hb = svc.heartbeat(
            ready_task.id,
            agent_id="agent-001",
            progress_percent=50,
            current_step="coding",
            next_step="testing",
        )
        assert hb.progress_percent == 50
        assert hb.current_step == "coding"

    def test_heartbeat_wrong_agent_raises(self, _db, session, ready_task):
        """Cannot heartbeat on another agent's claim."""
        svc = WorkflowService(session)
        svc.claim(ready_task.id, agent_id="agent-001")
        session.flush()

        with pytest.raises(Conflict):
            svc.heartbeat(
                ready_task.id,
                agent_id="agent-002",
                progress_percent=50,
                current_step="coding",
                next_step="testing",
            )

    def test_heartbeat_updates_last_heartbeat_at(self, _db, session, ready_task):
        """Heartbeat updates claim's last_heartbeat_at."""
        svc = WorkflowService(session)
        claim = svc.claim(ready_task.id, agent_id="agent-001")
        session.flush()

        svc.heartbeat(
            ready_task.id,
            agent_id="agent-001",
            progress_percent=30,
            current_step="step1",
            next_step="step2",
        )
        session.flush()
        assert claim.last_heartbeat_at is not None

    def test_heartbeat_no_claim_raises(self, _db, session, ready_task):
        """Heartbeat on unclaimed task raises NotFound."""
        svc = WorkflowService(session)
        with pytest.raises(NotFound):
            svc.heartbeat(
                ready_task.id,
                agent_id="agent-001",
                progress_percent=50,
                current_step="coding",
                next_step="testing",
            )


class TestProgress:
    def test_update_progress(self, _db, session, ready_task):
        """Agent can update progress on claimed task."""
        svc = WorkflowService(session)
        svc.claim(ready_task.id, agent_id="agent-001")
        session.flush()

        hb = svc.progress(ready_task.id, agent_id="agent-001", progress_percent=75)
        assert hb.progress_percent == 75

    def test_progress_step_names_not_empty(self, _db, session, ready_task):
        """progress() uses meaningful step names, not empty strings."""
        svc = WorkflowService(session)
        svc.claim(ready_task.id, agent_id="agent-001")
        session.flush()

        hb = svc.progress(ready_task.id, agent_id="agent-001", progress_percent=50)
        assert hb.current_step != ""
        assert hb.next_step != ""
        assert len(hb.current_step) > 0
        assert len(hb.next_step) > 0

    def test_progress_wrong_agent_raises(self, _db, session, ready_task):
        """Cannot update progress on another agent's claim."""
        svc = WorkflowService(session)
        svc.claim(ready_task.id, agent_id="agent-001")
        session.flush()

        with pytest.raises(Conflict):
            svc.progress(ready_task.id, agent_id="agent-002", progress_percent=75)
