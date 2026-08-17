# TASK-0118 — M20 S22.4: Task Comments + Audit Export

**Milestone:** M20
**Sprint:** S22.4
**Points:** 8
**Spec:** SPEC-0023 §S22.4
**Status:** DONE

## Objective

Add threaded task comments and audit trail export (CSV/JSON).

## Acceptance Criteria

- [ ] `Comment` model: task_id, author_type, author_id, body, parent_id (nullable for threads)
- [ ] `POST /api/v1/tasks/{id}/comments` — create comment
- [ ] `GET /api/v1/tasks/{id}/comments` — list comments (threaded)
- [ ] `GET /api/v1/audit/export?format=csv|json&project_id=...` — export audit events
- [ ] Frontend: Comments tab in TaskDetailSheet
- [ ] Frontend: Export button on AuditPage
- [ ] Migration 0022_add_task_comments
- [ ] All existing tests still pass
- [ ] New tests: create comment, list threaded, audit export CSV, audit export JSON

## Technical Design

### Backend — Comments

**New model:** `Comment` in `app/delivery/models.py`
- id, task_id (FK), author_type, author_id, body (Text), parent_id (self-FK, nullable)
- created_at, updated_at

**Service:** `CommentService` in `app/delivery/service.py`
- create(task_id, author_type, author_id, body, parent_id?) → Comment
- list_by_task(task_id) → list[Comment]

**API:** `app/api/v1/delivery.py`
- POST /tasks/{task_id}/comments
- GET /tasks/{task_id}/comments

### Backend — Audit Export

**Endpoint:** `GET /api/v1/audit/export`
- Query params: format (csv|json), project_id, optional filters
- Returns CSV with headers or JSON array

### Frontend

- Comments tab in TaskDetailSheet with comment list + reply form
- Export button on AuditPage triggering download
