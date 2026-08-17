"""Tests for Evidence, ReviewRound, ReviewFinding models — TASK-0077."""

import pytest
from app.delivery.models import Feature, Task  # noqa: F401
from app.projects.models import Project  # noqa: F401
from app.quality.models import (
    DoDItem,
    Evidence,
    ReviewFinding,
    ReviewRound,
)
from app.shared.database import Base

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


class TestEvidenceModel:
    def test_create_evidence(self, session, task):
        e = Evidence(
            task_id=task.id,
            type="commit",
            title="Initial commit",
            description="First implementation",
            url="https://git.example.com/commit/abc123",
            content_snippet="diff --git a/file.py",
            created_by_type="agent",
            created_by_id="agent-1",
        )
        session.add(e)
        session.flush()
        assert e.id is not None
        assert e.verification_state == "unverified"
        assert e.created_at is not None

    def test_evidence_optional_fields(self, session, task):
        e = Evidence(
            task_id=task.id,
            type="screenshot",
            title="UI screenshot",
            created_by_type="human",
            created_by_id="user-1",
        )
        session.add(e)
        session.flush()
        assert e.dod_item_id is None
        assert e.url is None
        assert e.content_snippet is None
        assert e.artifact_ref is None

    def test_evidence_with_dod_item(self, session, task):
        dod = DoDItem(task_id=task.id, name="Tests pass", required_evidence_type="test_output")
        session.add(dod)
        session.flush()

        e = Evidence(
            task_id=task.id,
            dod_item_id=dod.id,
            type="test_output",
            title="pytest output",
            created_by_type="agent",
            created_by_id="agent-1",
        )
        session.add(e)
        session.flush()
        assert e.dod_item_id == dod.id

    def test_evidence_type_values(self, session, task):
        """All valid evidence types can be created."""
        for etype in ("commit", "test_output", "screenshot", "log", "manual", "other"):
            e = Evidence(
                task_id=task.id,
                type=etype,
                title=f"Evidence {etype}",
                created_by_type="agent",
                created_by_id="a1",
            )
            session.add(e)
        session.flush()

    def test_dod_item_required_evidence_type(self, session, task):
        """DoDItem can have required_evidence_type."""
        dod = DoDItem(
            task_id=task.id,
            name="Coverage >= 80%",
            required_evidence_type="test_output",
        )
        session.add(dod)
        session.flush()
        assert dod.required_evidence_type == "test_output"


class TestReviewRoundModel:
    def test_create_review_round(self, session, task):
        rr = ReviewRound(
            task_id=task.id,
            requested_by_type="agent",
            requested_by_id="agent-1",
        )
        session.add(rr)
        session.flush()
        assert rr.id is not None
        assert rr.state == "pending"
        assert rr.verdict is None
        assert rr.created_at is not None

    def test_review_round_with_reviewer(self, session, task):
        rr = ReviewRound(
            task_id=task.id,
            requested_by_type="human",
            requested_by_id="user-1",
            reviewer_type="agent",
            reviewer_id="reviewer-agent",
        )
        session.add(rr)
        session.flush()
        assert rr.reviewer_type == "agent"
        assert rr.reviewer_id == "reviewer-agent"

    def test_review_round_verdict_values(self, session, task):
        """Verdict can be approve, reject, or needs_changes."""
        for verdict in ("approve", "reject", "needs_changes"):
            rr = ReviewRound(
                task_id=task.id,
                requested_by_type="agent",
                requested_by_id="a1",
                state="completed",
                verdict=verdict,
                confidence=85,
                summary=f"Verdict: {verdict}",
            )
            session.add(rr)
        session.flush()


class TestReviewFindingModel:
    def test_create_finding(self, session, task):
        rr = ReviewRound(
            task_id=task.id,
            requested_by_type="agent",
            requested_by_id="a1",
        )
        session.add(rr)
        session.flush()

        f = ReviewFinding(
            review_round_id=rr.id,
            severity="major",
            category="correctness",
            message="Missing null check",
            suggestion="Add guard clause",
        )
        session.add(f)
        session.flush()
        assert f.id is not None
        assert f.created_at is not None

    def test_finding_with_evidence_ref(self, session, task):
        rr = ReviewRound(
            task_id=task.id,
            requested_by_type="agent",
            requested_by_id="a1",
        )
        session.add(rr)
        session.flush()

        e = Evidence(
            task_id=task.id,
            type="test_output",
            title="Failing test",
            created_by_type="agent",
            created_by_id="a1",
        )
        session.add(e)
        session.flush()

        f = ReviewFinding(
            review_round_id=rr.id,
            severity="critical",
            category="correctness",
            message="Test fails on edge case",
            evidence_id=e.id,
        )
        session.add(f)
        session.flush()
        assert f.evidence_id == e.id

    def test_finding_severity_values(self, session, task):
        rr = ReviewRound(
            task_id=task.id,
            requested_by_type="agent",
            requested_by_id="a1",
        )
        session.add(rr)
        session.flush()

        for severity in ("critical", "major", "minor", "nit"):
            f = ReviewFinding(
                review_round_id=rr.id,
                severity=severity,
                category="other",
                message=f"Severity {severity}",
            )
            session.add(f)
        session.flush()

    def test_finding_category_values(self, session, task):
        rr = ReviewRound(
            task_id=task.id,
            requested_by_type="agent",
            requested_by_id="a1",
        )
        session.add(rr)
        session.flush()

        for cat in ("correctness", "completeness", "security", "performance", "style", "other"):
            f = ReviewFinding(
                review_round_id=rr.id,
                severity="minor",
                category=cat,
                message=f"Category {cat}",
            )
            session.add(f)
        session.flush()
