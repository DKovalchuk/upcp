"""Owner-context read services behind the agent endpoints — TASK-0176 (red first).

Pins the public read contract consumed by ``identity/agent_endpoints.py``
and ``api/v1/agent_self.py`` instead of their current foreign-model
queries: ``AgentActivityService`` (delivery). Red on the old code (the
service does not exist yet), green once it lands. The quality-side reads
live in ``test_agent_quality_tab_reads.py``.
"""

from datetime import UTC, datetime

from app.delivery.models import (
    AgentInboxEvent,
    ClarificationRequest,
    Feature,
    Heartbeat,
    Task,
    TaskClaim,
)
from app.delivery.service import AgentActivityService
from app.projects.models import Project
from app.shared.text import new_id
from sqlalchemy.orm import Session

_AGENT = "agent-under-test"
_OTHER = "other-agent"
_T1 = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
_T2 = datetime(2026, 1, 2, 12, 0, 0, tzinfo=UTC)


def _aware(dt: datetime) -> datetime:
    """SQLite returns naive datetimes; normalize for comparison."""
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt


def _seed_task(session: Session, n: int = 1) -> Task:
    """FK-enforced engine: parents must be flushed before the task."""
    p = Project(name=f"P{n}", slug=f"p{n}")
    session.add(p)
    session.flush()
    f = Feature(project_id=p.id, name=f"F{n}", slug=f"f{n}")
    session.add(f)
    session.flush()
    t = Task(feature_id=f.id, title=f"T{n}", status="ready")
    session.add(t)
    session.flush()
    return t


def _claim(
    session: Session,
    task: Task,
    agent_id: str,
    *,
    state: str = "active",
    claimed_at: datetime | None = None,
) -> TaskClaim:
    c = TaskClaim(
        id=new_id(),
        task_id=task.id,
        agent_id=agent_id,
        state=state,
        claimed_at=claimed_at or _T1,
    )
    session.add(c)
    session.flush()
    return c


# ── delivery: AgentActivityService ───────────────────────────────────────────


class TestCountClaims:
    def test_empty(self, db_session: Session) -> None:
        assert AgentActivityService(db_session).count_claims(_AGENT) == 0

    def test_total_and_by_state(self, db_session: Session) -> None:
        task = _seed_task(db_session)
        _claim(db_session, task, _AGENT, state="completed")
        _claim(db_session, task, _AGENT, state="completed")
        _claim(db_session, task, _AGENT, state="active")
        svc = AgentActivityService(db_session)
        assert svc.count_claims(_AGENT) == 3
        assert svc.count_claims(_AGENT, state="completed") == 2
        assert svc.count_claims(_AGENT, state="expired") == 0

    def test_other_agent_not_counted(self, db_session: Session) -> None:
        task = _seed_task(db_session)
        _claim(db_session, task, _OTHER, state="completed")
        assert AgentActivityService(db_session).count_claims(_AGENT) == 0


class TestActiveClaim:
    def test_none(self, db_session: Session) -> None:
        assert AgentActivityService(db_session).get_active_claim(_AGENT) is None

    def test_returns_only_active(self, db_session: Session) -> None:
        task = _seed_task(db_session)
        _claim(db_session, task, _AGENT, state="completed")
        active = _claim(db_session, task, _AGENT, state="active")
        svc = AgentActivityService(db_session)
        got = svc.get_active_claim(_AGENT)
        assert got is not None
        assert got.id == active.id
        assert AgentActivityService(db_session).get_active_claim(_OTHER) is None


class TestLastClaimedAt:
    def test_none_when_no_claims(self, db_session: Session) -> None:
        assert AgentActivityService(db_session).last_claimed_at(_AGENT) is None

    def test_returns_newest_claim_time(self, db_session: Session) -> None:
        # Partial unique index: one ACTIVE claim per task — use two tasks.
        t1 = _seed_task(db_session, n=1)
        t2 = _seed_task(db_session, n=2)
        _claim(db_session, t1, _AGENT, claimed_at=_T1)
        _claim(db_session, t2, _AGENT, claimed_at=_T2)
        got = AgentActivityService(db_session).last_claimed_at(_AGENT)
        assert got is not None
        assert _aware(got) == _T2


class TestListClaims:
    def test_empty(self, db_session: Session) -> None:
        assert AgentActivityService(db_session).list_claims(_AGENT) == []

    def test_newest_first_and_limited(self, db_session: Session) -> None:
        # Partial unique index: one ACTIVE claim per task — use three tasks.
        t1 = _seed_task(db_session, n=1)
        t2 = _seed_task(db_session, n=2)
        t3 = _seed_task(db_session, n=3)
        _claim(db_session, t1, _AGENT, claimed_at=_T1)
        _claim(db_session, t2, _AGENT, claimed_at=_T2)
        _claim(db_session, t3, _OTHER, claimed_at=_T2)
        svc = AgentActivityService(db_session)
        claims = svc.list_claims(_AGENT, limit=1)
        assert len(claims) == 1
        assert claims[0].agent_id == _AGENT
        assert _aware(claims[0].claimed_at) == _T2
        assert len(svc.list_claims(_AGENT)) == 2


class TestLatestHeartbeat:
    def test_none_for_unknown_claim(self, db_session: Session) -> None:
        assert AgentActivityService(db_session).get_latest_heartbeat("no-such") is None

    def test_returns_newest_by_created_at(self, db_session: Session) -> None:
        task = _seed_task(db_session)
        claim = _claim(db_session, task, _AGENT)
        older = Heartbeat(
            id=new_id(),
            claim_id=claim.id,
            progress_percent=10,
            current_step="a",
            next_step="b",
            created_at=_T1,
        )
        newer = Heartbeat(
            id=new_id(),
            claim_id=claim.id,
            progress_percent=90,
            current_step="b",
            next_step="c",
            created_at=_T2,
        )
        db_session.add_all([older, newer])
        db_session.flush()
        got = AgentActivityService(db_session).get_latest_heartbeat(claim.id)
        assert got is not None
        assert got.id == newer.id
        assert got.progress_percent == 90


class TestListTasksByIds:
    def test_empty_ids(self, db_session: Session) -> None:
        assert AgentActivityService(db_session).list_tasks_by_ids([]) == []

    def test_returns_only_matching(self, db_session: Session) -> None:
        t1 = _seed_task(db_session, n=1)
        t2 = _seed_task(db_session, n=2)
        svc = AgentActivityService(db_session)
        got = svc.list_tasks_by_ids([t1.id, "missing-id"])
        assert [t.id for t in got] == [t1.id]
        assert svc.list_tasks_by_ids([t2.id])[0].id == t2.id


class TestListInboxEvents:
    def test_empty(self, db_session: Session) -> None:
        assert AgentActivityService(db_session).list_inbox_events(_AGENT) == []

    def test_own_events_unread_filter_and_limit(self, db_session: Session) -> None:
        read_ev = AgentInboxEvent(
            id=new_id(),
            agent_id=_AGENT,
            event_type="task.assigned",
            message="read one",
            is_read=True,
            created_at=_T1,
        )
        unread_ev = AgentInboxEvent(
            id=new_id(),
            agent_id=_AGENT,
            event_type="task.assigned",
            message="unread one",
            is_read=False,
            created_at=_T2,
        )
        foreign = AgentInboxEvent(
            id=new_id(),
            agent_id=_OTHER,
            event_type="task.assigned",
            message="not mine",
            created_at=_T2,
        )
        db_session.add_all([read_ev, unread_ev, foreign])
        db_session.flush()
        svc = AgentActivityService(db_session)
        all_own = svc.list_inbox_events(_AGENT, limit=50)
        assert [e.id for e in all_own] == [unread_ev.id, read_ev.id]
        unread = svc.list_inbox_events(_AGENT, unread_only=True, limit=50)
        assert [e.id for e in unread] == [unread_ev.id]
        assert svc.list_inbox_events(_OTHER, limit=50)[0].id == foreign.id


class TestClarificationReads:
    def test_list_by_author_only_newest_limited(self, db_session: Session) -> None:
        task = _seed_task(db_session)
        mine_old = ClarificationRequest(
            id=new_id(),
            task_id=task.id,
            author_type="agent",
            author_id=_AGENT,
            question="old?",
            created_at=_T1,
        )
        mine_new = ClarificationRequest(
            id=new_id(),
            task_id=task.id,
            author_type="agent",
            author_id=_AGENT,
            question="new?",
            created_at=_T2,
        )
        foreign = ClarificationRequest(
            id=new_id(),
            task_id=task.id,
            author_type="agent",
            author_id=_OTHER,
            question="other?",
            created_at=_T2,
        )
        db_session.add_all([mine_old, mine_new, foreign])
        db_session.flush()
        svc = AgentActivityService(db_session)
        assert [c.id for c in svc.list_clarifications(_AGENT)] == [mine_new.id, mine_old.id]
        assert len(svc.list_clarifications(_AGENT, limit=1)) == 1

    def test_count_filters_by_author_type_and_state(self, db_session: Session) -> None:
        task = _seed_task(db_session)
        rows = [
            ClarificationRequest(
                id=new_id(),
                task_id=task.id,
                author_type="agent",
                author_id=_AGENT,
                question="q",
                state="open",
            ),
            ClarificationRequest(
                id=new_id(),
                task_id=task.id,
                author_type="agent",
                author_id=_AGENT,
                question="q",
                state="answered",
                answer="a",
            ),
            ClarificationRequest(
                id=new_id(),
                task_id=task.id,
                author_type="user",
                author_id=_AGENT,
                question="q",
                state="open",
            ),
            ClarificationRequest(
                id=new_id(),
                task_id=task.id,
                author_type="agent",
                author_id=_OTHER,
                question="q",
                state="open",
            ),
        ]
        db_session.add_all(rows)
        db_session.flush()
        svc = AgentActivityService(db_session)
        assert svc.count_clarifications(_AGENT) == 3
        assert svc.count_clarifications(_AGENT, author_type="agent") == 2
        assert svc.count_clarifications(_AGENT, author_type="agent", state="open") == 1
        assert svc.count_clarifications(_OTHER, author_type="agent", state="open") == 1
