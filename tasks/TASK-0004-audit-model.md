# TASK-0004 Audit Event Append-Only Model

Spec: SPEC-0004
Status: done
Priority: 10
Model: routine
Milestone: M0

## Goal

Implement the audit context with append-only event model and service.

## Non-goals

- No API endpoints.
- No archive/retention.

## Files likely involved

```text
backend/app/audit/__init__.py
backend/app/audit/models.py
backend/app/audit/service.py
backend/tests/test_audit.py
backend/alembic/versions/0002_audit_event.py
```

## TDD Steps

1. Create failing tests for AuditEvent and AuditService.
2. Run tests, confirm failure.
3. Implement models and service.
4. Generate migration.
5. Run tests, confirm pass.
6. Run lint and typecheck.

## Acceptance Criteria

- `AuditEvent` model with correct columns.
- `AuditService.log_event()` works.
- No update/delete methods.
- Migration generated.
- `make test`, `make lint`, `make typecheck` pass.
- Statuses updated.

## DoD

- tests added;
- implementation added;
- migration generated;
- commands pass;
- statuses updated.
