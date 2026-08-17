"""Tests for TaskClaim and Heartbeat models — TASK-0070."""

import pytest
from app.delivery.models import Feature, Heartbeat, Task, TaskClaim  # noqa: F401
from app.projects.models import Project  # noqa: F401
from app.shared.database import Base
from app.shared.text import utcnow
from sqlalchemy.exc import IntegrityError

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
    """Provide a transactional DB session that rolls back after each test."""
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
    t = Task(feature_id=feature.id, title="T1", status="ready")
    session.add(t)
    session.flush()
    return t


class TestTaskClaim:
    def test_create_claim(self, _db, session, task):
        """TaskClaim can be created with valid fields."""
        claim = TaskClaim(
            task_id=task.id,
            agent_id="agent-001",
            state="active",
        )
        session.add(claim)
        session.flush()
        assert claim.id is not None
        assert claim.task_id == task.id
        assert claim.agent_id == "agent-001"
        assert claim.state == "active"
        assert claim.claimed_at is not None

    def test_claim_default_state(self, _db, session, task):
        """New claim defaults to active state."""
        claim = TaskClaim(task_id=task.id, agent_id="agent-001")
        session.add(claim)
        session.flush()
        assert claim.state == "active"

    def test_unique_active_claim_per_task(self, _db, session, task):
        """Only one active claim allowed per task."""
        c1 = TaskClaim(task_id=task.id, agent_id="agent-001", state="active")
        session.add(c1)
        session.flush()

        # Second active claim on same task should fail
        c2 = TaskClaim(task_id=task.id, agent_id="agent-002", state="active")
        session.add(c2)
        with pytest.raises(IntegrityError):
            session.flush()
        session.rollback()
        session.begin_nested()

    def test_released_claim_allows_new_claim(self, _db, session, task):
        """After release, a new active claim is possible."""
        c1 = TaskClaim(task_id=task.id, agent_id="agent-001", state="released")
        session.add(c1)
        session.flush()

        c2 = TaskClaim(task_id=task.id, agent_id="agent-002", state="active")
        session.add(c2)
        session.flush()
        assert c2.id is not None

    def test_claim_fields(self, _db, session, task):
        """Claim stores expires_at and context_snapshot."""
        claim = TaskClaim(
            task_id=task.id,
            agent_id="agent-001",
            expires_at=utcnow(),
            context_snapshot="snapshot-data",
        )
        session.add(claim)
        session.flush()
        assert claim.expires_at is not None
        assert claim.context_snapshot == "snapshot-data"


class TestHeartbeat:
    def test_create_heartbeat(self, _db, session, task):
        """Heartbeat can be created with valid fields."""
        claim = TaskClaim(task_id=task.id, agent_id="agent-001")
        session.add(claim)
        session.flush()

        hb = Heartbeat(
            claim_id=claim.id,
            progress_percent=50,
            current_step="implementing",
            next_step="testing",
        )
        session.add(hb)
        session.flush()
        assert hb.id is not None
        assert hb.claim_id == claim.id
        assert hb.progress_percent == 50

    def test_heartbeat_with_optionals(self, _db, session, task):
        """Heartbeat stores blockers and eta."""
        claim = TaskClaim(task_id=task.id, agent_id="agent-001")
        session.add(claim)
        session.flush()

        hb = Heartbeat(
            claim_id=claim.id,
            progress_percent=30,
            current_step="coding",
            next_step="review",
            blockers="waiting for API spec",
            eta="2026-07-28T12:00:00Z",
        )
        session.add(hb)
        session.flush()
        assert hb.blockers == "waiting for API spec"
        assert hb.eta == "2026-07-28T12:00:00Z"

    def test_multiple_heartbeats_per_claim(self, _db, session, task):
        """Multiple heartbeats can exist per claim."""
        claim = TaskClaim(task_id=task.id, agent_id="agent-001")
        session.add(claim)
        session.flush()

        for i in range(3):
            hb = Heartbeat(
                claim_id=claim.id,
                progress_percent=i * 33,
                current_step=f"step-{i}",
                next_step=f"step-{i + 1}",
            )
            session.add(hb)
        session.flush()

        heartbeats = session.query(Heartbeat).filter_by(claim_id=claim.id).all()
        assert len(heartbeats) == 3
