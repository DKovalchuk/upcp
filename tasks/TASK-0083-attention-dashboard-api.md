# TASK-0083 Attention Dashboard API

Status: DONE (2026-10-31 — gap закрыт: positive-тесты 4 секций (stale_claims/rejected/verdicts_waiting/low_health) + boundary; deviation: recent_activity → LiveActivityFeed (стаб в API); верификация в TASK-0160)
Milestone: M11
Spec: SPEC-0016
Depends: TASK-0082

## Goal

Dashboard attention endpoint returning aggregated action items.

## Acceptance Criteria

- GET /dashboard/attention returns all attention sections.
- Each section has correct query logic.
- Project health score calculation.
- Tests for each section.
