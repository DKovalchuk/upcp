"""Dashboard aggregate health — TASK-0149 red→green (TASK-0140 perf finding).

Root cause of 1.06–1.33s @394 projects: ``_get_health_score()`` looped
``get_project_health()`` once per project (≈6 queries each).

AC1 (red first): ``get_stats()`` must issue a bounded number of queries
regardless of project count — counted with a ``before_cursor_execute``
listener (bound 25; the N+1 at N=30 is ≈188).

AC2 (parity pin, green on both sides): the aggregate health_score must
equal the mean of per-project ``get_project_health()`` scores — seeded
with a failed-DoD discriminator (only one project affected: the
portfolio-global approximation used by ``get_projects_health_batch``
would penalise every project and move the average) and an empty project
(score 100 must stay in the denominator).
"""

from __future__ import annotations

from app.delivery.models import Feature, Task
from app.projects.models import Project
from app.quality.models import DoDItem
from app.reporting.attention import AttentionDashboardService
from app.reporting.dashboard import DashboardService
from sqlalchemy import event
from sqlalchemy.orm import Session

_N_PROJECTS = 30
_QUERY_LIMIT = 25


def _seed(db: Session) -> None:
    """N projects with one feature/two tasks each; DoD discriminator on #0; last project empty."""
    for i in range(_N_PROJECTS):
        project = Project(name=f"Perf{i}", slug=f"perf-{i}")
        db.add(project)
        db.flush()
        if i == _N_PROJECTS - 1:
            continue  # empty project — health 100, counted in the mean
        feature = Feature(project_id=project.id, name=f"PF{i}", slug=f"pf-{i}")
        db.add(feature)
        db.flush()
        first = Task(feature_id=feature.id, title="main", status="blocked" if i % 2 else "done")
        db.add(first)
        db.flush()
        db.add(Task(feature_id=feature.id, title="second", status="backlog"))
        if i == 0:
            # per-project penalty only in project #0 — a global-approx
            # implementation would subtract it from EVERY score
            db.add(DoDItem(task_id=first.id, name="evidence", status="failed"))
    db.flush()


def test_get_stats_query_count_bounded_with_exact_parity(db_session: Session) -> None:
    """AC1 query bound (red at N+1) + AC2 parity pin against the per-project loop."""
    _seed(db_session)

    counter = {"n": 0}

    def _count(conn, cursor, statement, parameters, context, executemany):  # noqa: ANN001
        counter["n"] += 1

    import tests.conftest as conftest

    event.listen(conftest._test_engine, "before_cursor_execute", _count)
    try:
        stats = DashboardService(db_session).get_stats()
    finally:
        event.remove(conftest._test_engine, "before_cursor_execute", _count)

    assert counter["n"] <= _QUERY_LIMIT, (
        f"get_stats issued {counter['n']} queries at {_N_PROJECTS} projects "
        "(≤ expected) — aggregate health must be set-based (TASK-0149)"
    )

    # Parity pin: identical arithmetic to the pre-fix loop
    attn = AttentionDashboardService(db_session)
    ref_scores = [
        int(attn.get_project_health(p.id)["score"]) for p in db_session.query(Project).all()
    ]
    expected = round(sum(ref_scores) / len(ref_scores))
    assert stats["health_score"] == expected, (
        f"aggregate health {stats['health_score']} != per-project mean {expected}"
    )
