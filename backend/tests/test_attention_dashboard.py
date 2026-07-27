"""Tests for Attention Dashboard API — TASK-0083."""

import pytest
from app.delivery.models import ClarificationRequest, Feature, Task  # noqa: F401
from app.projects.models import Project  # noqa: F401
from app.quality.models import DoDItem, ReviewRound
from app.reporting.attention import AttentionDashboardService
from app.shared.database import Base

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
def session(_db):
    s = _TestSession()
    yield s
    s.close()


@pytest.fixture()
def project(session):
    p = Project(name="Test", slug="test")
    session.add(p)
    session.flush()
    return p


@pytest.fixture()
def feature(session, project):
    f = Feature(project_id=project.id, name="F1", slug="f1")
    session.add(f)
    session.flush()
    return f


class TestAttentionDashboardService:
    def test_empty_dashboard(self, session):
        svc = AttentionDashboardService(session)
        result = svc.get_attention()
        assert result["needs_review"] == []
        assert result["open_questions"] == []
        assert result["blocked_tasks"] == []
        assert result["stale_claims"] == []
        assert result["failed_dod"] == []
        assert result["rejected_tasks"] == []
        assert result["agent_verdicts_waiting"] == []
        assert result["low_health_projects"] == []
        assert result["recent_activity"] == []

    def test_needs_review(self, session, feature):
        """Tasks with pending review rounds appear in needs_review."""
        t = Task(feature_id=feature.id, title="T1", status="in_progress")
        session.add(t)
        session.flush()

        rr = ReviewRound(
            task_id=t.id,
            requested_by_type="agent",
            requested_by_id="a1",
            state="pending",
        )
        session.add(rr)
        session.flush()

        svc = AttentionDashboardService(session)
        result = svc.get_attention()
        assert len(result["needs_review"]) == 1
        assert result["needs_review"][0]["task_id"] == t.id

    def test_open_questions(self, session, feature):
        """Blocking open clarifications appear in open_questions."""
        t = Task(feature_id=feature.id, title="T2", status="in_progress")
        session.add(t)
        session.flush()

        cr = ClarificationRequest(
            task_id=t.id,
            author_type="agent",
            author_id="a1",
            question="What format?",
            blocking=True,
            state="open",
        )
        session.add(cr)
        session.flush()

        svc = AttentionDashboardService(session)
        result = svc.get_attention()
        assert len(result["open_questions"]) == 1
        assert result["open_questions"][0]["task_id"] == t.id

    def test_non_blocking_question_excluded(self, session, feature):
        """Non-blocking clarifications do NOT appear in open_questions."""
        t = Task(feature_id=feature.id, title="T3", status="in_progress")
        session.add(t)
        session.flush()

        cr = ClarificationRequest(
            task_id=t.id,
            author_type="agent",
            author_id="a1",
            question="Minor question",
            blocking=False,
            state="open",
        )
        session.add(cr)
        session.flush()

        svc = AttentionDashboardService(session)
        result = svc.get_attention()
        assert len(result["open_questions"]) == 0

    def test_blocked_tasks(self, session, feature):
        """Tasks in blocked status appear in blocked_tasks."""
        t = Task(feature_id=feature.id, title="T4", status="blocked")
        session.add(t)
        session.flush()

        svc = AttentionDashboardService(session)
        result = svc.get_attention()
        assert len(result["blocked_tasks"]) == 1
        assert result["blocked_tasks"][0]["task_id"] == t.id

    def test_failed_dod(self, session, feature):
        """Tasks with failed DoD items appear in failed_dod."""
        t = Task(feature_id=feature.id, title="T5", status="in_progress")
        session.add(t)
        session.flush()

        dod = DoDItem(task_id=t.id, name="Tests pass", status="failed")
        session.add(dod)
        session.flush()

        svc = AttentionDashboardService(session)
        result = svc.get_attention()
        assert len(result["failed_dod"]) == 1
        assert result["failed_dod"][0]["task_id"] == t.id

    def test_project_health_score(self, session, feature):
        """Project health score is calculated correctly."""
        # Add a blocked task
        t = Task(feature_id=feature.id, title="T6", status="blocked")
        session.add(t)
        session.flush()

        svc = AttentionDashboardService(session)
        health = svc.get_project_health(feature.project_id)
        assert health["score"] == 85  # 100 - (1 blocked * 15)

    def test_health_score_all_healthy(self, session, project):
        """Project with no issues has health 100."""
        svc = AttentionDashboardService(session)
        health = svc.get_project_health(project.id)
        assert health["score"] == 100
