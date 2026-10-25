"""Unit tests for stale claim reaper — TASK-0099 B2."""

from datetime import UTC, datetime, timedelta

import pytest
from app.delivery.models import Feature, Heartbeat, Task, TaskClaim  # noqa: F401
from app.delivery.stale_reaper import DEAD_MINUTES, STALE_MINUTES, reaper_tick
from app.projects.models import Project  # noqa: F401
from app.shared.database import Base
from app.shared.text import new_id

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


@pytest.fixture()
def ready_task(session, feature) -> Task:
    t = Task(feature_id=feature.id, title="Ready", status="ready")
    session.add(t)
    session.flush()
    return t


def _make_claim(
    session, task_id: str, agent_id: str, *, heartbeat_ago: timedelta | None = None
) -> TaskClaim:
    claim = TaskClaim(
        id=new_id(),
        task_id=task_id,
        agent_id=agent_id,
        state="active",
    )
    if heartbeat_ago is not None:
        claim.last_heartbeat_at = datetime.now(UTC) - heartbeat_ago
    session.add(claim)
    session.flush()
    return claim


class TestReaperTick:
    def test_no_claims_returns_zero(self, _db, session):
        result = reaper_tick(session)
        assert result == {"stale": 0, "released": 0}

    def test_fresh_claim_not_touched(self, _db, session, ready_task):
        _make_claim(session, ready_task.id, "a1", heartbeat_ago=timedelta(minutes=1))
        result = reaper_tick(session)
        assert result == {"stale": 0, "released": 0}

    def test_stale_claim_gets_notification(self, _db, session, ready_task):
        _make_claim(
            session,
            ready_task.id,
            "a1",
            heartbeat_ago=timedelta(minutes=7),
        )
        result = reaper_tick(session)
        assert result["stale"] == 1
        assert result["released"] == 0

    def test_dead_claim_gets_released(self, _db, session, ready_task):
        _make_claim(
            session,
            ready_task.id,
            "a1",
            heartbeat_ago=timedelta(minutes=20),
        )
        result = reaper_tick(session)
        assert result["stale"] == 0
        assert result["released"] == 1
        assert ready_task.status == "backlog"

    def test_dead_claim_never_heartbeated(self, _db, session, ready_task):
        """Claim with no heartbeat but claimed_at > DEAD_MINUTES ago."""
        claim = TaskClaim(
            id=new_id(),
            task_id=ready_task.id,
            agent_id="a1",
            state="active",
            claimed_at=datetime.now(UTC) - timedelta(minutes=20),
        )
        session.add(claim)
        session.flush()

        result = reaper_tick(session)
        assert result["released"] == 1

    def test_already_released_claim_not_touched(self, _db, session, ready_task):
        claim = TaskClaim(
            id=new_id(),
            task_id=ready_task.id,
            agent_id="a1",
            state="released",
            last_heartbeat_at=datetime.now(UTC) - timedelta(hours=1),
        )
        session.add(claim)
        session.flush()

        result = reaper_tick(session)
        assert result == {"stale": 0, "released": 0}

    def test_stale_boundary(self, _db, session, ready_task):
        """Just under STALE_MINUTES should NOT be stale."""
        _make_claim(
            session,
            ready_task.id,
            "a1",
            heartbeat_ago=timedelta(minutes=STALE_MINUTES) - timedelta(seconds=1),
        )
        result = reaper_tick(session)
        assert result["stale"] == 0

    def test_dead_boundary(self, _db, session, ready_task):
        """Just under DEAD_MINUTES should NOT be dead."""
        _make_claim(
            session,
            ready_task.id,
            "a1",
            heartbeat_ago=timedelta(minutes=DEAD_MINUTES) - timedelta(seconds=1),
        )
        result = reaper_tick(session)
        assert result["released"] == 0

    def test_creates_inbox_events(self, _db, session, ready_task):
        from app.delivery.models import AgentInboxEvent

        _make_claim(session, ready_task.id, "a1", heartbeat_ago=timedelta(minutes=20))
        reaper_tick(session)

        events = session.query(AgentInboxEvent).filter_by(agent_id="a1").all()
        assert len(events) == 1
        assert events[0].event_type == "claim_released"
