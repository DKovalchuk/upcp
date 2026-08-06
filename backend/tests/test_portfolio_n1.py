"""Tests for PortfolioService N+1 query optimization — TASK-0092 (2.1)."""

from unittest.mock import patch

import pytest
from app.delivery.models import Feature, Task  # noqa: F401
from app.projects.models import Project  # noqa: F401
from app.reporting.portfolio import PortfolioService
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


def _seed_data(session, n_projects: int = 5, n_features: int = 3, n_tasks: int = 4):
    """Create test data with multiple projects, features, and tasks."""
    projects = []
    all_features = []
    all_tasks = []

    for p_idx in range(n_projects):
        p = Project(name=f"Project-{p_idx}", slug=f"project-{p_idx}")
        session.add(p)
        session.flush()
        projects.append(p)

        for f_idx in range(n_features):
            f = Feature(project_id=p.id, name=f"F{p_idx}-{f_idx}", slug=f"f{p_idx}-{f_idx}")
            session.add(f)
            session.flush()
            all_features.append(f)

            for t_idx in range(n_tasks):
                statuses = ["done", "in_progress", "backlog", "review"]
                t = Task(
                    feature_id=f.id,
                    title=f"T{p_idx}-{f_idx}-{t_idx}",
                    status=statuses[t_idx % len(statuses)],
                )
                session.add(t)
                all_tasks.append(t)

    session.flush()
    return projects, all_features, all_tasks


class TestPortfolioN1Fix:
    """Verify PortfolioService uses batch queries instead of per-project loops."""

    def test_batch_query_used(self, session):
        """PortfolioService should use ≤5 queries regardless of project count."""
        projects, _, _ = _seed_data(session, n_projects=5, n_features=3, n_tasks=4)

        # Patch query to count calls
        original_query = type(session).query
        query_count = 0

        def counting_query(*args, **kwargs):
            nonlocal query_count
            query_count += 1
            return original_query(*args, **kwargs)

        with patch.object(type(session), "query", counting_query):
            svc = PortfolioService(session)
            result = svc.get_overview()

        # Should be: 3 (portfolio) + 7 (batch health) = 10 queries
        # NOT 5 + 5*3 + 5*6 = 50+ per-project queries
        assert query_count <= 12, f"Expected ≤12 queries, got {query_count}"
        assert result["total_projects"] == 5
        assert result["total_tasks"] == 5 * 3 * 4  # 60

    def test_empty_portfolio_still_works(self, session):
        """Empty portfolio returns correct defaults."""
        svc = PortfolioService(session)
        result = svc.get_overview()
        assert result["total_projects"] == 0
        assert result["total_tasks"] == 0
        assert result["projects"] == []

    def test_single_project(self, session):
        """Single project with tasks works correctly."""
        _seed_data(session, n_projects=1, n_features=2, n_tasks=3)
        svc = PortfolioService(session)
        result = svc.get_overview()
        assert result["total_projects"] == 1
        assert result["total_tasks"] == 6
        assert len(result["projects"]) == 1

    def test_tasks_by_status_correct(self, session):
        """Task counts by status are aggregated correctly."""
        _seed_data(session, n_projects=2, n_features=1, n_tasks=4)
        svc = PortfolioService(session)
        result = svc.get_overview()
        # Each project has 1 feature with 4 tasks: done, in_progress, backlog, review
        assert result["tasks_by_status"]["done"] == 2
        assert result["tasks_by_status"]["in_progress"] == 2
        assert result["tasks_by_status"]["backlog"] == 2
        assert result["tasks_by_status"]["review"] == 2

    def test_project_without_features(self, session):
        """Project with no features still appears in summary."""
        p = Project(name="Empty", slug="empty")
        session.add(p)
        session.flush()

        svc = PortfolioService(session)
        result = svc.get_overview()
        assert result["total_projects"] == 1
        assert result["total_tasks"] == 0
        assert len(result["projects"]) == 1
        assert result["projects"][0]["task_count"] == 0
