"""Tests for submit-for-review gate — TASK-0080."""

import pytest
from app.delivery.models import ClarificationRequest, Feature, Task  # noqa: F401
from app.projects.models import Project  # noqa: F401
from app.quality.models import (
    DoDItem,
)
from app.quality.service import EvidenceService, ReviewGateError, ReviewGateService
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


class TestReviewGateService:
    def test_pass_no_dod_no_evidence(self, session, task):
        """Task with no DoD items and no evidence passes gate."""
        svc = ReviewGateService(session)
        rr = svc.submit_for_review(task.id, requested_by_type="agent", requested_by_id="a1")
        assert rr.state == "pending"
        assert rr.task_id == task.id

    def test_pass_all_dod_passed(self, session, task):
        """Task with all DoD items passed passes gate."""
        dod = DoDItem(task_id=task.id, name="Tests pass", status="passed")
        session.add(dod)
        session.flush()

        svc = ReviewGateService(session)
        rr = svc.submit_for_review(task.id, requested_by_type="agent", requested_by_id="a1")
        assert rr.state == "pending"

    def test_fail_dod_not_passed(self, session, task):
        """Task with pending DoD items fails gate."""
        dod = DoDItem(task_id=task.id, name="Tests pass", status="pending")
        session.add(dod)
        session.flush()

        svc = ReviewGateService(session)
        with pytest.raises(ReviewGateError) as exc_info:
            svc.submit_for_review(task.id, requested_by_type="agent", requested_by_id="a1")
        assert "dod_not_satisfied" in str(exc_info.value)

    def test_fail_required_evidence_missing(self, session, task):
        """Task with DoD requiring evidence type but no matching evidence fails."""
        dod = DoDItem(
            task_id=task.id,
            name="Coverage >= 80%",
            status="passed",
            required_evidence_type="test_output",
        )
        session.add(dod)
        session.flush()

        svc = ReviewGateService(session)
        with pytest.raises(ReviewGateError) as exc_info:
            svc.submit_for_review(task.id, requested_by_type="agent", requested_by_id="a1")
        assert "evidence_required" in str(exc_info.value)

    def test_pass_required_evidence_present(self, session, task):
        """Task with required evidence type satisfied passes gate."""
        dod = DoDItem(
            task_id=task.id,
            name="Coverage >= 80%",
            status="passed",
            required_evidence_type="test_output",
        )
        session.add(dod)
        session.flush()

        ev = EvidenceService(session)
        ev.create(
            task_id=task.id,
            type="test_output",
            title="pytest output",
            created_by_type="agent",
            created_by_id="a1",
            dod_item_id=dod.id,
        )

        svc = ReviewGateService(session)
        rr = svc.submit_for_review(task.id, requested_by_type="agent", requested_by_id="a1")
        assert rr.state == "pending"

    def test_fail_blocking_clarification(self, session, task):
        """Task with open blocking clarification fails gate."""
        cr = ClarificationRequest(
            task_id=task.id,
            author_type="agent",
            author_id="a1",
            question="What do you mean?",
            blocking=True,
            state="open",
        )
        session.add(cr)
        session.flush()

        svc = ReviewGateService(session)
        with pytest.raises(ReviewGateError) as exc_info:
            svc.submit_for_review(task.id, requested_by_type="agent", requested_by_id="a1")
        assert "clarification_blocking" in str(exc_info.value)

    def test_pass_non_blocking_clarification(self, session, task):
        """Task with non-blocking clarification passes gate."""
        cr = ClarificationRequest(
            task_id=task.id,
            author_type="agent",
            author_id="a1",
            question="Minor question",
            blocking=False,
            state="open",
        )
        session.add(cr)
        session.flush()

        svc = ReviewGateService(session)
        rr = svc.submit_for_review(task.id, requested_by_type="agent", requested_by_id="a1")
        assert rr.state == "pending"

    def test_fail_task_not_in_progress(self, session, task):
        """Task not in claimed/in_progress state fails gate."""
        task.status = "backlog"
        session.flush()

        svc = ReviewGateService(session)
        with pytest.raises(ReviewGateError) as exc_info:
            svc.submit_for_review(task.id, requested_by_type="agent", requested_by_id="a1")
        assert "invalid_task_status" in str(exc_info.value)

    def test_pass_claimed_status(self, session, task):
        """Task in claimed state passes gate."""
        task.status = "claimed"
        session.flush()

        svc = ReviewGateService(session)
        rr = svc.submit_for_review(task.id, requested_by_type="agent", requested_by_id="a1")
        assert rr.state == "pending"
