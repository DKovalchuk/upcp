# SPEC-0023 — M20: Extended Features

**Milestone:** M20
**Version:** 0.22.0
**Status:** PLANNED
**Created:** 2026-08-12
**Source:** Audit §7 Missing Components

## 1. Problem

Several components are needed for production readiness but were not part of the original M7-M15 design: real-time notifications, file uploads, bulk operations, task comments, and audit export.

## 2. Scope

### S22.1: Real-Time Notifications via SSE (TASK-0115, 8pts)

Replace 30s polling with Server-Sent Events for critical notifications.

- Backend: SSE endpoint `GET /api/v1/notifications/stream`
- Backend: Event emitter on notification creation
- Frontend: `EventSource` connection with fallback to polling
- Toast for critical events (blocking clarification, review submitted)

### S22.2: File Uploads for Evidence (TASK-0116, 8pts)

Evidence currently supports URLs only. Add file attachment support.

- Backend: `POST /api/v1/evidence/upload` with multipart form
- Storage: local filesystem (`data/uploads/`) + S3 adapter for production
- Frontend: drag-and-drop upload zone in EvidenceTab
- Security: file type whitelist, size limit (10MB), virus scan hook

### S22.3: Bulk Task Operations (TASK-0117, 5pts)

Select multiple tasks and perform batch actions.

- Frontend: checkbox column in task table, select all/none
- Actions: bulk status change, bulk assign, bulk priority change
- Backend: `PATCH /api/v1/tasks/bulk` with `{task_ids: [], updates: {}}`
- Confirmation dialog for destructive bulk actions

### S22.4: Task Comments + Audit Export (TASK-0118, 8pts)

**Task Comments:**
- Backend: `Comment` model with task_id, author_id, body, parent_id (threads)
- API: `POST/GET /api/v1/tasks/{id}/comments`
- Frontend: Comments tab in TaskDetailSheet

**Audit Export:**
- Backend: `GET /api/v1/audit/export?format=csv|json&filters=...`
- Frontend: Export button on AuditPage
- Format: CSV with headers, JSON with nested payload

## 3. Exit Criteria

- SSE notifications work (no polling for critical events)
- Evidence supports file attachments
- Multiple tasks can be bulk-updated
- Tasks have threaded comments
- Audit trail exportable as CSV/JSON
- All 800+ backend tests pass
- All 300+ frontend tests pass
