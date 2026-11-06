"""Comprehensive unit tests for quality service layer.

Tests EvidenceService, ReviewRoundService, AcceptanceCriterionService,
DoDItemService, and QualityStatsService.
"""

import uuid

import pytest
from app.delivery.models import Feature, Task
from app.projects.models import Project
from app.quality.service import (
    AcceptanceCriterionService,
    DoDItemService,
    EvidenceService,
    QualityStatsService,
    ReviewRoundService,
)
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
    slug = f"qtest-{uuid.uuid4().hex[:8]}"
    p = Project(name="Test Project", slug=slug)
    session.add(p)
    session.flush()
    return p


@pytest.fixture()
def feature(session, project):
    slug = f"qfeat-{uuid.uuid4().hex[:8]}"
    f = Feature(project_id=project.id, name="Test Feature", slug=slug)
    session.add(f)
    session.flush()
    return f


@pytest.fixture()
def task(session, feature):
    t = Task(feature_id=feature.id, title="Test Task", status="in_progress")
    session.add(t)
    session.flush()
    return t


# ── EvidenceService Tests ─────────────────────────────────────


class TestEvidenceService:
    def test_create_evidence(self, session, task):
        svc = EvidenceService(session)
        e = svc.create(
            task_id=task.id,
            type="commit",
            title="Initial commit",
            created_by_type="agent",
            created_by_id="a1",
        )
        assert e.id is not None
        assert e.type == "commit"
        assert e.title == "Initial commit"
        assert e.verification_state == "unverified"

    def test_get_evidence(self, session, task):
        svc = EvidenceService(session)
        e = svc.create(
            task_id=task.id,
            type="test_output",
            title="pytest output",
            created_by_type="agent",
            created_by_id="a1",
        )
        found = svc.get(e.id)
        assert found.id == e.id
        assert found.title == "pytest output"

    def test_get_evidence_not_found(self, session):
        svc = EvidenceService(session)
        with pytest.raises(NotFound):
            svc.get("nonexistent-id")

    def test_list_evidence_by_task(self, session, task):
        svc = EvidenceService(session)
        svc.create(
            task_id=task.id, type="commit", title="C1", created_by_type="agent", created_by_id="a1"
        )
        svc.create(
            task_id=task.id,
            type="test_output",
            title="T1",
            created_by_type="agent",
            created_by_id="a1",
        )
        items, total = svc.list_by_task(task.id)
        assert total == 2
        assert len(items) == 2

    def test_verify_evidence(self, session, task):
        svc = EvidenceService(session)
        e = svc.create(
            task_id=task.id, type="commit", title="C1", created_by_type="agent", created_by_id="a1"
        )
        verified = svc.verify(e.id, verified_by_type="agent", verified_by_id="a1")
        assert verified.verification_state == "agent_verified"
        assert verified.verified_at is not None

    def test_accept_evidence(self, session, task):
        svc = EvidenceService(session)
        e = svc.create(
            task_id=task.id, type="commit", title="C1", created_by_type="agent", created_by_id="a1"
        )
        accepted = svc.accept(e.id, verified_by_type="human", verified_by_id="u1")
        assert accepted.verification_state == "human_accepted"

    def test_reject_evidence(self, session, task):
        svc = EvidenceService(session)
        e = svc.create(
            task_id=task.id,
            type="screenshot",
            title="S1",
            created_by_type="agent",
            created_by_id="a1",
        )
        rejected = svc.reject(e.id, verified_by_type="human", verified_by_id="u1")
        assert rejected.verification_state == "rejected"

    def test_invalid_transition_conflict(self, session, task):
        svc = EvidenceService(session)
        e = svc.create(
            task_id=task.id, type="commit", title="C1", created_by_type="agent", created_by_id="a1"
        )
        svc.accept(e.id, verified_by_type="human", verified_by_id="u1")
        with pytest.raises(Conflict):
            svc.verify(e.id, verified_by_type="agent", verified_by_id="a1")


# ── ReviewRoundService Tests ──────────────────────────────────


class TestReviewRoundService:
    def test_create_round(self, session, task):
        svc = ReviewRoundService(session)
        rr = svc.create(
            task_id=task.id,
            requested_by_type="agent",
            requested_by_id="a1",
        )
        assert rr.id is not None
        assert rr.state == "pending"

    def test_get_round(self, session, task):
        svc = ReviewRoundService(session)
        rr = svc.create(task_id=task.id, requested_by_type="agent", requested_by_id="a1")
        found = svc.get(rr.id)
        assert found.id == rr.id

    def test_get_round_not_found(self, session):
        svc = ReviewRoundService(session)
        with pytest.raises(NotFound):
            svc.get("nonexistent-id")

    def test_list_rounds_by_task(self, session, task):
        svc = ReviewRoundService(session)
        svc.create(task_id=task.id, requested_by_type="agent", requested_by_id="a1")
        svc.create(task_id=task.id, requested_by_type="agent", requested_by_id="a2")
        items, total = svc.list_by_task(task.id)
        assert total == 2
        assert len(items) == 2

    def test_start_round(self, session, task):
        svc = ReviewRoundService(session)
        rr = svc.create(task_id=task.id, requested_by_type="agent", requested_by_id="a1")
        started = svc.start(rr.id)
        assert started.state == "in_progress"
        assert started.started_at is not None

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
        assert f.severity == "major"

    def test_submit_verdict(self, session, task):
        svc = ReviewRoundService(session)
        rr = svc.create(task_id=task.id, requested_by_type="agent", requested_by_id="a1")
        svc.start(rr.id)
        completed = svc.submit_verdict(rr.id, verdict="approve", confidence=90, summary="LGTM")
        assert completed.state == "completed"
        assert completed.verdict == "approve"
        assert completed.confidence == 90
        assert completed.completed_at is not None

    def test_list_findings(self, session, task):
        svc = ReviewRoundService(session)
        rr = svc.create(task_id=task.id, requested_by_type="agent", requested_by_id="a1")
        svc.add_finding(rr.id, severity="critical", category="security", message="SQL injection")
        svc.add_finding(rr.id, severity="minor", category="style", message="Missing docstring")
        findings = svc.list_findings(rr.id)
        assert len(findings) == 2

    def test_invalid_start_conflict(self, session, task):
        svc = ReviewRoundService(session)
        rr = svc.create(task_id=task.id, requested_by_type="agent", requested_by_id="a1")
        svc.start(rr.id)
        svc.submit_verdict(rr.id, verdict="approve", confidence=90, summary="LGTM")
        with pytest.raises(Conflict):
            svc.start(rr.id)


# ── AcceptanceCriterionService Tests ──────────────────────────


class TestAcceptanceCriterionService:
    def test_create_ac(self, session, task):
        svc = AcceptanceCriterionService(session)
        ac = svc.create(task_id=task.id, description="Must return 200 OK")
        assert ac.id is not None
        assert ac.description == "Must return 200 OK"
        assert ac.status == "pending"

    def test_get_ac(self, session, task):
        svc = AcceptanceCriterionService(session)
        ac = svc.create(task_id=task.id, description="Must return 200 OK")
        found = svc.get(ac.id)
        assert found.id == ac.id

    def test_get_ac_not_found(self, session):
        svc = AcceptanceCriterionService(session)
        with pytest.raises(NotFound):
            svc.get("nonexistent-id")

    def test_update_ac(self, session, task):
        svc = AcceptanceCriterionService(session)
        ac = svc.create(task_id=task.id, description="Must return 200 OK")
        updated = svc.update(ac.id, status="passed")
        assert updated.status == "passed"

    def test_delete_ac(self, session, task):
        svc = AcceptanceCriterionService(session)
        ac = svc.create(task_id=task.id, description="Must return 200 OK")
        svc.delete(ac.id)
        with pytest.raises(NotFound):
            svc.get(ac.id)

    def test_list_ac_by_task(self, session, task):
        svc = AcceptanceCriterionService(session)
        svc.create(task_id=task.id, description="AC 1")
        svc.create(task_id=task.id, description="AC 2")
        items, total = svc.list_by_task(task.id)
        assert total == 2
        assert len(items) == 2


# ── DoDItemService Tests ──────────────────────────────────────


class TestDoDItemService:
    def test_create_dod_item(self, session, task):
        svc = DoDItemService(session)
        item = svc.create(task_id=task.id, name="All tests pass")
        assert item.id is not None
        assert item.name == "All tests pass"
        assert item.status == "pending"

    def test_get_dod_item(self, session, task):
        svc = DoDItemService(session)
        item = svc.create(task_id=task.id, name="All tests pass")
        found = svc.get(item.id)
        assert found.id == item.id

    def test_get_dod_item_not_found(self, session):
        svc = DoDItemService(session)
        with pytest.raises(NotFound):
            svc.get("nonexistent-id")

    def test_update_dod_item(self, session, task):
        svc = DoDItemService(session)
        item = svc.create(task_id=task.id, name="All tests pass")
        updated = svc.update(item.id, status="passed")
        assert updated.status == "passed"

    def test_delete_dod_item(self, session, task):
        svc = DoDItemService(session)
        item = svc.create(task_id=task.id, name="All tests pass")
        svc.delete(item.id)
        with pytest.raises(NotFound):
            svc.get(item.id)

    def test_list_dod_items_by_task(self, session, task):
        svc = DoDItemService(session)
        svc.create(task_id=task.id, name="Item 1")
        svc.create(task_id=task.id, name="Item 2")
        items, total = svc.list_by_task(task.id)
        assert total == 2
        assert len(items) == 2


# ── QualityStatsService Tests ─────────────────────────────────


class TestQualityStatsService:
    def test_get_stats_empty_project(self, session, project):
        svc = QualityStatsService(session)
        stats = svc.get_quality_stats(project.id)
        assert stats["total_tasks"] == 0
        assert stats["pass_rate"] == 0.0

    def test_get_stats_nonexistent_project(self, session):
        svc = QualityStatsService(session)
        with pytest.raises(NotFound):
            svc.get_quality_stats("nonexistent-id")

    def test_get_stats_with_tasks(self, session, task, project):
        svc = QualityStatsService(session)
        stats = svc.get_quality_stats(project.id)
        assert stats["total_tasks"] == 1

    def test_get_stats_with_ac(self, session, task, project):
        from app.quality.service import AcceptanceCriterionService

        ac_svc = AcceptanceCriterionService(session)
        ac_svc.create(task_id=task.id, description="AC 1")
        ac_svc.create(task_id=task.id, description="AC 2")

        stats_svc = QualityStatsService(session)
        stats = stats_svc.get_quality_stats(project.id)
        assert stats["total_ac"] == 2
        assert stats["tasks_with_ac"] == 1

    def test_get_stats_with_passed_items(self, session, task, project):
        from app.quality.service import AcceptanceCriterionService, DoDItemService

        ac_svc = AcceptanceCriterionService(session)
        ac = ac_svc.create(task_id=task.id, description="AC 1")
        ac_svc.update(ac.id, status="passed")

        dod_svc = DoDItemService(session)
        dod = dod_svc.create(task_id=task.id, name="DoD 1")
        dod_svc.update(dod.id, status="passed")

        stats_svc = QualityStatsService(session)
        stats = stats_svc.get_quality_stats(project.id)
        assert stats["passed_ac"] == 1
        assert stats["passed_dod"] == 1
        assert stats["pass_rate"] == 100.0
