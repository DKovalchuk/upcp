"""Tests for analytics service and API — TASK-0102."""

from datetime import UTC, datetime

import pytest
from app.delivery.models import Feature, Task, TaskClaim
from app.project.models import Project
from app.reporting.analytics import AnalyticsService
from app.shared.database import Base
from app.shared.text import new_id
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestSession = sessionmaker(bind=engine)
    session = TestSession()
    yield session
    session.close()
    engine.dispose()


def _setup_project(session) -> tuple[str, str]:
    """Create a project and feature, return their IDs."""
    pid = new_id()
    fid = new_id()
    session.add(Project(id=pid, name="Test", slug="test", status="active"))
    session.add(Feature(id=fid, project_id=pid, name="F1", slug="f1", status="active"))
    session.commit()
    return pid, fid


class TestAnalyticsService:
    def test_project_trends_empty(self, db_session):
        pid, _ = _setup_project(db_session)
        svc = AnalyticsService(db_session)
        trends = svc.get_project_trends(pid, weeks=4)
        assert len(trends) == 4
        assert all(t["completed"] == 0 for t in trends)

    def test_team_velocity_empty(self, db_session):
        pid, _ = _setup_project(db_session)
        svc = AnalyticsService(db_session)
        velocity = svc.get_team_velocity(pid, weeks=4)
        assert len(velocity) == 4
        assert all(v["count"] == 0 for v in velocity)

    def test_health_history_empty(self, db_session):
        pid, _ = _setup_project(db_session)
        svc = AnalyticsService(db_session)
        history = svc.get_health_history(pid, days=7)
        assert len(history) == 7

    def test_agents_overview_empty(self, db_session):
        svc = AnalyticsService(db_session)
        overview = svc.get_agents_overview()
        assert overview == []

    def test_agent_performance_with_claims(self, db_session):
        pid, fid = _setup_project(db_session)
        tid = new_id()
        db_session.add(
            Task(
                id=tid,
                feature_id=fid,
                title="T1",
                status="done",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        )
        db_session.add(
            TaskClaim(
                id=new_id(),
                task_id=tid,
                agent_id="agent-1",
                claimed_at=datetime.now(UTC),
            )
        )
        db_session.commit()

        svc = AnalyticsService(db_session)
        perf = svc.get_agent_performance("agent-1")
        assert len(perf) == 1
        assert perf[0]["agent_id"] == "agent-1"
        assert perf[0]["total_claims"] == 1
