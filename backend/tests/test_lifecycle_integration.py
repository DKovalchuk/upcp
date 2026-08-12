"""Full lifecycle integration test.

Project → Feature → Task → Evidence → Review → Complete
"""

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


def _make_project(session: Session, slug: str = "test-project") -> Project:
    p = Project(name="Test Project", slug=slug, description="Lifecycle test")
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
            evidence_type="test_result",
            filename="test_output.txt",
            created_by_type="agent",
            created_by_id="agent-1",
        )
        assert evidence.status == "submitted"

        # 6. Verify and accept evidence
        es.verify(str(evidence.id), verified_by_type="human", verified_by_id="user-1")
        evidence = es.get(str(evidence.id))
        assert evidence.status == "verified"

        es.accept(str(evidence.id), verified_by_type="human", verified_by_id="user-1")
        evidence = es.get(str(evidence.id))
        assert evidence.status == "accepted"

        # 7. Pass DoD items
        ds.update(str(dod1.id), status="passed")
        ds.update(str(dod2.id), status="passed")

        # 8. Complete task
        task = ts.complete(str(task.id))
        assert task.status == "done"

        # Notifications may or may not be created depending on trigger wiring
        # The key assertion is that the lifecycle completes without error

    def test_complete_fails_with_unpassed_dod(self, db_session: Session) -> None:
        project = _make_project(db_session)
        fs = FeatureService(db_session)
        feature = fs.create(project_id=str(project.id), name="Feature")
        ts = TaskService(db_session)
        task = ts.create(feature_id=str(feature.id), title="Task")

        ds = DoDItemService(db_session)
        ds.create(task_id=str(task.id), name="Tests pass")

        # Try to complete without passing DoD
        from app.quality.service import QualityError

        with pytest.raises(QualityError):
            ts.complete(str(task.id))

    def test_task_status_transition(self, db_session: Session) -> None:
        project = _make_project(db_session)
        fs = FeatureService(db_session)
        feature = fs.create(project_id=str(project.id), name="Feature")
        ts = TaskService(db_session)
        task = ts.create(feature_id=str(feature.id), title="Task")

        # Valid transition: backlog → in_progress
        task = ts.update(str(task.id), status="in_progress")
        assert task.status == "in_progress"

        # Valid transition: in_progress → review
        task = ts.update(str(task.id), status="review")
        assert task.status == "review"

    def test_invalid_transition_raises(self, db_session: Session) -> None:
        from app.delivery.lifecycle import InvalidTransition

        project = _make_project(db_session)
        fs = FeatureService(db_session)
        feature = fs.create(project_id=str(project.id), name="Feature")
        ts = TaskService(db_session)
        task = ts.create(feature_id=str(feature.id), title="Task")

        # Invalid transition: backlog → done
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
            evidence_type="code_review",
            filename="review.md",
        )

        es.reject(str(evidence.id), verified_by_type="human", verified_by_id="user-1")
        evidence = es.get(str(evidence.id))
        assert evidence.status == "rejected"

    def test_review_round_flow(self, db_session: Session) -> None:
        project = _make_project(db_session)
        fs = FeatureService(db_session)
        feature = fs.create(project_id=str(project.id), name="Feature")
        ts = TaskService(db_session)
        task = ts.create(feature_id=str(feature.id), title="Task")

        rrs = ReviewRoundService(db_session)
        rnd = rrs.create(task_id=str(task.id), round_number=1)
        assert rnd.status == "pending"

        rrs.start(str(rnd.id))
        rnd = rrs.get(str(rnd.id))
        assert rnd.status == "in_progress"

        finding = rrs.add_finding(
            round_id=str(rnd.id),
            severity="minor",
            description="Missing docstring",
        )
        assert finding.severity == "minor"

        rrs.submit_verdict(round_id=str(rnd.id), verdict="approved", summary="Looks good")
        rnd = rrs.get(str(rnd.id))
        assert rnd.verdict == "approved"
