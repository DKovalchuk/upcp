# TASK-0087 Project Health & Portfolio API

Status: DONE (2026-10-31 — gap закрыт: route-тесты GET /projects/{id}/health + фикс документированного 404 для неизвестного проекта (red→green); формула/weights сверены со SPEC-0016; верификация в TASK-0160)
Milestone: M11
Spec: SPEC-0016
Depends: TASK-0083

## Goal

Project health score and portfolio overview endpoints.

## Acceptance Criteria

- GET /projects/{id}/health — health score with breakdown.
- GET /portfolio/overview — aggregate stats.
- Health score formula per SPEC-0016.
- Tests.
