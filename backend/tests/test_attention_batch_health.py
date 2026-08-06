"""Tests for AttentionDashboardService batch health — TASK-0092 (2.2)."""

import pytest
from app.delivery.models import ClarificationRequest, Feature, Task  # noqa: F401
from app.projects.models import Project  # noqa: F401
from app.quality.models import DoDItem
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


def _seed_project(session, name: str, n_features: int = 2, n_tasks: int = 3):
    """Create a project with features and tasks."""
    p = Project(name=name, slug=name.lower().replace(" ", "-"))
    session.add(p)
    session.flush()

    features = []
    all_tasks = []
    for i in range(n_features):
        f = Feature(project_id=p.id, name=f"{name}-F{i}", slug=f"{name.lower()}-f{i}")
        session.add(f)
        session.flush()
        features.append(f)

        for j in range(n_tasks):
            statuses = ["done", "in_progress", "backlog"]
            t = Task(feature_id=f.id, title=f"{name}-T{i}-{j}", status=statuses[j % len(statuses)])
            session.add(t)
            all_tasks.append(t)

    session.flush()
    return p, features, all_tasks


class TestBatchHealth:
    def test_empty_batch(self, session):
        """Empty project list returns empty dict."""
        svc = AttentionDashboardService(session)
        result = svc.get_projects_health_batch([])
        assert result == {}

    def test_single_project_healthy(self, session):
        """Project with no issues has score 100."""
        p, _, _ = _seed_project(session, "Alpha")
        svc = AttentionDashboardService(session)
        result = svc.get_projects_health_batch([p.id])
        assert result[p.id]["score"] == 100
        assert result[p.id]["top_issue"] == ""

    def test_single_project_blocked(self, session):
        """Project with blocked tasks has reduced score."""
        p, features, _ = _seed_project(session, "Beta")
        t = Task(feature_id=features[0].id, title="Blocked", status="blocked")
        session.add(t)
        session.flush()

        svc = AttentionDashboardService(session)
        result = svc.get_projects_health_batch([p.id])
        assert result[p.id]["score"] < 100
        assert result[p.id]["breakdown"]["blocked"] == 1

    def test_multiple_projects(self, session):
        """Batch health works for multiple projects."""
        p1, _, _ = _seed_project(session, "Project-1")
        p2, _, _ = _seed_project(session, "Project-2")

        svc = AttentionDashboardService(session)
        result = svc.get_projects_health_batch([p1.id, p2.id])
        assert len(result) == 2
        assert p1.id in result
        assert p2.id in result

    def test_project_without_tasks(self, session):
        """Project with features but no tasks still gets score 100."""
        p = Project(name="NoTasks", slug="no-tasks")
        session.add(p)
        session.flush()

        f = Feature(project_id=p.id, name="Empty-F", slug="empty-f")
        session.add(f)
        session.flush()

        svc = AttentionDashboardService(session)
        result = svc.get_projects_health_batch([p.id])
        assert result[p.id]["score"] == 100

    def test_project_with_failed_dod(self, session):
        """Project with failed DoD items has reduced score."""
        p, features, tasks = _seed_project(session, "DodFail")
        dod = DoDItem(task_id=tasks[0].id, name="Tests pass", status="failed")
        session.add(dod)
        session.flush()

        svc = AttentionDashboardService(session)
        result = svc.get_projects_health_batch([p.id])
        assert result[p.id]["score"] < 100
        assert result[p.id]["breakdown"]["failed_dod"] == 1

    def test_project_with_open_clarification(self, session):
        """Project with blocking open clarification has reduced score."""
        p, features, tasks = _seed_project(session, "Clarify")
        cr = ClarificationRequest(
            task_id=tasks[0].id,
            author_type="agent",
            author_id="a1",
            question="What?",
            blocking=True,
            state="open",
        )
        session.add(cr)
        session.flush()

        svc = AttentionDashboardService(session)
        result = svc.get_projects_health_batch([p.id])
        assert result[p.id]["score"] < 100
        assert result[p.id]["breakdown"]["open_clarifications"] == 1
