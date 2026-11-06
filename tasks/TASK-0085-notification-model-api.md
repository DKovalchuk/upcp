# TASK-0085 Notification Model & API

Status: DONE (2026-10-31 — все AC сверены + закрыт audit-finding T2 (HTTP-тесты 4 эндпоинтов), пути perf-сценария/PRD починены; deviations: envelope без total/offset (follow-up), user_id bucket (TASK-0164); верификация в TASK-0160)
Milestone: M11
Spec: SPEC-0016
Depends: TASK-0082

## Goal

Notification model, migration, and API endpoints.

## Acceptance Criteria

- Notification model with all fields.
- Migration 0016_add_notifications.py.
- API: list, mark read, mark all read.
- Badge count endpoint.
- Notifications created on workflow events (claim, evidence, review).
- Tests.
