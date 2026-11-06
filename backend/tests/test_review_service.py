"""Tests for ReviewRound service — TASK-0079."""

import pytest
from app.delivery.models import Feature, Task  # noqa: F401
from app.projects.models import Project  # noqa: F401
from app.quality.service import ReviewRoundService
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

    # Shared engine is process-wide (TASK-0112): other tests COMMIT rows
    # (e.g. Project slug='test' via test_analytics) whose residue survives
    # their teardown — create_all alone is a no-op on live tables, so the
    # canonical inserts below hit UNIQUE collisions under CI's xdist
    # ordering. Fresh schema per test: drop then create (setup side).
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


@pytest.fixture()
def task(session, feature):
    t = Task(feature_id=feature.id, title="T1", status="in_progress")
    session.add(t)
    session.flush()
    return t


class TestReviewRoundService:
    def test_create(self, session, task):
        svc = ReviewRoundService(session)
        rr = svc.create(
            task_id=task.id,
            requested_by_type="agent",
            requested_by_id="a1",
        )
        assert rr.id is not None
        assert rr.state == "pending"

    def test_create_with_reviewer(self, session, task):
        svc = ReviewRoundService(session)
        rr = svc.create(
            task_id=task.id,
            requested_by_type="human",
            requested_by_id="u1",
            reviewer_type="agent",
            reviewer_id="reviewer-1",
        )
        assert rr.reviewer_type == "agent"
        assert rr.reviewer_id == "reviewer-1"

    def test_get(self, session, task):
        svc = ReviewRoundService(session)
        rr = svc.create(task_id=task.id, requested_by_type="agent", requested_by_id="a1")
        found = svc.get(rr.id)
        assert found.id == rr.id

    def test_get_not_found(self, session):
        svc = ReviewRoundService(session)
        with pytest.raises(NotFound):
            svc.get("nonexistent")

    def test_list_by_task(self, session, task):
        svc = ReviewRoundService(session)
        svc.create(task_id=task.id, requested_by_type="agent", requested_by_id="a1")
        svc.create(task_id=task.id, requested_by_type="agent", requested_by_id="a2")
        items = svc.list_by_task(task.id)
        assert len(items) == 2

    def test_start(self, session, task):
        svc = ReviewRoundService(session)
        rr = svc.create(task_id=task.id, requested_by_type="agent", requested_by_id="a1")
        started = svc.start(rr.id)
        assert started.state == "in_progress"
        assert started.started_at is not None

    def test_start_completed_round_fails(self, session, task):
        svc = ReviewRoundService(session)
        rr = svc.create(task_id=task.id, requested_by_type="agent", requested_by_id="a1")
        svc.start(rr.id)
        svc.submit_verdict(rr.id, verdict="approve", confidence=90, summary="LGTM")
        with pytest.raises(Conflict):
            svc.start(rr.id)

    def test_add_finding(self, session, task):
        svc = ReviewRoundService(session)
        rr = svc.create(task_id=task.id, requested_by_type="agent", requested_by_id="a1")
        f = svc.add_finding(
            rr.id,
            severity="major",
            category="correctness",
            message="Missing null check",
        )
        assert f.id is not None
        assert f.review_round_id == rr.id

    def test_add_finding_completed_round_fails(self, session, task):
        svc = ReviewRoundService(session)
        rr = svc.create(task_id=task.id, requested_by_type="agent", requested_by_id="a1")
        svc.start(rr.id)
        svc.submit_verdict(rr.id, verdict="approve", confidence=90, summary="LGTM")
        with pytest.raises(Conflict):
            svc.add_finding(rr.id, severity="minor", category="style", message="Nit")

    def test_submit_verdict(self, session, task):
        svc = ReviewRoundService(session)
        rr = svc.create(task_id=task.id, requested_by_type="agent", requested_by_id="a1")
        svc.start(rr.id)
        completed = svc.submit_verdict(rr.id, verdict="approve", confidence=95, summary="All good")
        assert completed.state == "completed"
        assert completed.verdict == "approve"
        assert completed.confidence == 95
        assert completed.completed_at is not None

    def test_submit_verdict_pending_round_fails(self, session, task):
        svc = ReviewRoundService(session)
        rr = svc.create(task_id=task.id, requested_by_type="agent", requested_by_id="a1")
        with pytest.raises(Conflict):
            svc.submit_verdict(rr.id, verdict="approve", confidence=90, summary="LGTM")

    def test_verdict_values(self, session, task):
        svc = ReviewRoundService(session)
        for verdict in ("approve", "reject", "needs_changes"):
            rr = svc.create(task_id=task.id, requested_by_type="agent", requested_by_id="a1")
            svc.start(rr.id)
            completed = svc.submit_verdict(rr.id, verdict=verdict, confidence=80, summary=verdict)
            assert completed.verdict == verdict

    def test_list_findings(self, session, task):
        svc = ReviewRoundService(session)
        rr = svc.create(task_id=task.id, requested_by_type="agent", requested_by_id="a1")
        svc.add_finding(rr.id, severity="critical", category="security", message="SQL injection")
        svc.add_finding(rr.id, severity="minor", category="style", message="Missing docstring")
        findings = svc.list_findings(rr.id)
        assert len(findings) == 2
