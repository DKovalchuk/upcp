# TASK-0079 Review Service + API

Status: DONE (2026-10-31 — gap закрыт: HTTP-тесты start/findings/verdict (200/201/404/409); deviation: ReviewFindingService сложен в ReviewRoundService; верификация в TASK-0160)
Milestone: M10
Spec: SPEC-0015
Depends: TASK-0077

## Goal

ReviewRound and ReviewFinding services and API endpoints.

## Acceptance Criteria

- ReviewRoundService: create, get, list_by_task, start, add_finding, submit_verdict.
- ReviewFindingService: create, list_by_round.
- State transitions: pending → in_progress → completed/cancelled.
- API: GET /tasks/{id}/review-rounds, POST /tasks/{id}/review-rounds, POST /review-rounds/{id}/start, POST /review-rounds/{id}/findings, POST /review-rounds/{id}/verdict.
- Tests for all endpoints and state transitions.
