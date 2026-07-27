# SPEC-0004 Audit Event Append-Only Model

Status: approved
Owner: project-owner
Milestone: M0
Related tasks: TASK-0004

## Problem

No audit trail exists. Every future module needs a way to record who did what and when.

## Goal

Provide an append-only `audit_event` table and a service to log events.

## Non-goals

- No archive/retention policy (M6).
- No API for querying audit events (M1).
- No integration with other modules yet.

## Requirements

1. `AuditEvent` model with: id, timestamp, event_type, entity_type, entity_id, actor_type, actor_id, payload (JSON).
2. Table is append-only: no update, no delete service.
3. `AuditService` provides `log_event(...)`.
4. Migration generated for `audit_event` table.
5. Unit tests don't require running DB.

## Acceptance Criteria

- `AuditEvent` model exists in `app/audit/models.py`.
- `AuditService` exists in `app/audit/service.py`.
- `log_event()` inserts a row.
- No update/delete methods on the service.
- Migration generated.
- `make test`, `make lint`, `make typecheck` pass.
- Statuses updated.

## Risks

- Minimal: this is a standalone append-only module.

## DoD

- Spec approved.
- Task implemented with TDD.
- All commands pass.
- Statuses updated.
