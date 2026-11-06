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


class TestAttentionProjectScoping:
    """Project scoping for GET /dashboard/attention — TASK-0125."""

    @staticmethod
    def _second_project(session):
        p2 = Project(name="Second", slug="second")
        session.add(p2)
        session.flush()
        f2 = Feature(project_id=p2.id, name="F2", slug="f2")
        session.add(f2)
        session.flush()
        return p2, f2

    @staticmethod
    def _blocked_pair(session, feature, other_feature):
        t1 = Task(feature_id=feature.id, title="Blocked A", status="blocked")
        t2 = Task(feature_id=other_feature.id, title="Blocked B", status="blocked")
        session.add_all([t1, t2])
        session.flush()
        return t1, t2

    def test_scoped_returns_only_project_items(self, session, project, feature):
        """Scoped attention returns only the selected project's items."""
        p2, f2 = self._second_project(session)
        t1, t2 = self._blocked_pair(session, feature, f2)

        svc = AttentionDashboardService(session)
        unscoped = svc.get_attention()
        assert {i["task_id"] for i in unscoped["blocked_tasks"]} == {t1.id, t2.id}

        scoped = svc.get_attention(project_id=project.id)
        assert [i["task_id"] for i in scoped["blocked_tasks"]] == [t1.id]
        assert scoped["blocked_tasks"][0]["project_id"] == project.id

        other_scoped = svc.get_attention(project_id=p2.id)
        assert [i["task_id"] for i in other_scoped["blocked_tasks"]] == [t2.id]

    def test_scoped_review_sections_filter_by_project(self, session, project, feature):
        """Review-based sections join tasks to scope rounds by project."""
        p2, f2 = self._second_project(session)
        t1 = Task(feature_id=feature.id, title="Review A", status="in_progress")
        t2 = Task(feature_id=f2.id, title="Review B", status="in_progress")
        session.add_all([t1, t2])
        session.flush()
        for t in (t1, t2):
            session.add(
                ReviewRound(
                    task_id=t.id,
                    requested_by_type="agent",
                    requested_by_id="a1",
                    state="pending",
                )
            )
        session.flush()

        svc = AttentionDashboardService(session)
        unscoped = svc.get_attention()
        assert len(unscoped["needs_review"]) == 2

        scoped = svc.get_attention(project_id=project.id)
        assert [i["task_id"] for i in scoped["needs_review"]] == [t1.id]
        assert scoped["needs_review"][0]["project_id"] == project.id

        other_scoped = svc.get_attention(project_id=p2.id)
        assert [i["task_id"] for i in other_scoped["needs_review"]] == [t2.id]

    def test_nonexistent_project_returns_empty_sections(self, session, project, feature):
        """Unknown project_id yields empty sections, not an error."""
        _, f2 = self._second_project(session)
        self._blocked_pair(session, feature, f2)
        t1 = Task(feature_id=feature.id, title="Review A", status="in_progress")
        session.add(t1)
        session.flush()
        session.add(
            ReviewRound(
                task_id=t1.id,
                requested_by_type="agent",
                requested_by_id="a1",
                state="pending",
            )
        )
        session.flush()

        svc = AttentionDashboardService(session)
        result = svc.get_attention(project_id="nonexistent-uuid")
        assert result["blocked_tasks"] == []
        assert result["needs_review"] == []
        assert result["open_questions"] == []
        assert result["stale_claims"] == []
        assert result["failed_dod"] == []
        assert result["rejected_tasks"] == []
        assert result["agent_verdicts_waiting"] == []
        assert result["low_health_projects"] == []
        assert result["recent_activity"] == []
