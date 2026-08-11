"""Tests for Portfolio Overview API — TASK-0087."""

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

    Base.metadata.drop_all(bind=_test_engine)
    Base.metadata.create_all(bind=_test_engine)
    yield
    Base.metadata.drop_all(bind=_test_engine)


@pytest.fixture()
def session(_db):
    s = _TestSession()
    yield s
    s.close()


class TestPortfolioService:
    def test_empty_portfolio(self, session):
        svc = PortfolioService(session)
        result = svc.get_overview()
        assert result["total_projects"] == 0
        assert result["total_tasks"] == 0
        assert result["projects"] == []

    def test_portfolio_with_projects(self, session):
        p1 = Project(name="Alpha", slug="alpha")
        p2 = Project(name="Beta", slug="beta")
        session.add_all([p1, p2])
        session.flush()

        f1 = Feature(project_id=p1.id, name="F1", slug="f1")
        session.add(f1)
        session.flush()

        t1 = Task(feature_id=f1.id, title="T1", status="done")
        t2 = Task(feature_id=f1.id, title="T2", status="in_progress")
        session.add_all([t1, t2])
        session.flush()

        svc = PortfolioService(session)
        result = svc.get_overview()
        assert result["total_projects"] == 2
        assert result["total_tasks"] == 2
        assert len(result["projects"]) == 2

    def test_project_summary_in_overview(self, session):
        p = Project(name="Gamma", slug="gamma")
        session.add(p)
        session.flush()

        f = Feature(project_id=p.id, name="F1", slug="f1")
        session.add(f)
        session.flush()

        session.add(Task(feature_id=f.id, title="Done", status="done"))
        session.add(Task(feature_id=f.id, title="Active", status="in_progress"))
        session.add(Task(feature_id=f.id, title="Backlog", status="backlog"))
        session.flush()

        svc = PortfolioService(session)
        result = svc.get_overview()
        gamma = next(proj for proj in result["projects"] if proj["name"] == "Gamma")
        assert gamma["task_count"] == 3
        assert gamma["health_score"] == 100

    def test_portfolio_stats(self, session):
        p = Project(name="P1", slug="p1")
        session.add(p)
        session.flush()

        f = Feature(project_id=p.id, name="F1", slug="f1")
        session.add(f)
        session.flush()

        for status in ("done", "done", "in_progress", "backlog"):
            session.add(Task(feature_id=f.id, title=f"T-{status}", status=status))
        session.flush()

        svc = PortfolioService(session)
        result = svc.get_overview()
        assert result["total_tasks"] == 4
        assert result["tasks_by_status"]["done"] == 2
        assert result["tasks_by_status"]["in_progress"] == 1
