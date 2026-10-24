# TASK-0149 — Dashboard stats: aggregate health N+1 (TASK-0140 perf finding)

**Spec:** SPEC-0024 Phase 2 finding (TASK-0140) — Spec Flow: investigation → task → test → implement
**Milestone:** Этап 1 perf-расследования
**Points:** 3
**Status:** DONE (closed 2026-10-24)

## Investigation findings (2026-10-24)

`GET /dashboard/stats` measured **1.06–1.33s @394 projects** (117/119 load
timeouts, TASK-0140 finding). Root cause — `DashboardService._get_health_score()`
(`backend/app/reporting/dashboard.py`), aggregate branch:

```python
projects = self._session.query(Project).all()
for p in projects:
    svc.get_project_health(p.id)   # ≈6 queries per project → ≈2400 at 394, ≈180 at 30
```

Every other stats field is a single query — the health loop is the dominant cost.

**Why not `get_projects_health_batch()` as a drop-in:** it exists
(`attention.py`) but *approximates* stale/failed_dod/open clarifications/
rejected as **portfolio-global** penalties (documented "approximate
per-project" in `_low_health_projects`), while `get_project_health()` is
strictly per-project. Swapping it in would silently change health_score
numbers. Its only caller is `portfolio.py:63` — that semantics stays
untouched by this task.

Secondary finding: `task_query` in `get_stats()` is dead code (built with a
project filter, never used afterwards).

## Objective

Aggregate health average via one exact set-based batch (per-project
`GROUP BY` counts, arithmetic parity with `get_project_health`); query
count independent of project count; drop the dead `task_query`.

## Acceptance Criteria (verified 2026-10-24)

- [x] **Red first:** `test_dashboard_health_batch_perf.py` — query-bound:
      red **183 queries @30 projects > 25** → green **1 passed** (≤25;
      ≈15 actual: 7 fixed stats + 1 projects + 7 batch)
- [x] Parity pin: aggregate `health_score` == `round(mean(per-project
      get_project_health() scores))` on seeded data including a
      failed-DoD discriminator project (a global-approx shortcut moves
      the average → pin fails) and an empty project (score 100 in the
      denominator) — identical on both sides
- [x] Rounding semantics unchanged (`round()` half-even on int mean);
      project-scoped path (`?project_id=`) untouched (still calls
      `get_project_health`)
- [x] Dead `task_query` block removed
- [x] Full backend suite green (**994 passed**, 3 pre-existing
      `test_redis`); ruff + format + mypy clean (114 files)
- [x] PROJECT_STATUS updated

## Files

| File | Action |
|------|--------|
| `backend/app/reporting/attention.py` | ADD — exact per-project batch scores + average |
| `backend/app/reporting/dashboard.py` | MODIFY — `_get_health_score` uses batch; drop dead block |
| `backend/tests/test_dashboard_health_batch_perf.py` | CREATE (red→green) |
