# TASK-0039: Audit List API Endpoint

Spec: SPEC-0012 (C1)
Status: done
Priority: 1
Model: routine
Milestone: M5

## Goal

Add `GET /api/v1/projects/{project_id}/audit-events` endpoint with filtering and pagination. Currently `AuditService` only has `log_event()` — no query method exists.

## Non-goals

- No audit UI (TASK-0032).
- No real-time event streaming.
- No export functionality.

## Backend context

- `backend/app/audit/service.py` — only `log_event()`
- `backend/app/audit/models.py` — AuditEvent model exists
- No audit API route in `backend/app/api/v1/`

## API contract

```text
GET /api/v1/projects/{project_id}/audit-events

Query params:
  event_type: optional string filter
  entity_type: optional string filter
  date_from: optional ISO datetime
  date_to: optional ISO datetime
  offset: int (default 0)
  limit: int (default 20, max 100)

Response 200:
{
  "items": [AuditEvent],
  "total": int,
  "offset": int,
  "limit": int
}

AuditEvent:
{
  "id": string (UUID),
  "timestamp": ISO datetime,
  "event_type": string,
  "entity_type": string,
  "entity_id": string (UUID),
  "actor_type": string,
  "actor_id": string (UUID),
  "payload": object,
  "note": string | null
}
```

## TDD Steps

1. Add `list_events()` to `AuditService` with filters + pagination.
2. Create API route `GET /projects/{project_id}/audit-events`.
3. Add Pydantic response schema `AuditEventResponse`.
4. Write tests for: empty results, filtered results, pagination.
5. Verify `make test` passes.

## Acceptance Criteria

- `AuditService.list_events()` supports: event_type, entity_type, date_from, date_to filters.
- `AuditService.list_events()` supports offset/limit pagination.
- API route returns `PaginatedResponse<AuditEventResponse>`.
- Tests cover: empty database, filtered queries, pagination boundaries.
- `make test` passes.

## DoD

- endpoint implemented;
- service method added;
- tests pass;
- task file updated.
