"""Full lifecycle integration test.

Project → Feature → Task → Evidence → Review → Complete
"""

import uuid

import pytest
from app.delivery.service import FeatureService, TaskService
from app.projects.models import Project
from app.quality.service import (
    AcceptanceCriterionService,
    DoDItemService,
    EvidenceService,
    ReviewRoundService,
)
from sqlalchemy.orm import Session


def _make_project(session: Session) -> Project:
    slug = f"life-{uuid.uuid4().hex[:8]}"
    p = Project(name="Lifecycle Test", slug=slug, description="Lifecycle test")
    session.add(p)
    session.flush()
    return p


class TestFullLifecycle:
    """End-to-end: create project → feature → task → submit evidence → review → complete."""

    def test_happy_path(self, db_session: Session) -> None:
        project = _make_project(db_session)

        # 1. Create feature
        fs = FeatureService(db_session)
        feature = fs.create(project_id=str(project.id), name="Auth Module")
        assert feature.status == "backlog"

        # 2. Create task
        ts = TaskService(db_session)
        task = ts.create(feature_id=str(feature.id), title="Implement login")
        assert task.status == "backlog"

        # 3. Add DoD items
        ds = DoDItemService(db_session)
        dod1 = ds.create(task_id=str(task.id), name="Tests pass")
        dod2 = ds.create(task_id=str(task.id), name="Code reviewed")

        # 4. Add acceptance criteria
        acs = AcceptanceCriterionService(db_session)
        ac = acs.create(task_id=str(task.id), description="User can log in with email")
        assert ac.status == "pending"

        # 5. Submit evidence
        es = EvidenceService(db_session)
        evidence = es.create(
            task_id=str(task.id),
            type="test_result",
            title="test_output.txt",
            created_by_type="agent",
            created_by_id="agent-1",
        )
        assert evidence.verification_state == "unverified"

        # 6. Verify and accept evidence
        es.verify(str(evidence.id), verified_by_type="agent", verified_by_id="agent-1")
        evidence = es.get(str(evidence.id))
        assert evidence.verification_state == "agent_verified"

        es.accept(str(evidence.id), verified_by_type="human", verified_by_id="user-1")
        evidence = es.get(str(evidence.id))
        assert evidence.verification_state == "human_accepted"

        # 7. Pass DoD items
        ds.update(str(dod1.id), status="passed")
        ds.update(str(dod2.id), status="passed")

        # 8. Complete task
        task = ts.complete(str(task.id))
        assert task.status == "done"

    def test_complete_fails_with_unpassed_dod(self, db_session: Session) -> None:
        project = _make_project(db_session)
        fs = FeatureService(db_session)
        feature = fs.create(project_id=str(project.id), name="Feature")
        ts = TaskService(db_session)
        task = ts.create(feature_id=str(feature.id), title="Task")

        ds = DoDItemService(db_session)
        ds.create(task_id=str(task.id), name="Tests pass")

        from app.quality.service import QualityError

        with pytest.raises(QualityError):
            ts.complete(str(task.id))

    def test_task_valid_transitions(self, db_session: Session) -> None:
        project = _make_project(db_session)
        fs = FeatureService(db_session)
        feature = fs.create(project_id=str(project.id), name="Feature")
        ts = TaskService(db_session)
        task = ts.create(feature_id=str(feature.id), title="Task")

        task = ts.update(str(task.id), status="ready")
        assert task.status == "ready"

        task = ts.update(str(task.id), status="claimed")
        assert task.status == "claimed"

        task = ts.update(str(task.id), status="in_progress")
        assert task.status == "in_progress"

        task = ts.update(str(task.id), status="ready_for_review")
        assert task.status == "ready_for_review"

    def test_invalid_transition_raises(self, db_session: Session) -> None:
        from app.delivery.lifecycle import InvalidTransition

        project = _make_project(db_session)
        fs = FeatureService(db_session)
        feature = fs.create(project_id=str(project.id), name="Feature")
        ts = TaskService(db_session)
        task = ts.create(feature_id=str(feature.id), title="Task")

        with pytest.raises(InvalidTransition):
            ts.update(str(task.id), status="done")

    def test_evidence_reject_flow(self, db_session: Session) -> None:
        project = _make_project(db_session)
        fs = FeatureService(db_session)
        feature = fs.create(project_id=str(project.id), name="Feature")
        ts = TaskService(db_session)
        task = ts.create(feature_id=str(feature.id), title="Task")

        es = EvidenceService(db_session)
        evidence = es.create(
            task_id=str(task.id),
            type="code_review",
            title="review.md",
            created_by_type="human",
            created_by_id="user-1",
        )

        es.reject(str(evidence.id), verified_by_type="human", verified_by_id="user-1")
        evidence = es.get(str(evidence.id))
        assert evidence.verification_state == "rejected"

    def test_review_round_flow(self, db_session: Session) -> None:
        project = _make_project(db_session)
        fs = FeatureService(db_session)
        feature = fs.create(project_id=str(project.id), name="Feature")
        ts = TaskService(db_session)
        task = ts.create(feature_id=str(feature.id), title="Task")

        rrs = ReviewRoundService(db_session)
        rnd = rrs.create(
            task_id=str(task.id),
            requested_by_type="agent",
            requested_by_id="agent-1",
        )
        assert rnd.state == "pending"

        rrs.start(str(rnd.id))
        rnd = rrs.get(str(rnd.id))
        assert rnd.state == "in_progress"

        finding = rrs.add_finding(
            round_id=str(rnd.id),
            severity="minor",
            category="style",
            message="Missing docstring",
        )
        assert finding.severity == "minor"

        rrs.submit_verdict(
            round_id=str(rnd.id), verdict="approved", confidence=90, summary="Looks good"
        )
        rnd = rrs.get(str(rnd.id))
        assert rnd.verdict == "approved"
