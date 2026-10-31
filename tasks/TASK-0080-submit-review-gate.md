# TASK-0080 Submit-for-Review Gate

Status: DONE (2026-10-31 — все AC сверены (9 тестов gate + submit-review transition red→green в TASK-0160); deviations: error-code в detail-строке (не envelope), TaskWorkflowService → WorkflowService (не существовал), gate принимает также ready_for_review)
Milestone: M10
Spec: SPEC-0015
Depends: TASK-0078, TASK-0079

## Goal

Quality gate that blocks task review submission when criteria not met.

## Acceptance Criteria

- POST /tasks/{id}/submit-review checks:
  - All DoDItems passed or no DoDItems exist.
  - Required evidence types satisfied.
  - No blocking clarifications open.
  - Task in valid state (claimed/in_progress).
- Returns ReviewRound on success.
- Returns structured error on failure.
- Integration with existing TaskWorkflowService.
- Tests for all gate conditions.
