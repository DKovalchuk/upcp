"""Quality-side agent-tab reads — TASK-0176 (red first).

``EvidenceService.list_by_creator`` / ``ReviewRoundService.list_by_reviewer``
are the public reads the ``GET /agents/{id}/evidence|reviews`` tabs must
consume instead of querying ``quality.models`` from identity. Red on the
old code (the methods do not exist yet), green once they land.
"""

from datetime import UTC, datetime

from app.delivery.models import Feature, Task
from app.projects.models import Project
from app.quality.models import Evidence, ReviewRound
from app.quality.service import EvidenceService, ReviewRoundService
from app.shared.text import new_id
from sqlalchemy.orm import Session

_AGENT = "agent-under-test"
_OTHER = "other-agent"
_T1 = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
_T2 = datetime(2026, 1, 2, 12, 0, 0, tzinfo=UTC)


def _seed_task(session: Session) -> Task:
    """FK-enforced engine: parents must be flushed before the task."""
    p = Project(name="QP", slug="qp")
    session.add(p)
    session.flush()
    f = Feature(project_id=p.id, name="QF", slug="qf")
    session.add(f)
    session.flush()
    t = Task(feature_id=f.id, title="QT", status="ready")
    session.add(t)
    session.flush()
    return t


class TestEvidenceListByCreator:
    def test_empty(self, db_session: Session) -> None:
        assert EvidenceService(db_session).list_by_creator(_AGENT) == []

    def test_only_creator_newest_limited(self, db_session: Session) -> None:
        task = _seed_task(db_session)
        e_old = Evidence(
            id=new_id(),
            task_id=task.id,
            type="file",
            title="old",
            created_by_type="agent",
            created_by_id=_AGENT,
            created_at=_T1,
        )
        e_new = Evidence(
            id=new_id(),
            task_id=task.id,
            type="file",
            title="new",
            created_by_type="agent",
            created_by_id=_AGENT,
            created_at=_T2,
        )
        foreign = Evidence(
            id=new_id(),
            task_id=task.id,
            type="file",
            title="other",
            created_by_type="agent",
            created_by_id=_OTHER,
            created_at=_T2,
        )
        db_session.add_all([e_old, e_new, foreign])
        db_session.flush()
        svc = EvidenceService(db_session)
        assert [e.id for e in svc.list_by_creator(_AGENT)] == [e_new.id, e_old.id]
        assert [e.id for e in svc.list_by_creator(_AGENT, limit=1)] == [e_new.id]
        assert [e.id for e in svc.list_by_creator(_OTHER)] == [foreign.id]


class TestReviewListByReviewer:
    def test_empty(self, db_session: Session) -> None:
        assert ReviewRoundService(db_session).list_by_reviewer(_AGENT) == []

    def test_only_reviewer_newest_limited(self, db_session: Session) -> None:
        task = _seed_task(db_session)

        def _round(round_id: str, reviewer_id: str | None, created: datetime) -> ReviewRound:
            rr = ReviewRound(
                id=round_id,
                task_id=task.id,
                requested_by_type="agent",
                requested_by_id=_AGENT,
                reviewer_id=reviewer_id,
                created_at=created,
            )
            db_session.add(rr)
            db_session.flush()
            return rr

        _round("rr-old", _AGENT, _T1)
        _round("rr-new", _AGENT, _T2)
        _round("rr-foreign", _OTHER, _T2)
        _round("rr-unassigned", None, _T2)
        svc = ReviewRoundService(db_session)
        assert [r.id for r in svc.list_by_reviewer(_AGENT)] == ["rr-new", "rr-old"]
        assert [r.id for r in svc.list_by_reviewer(_AGENT, limit=1)] == ["rr-new"]
        assert [r.id for r in svc.list_by_reviewer(_OTHER)] == ["rr-foreign"]
        assert svc.list_by_reviewer("nobody") == []
