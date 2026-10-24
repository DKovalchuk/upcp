# TASK-0110 — M18 S20.3: Notification UX

**Milestone:** M18
**Sprint:** S20.3
**Points:** 5
**Status:** DONE
**Spec:** SPEC-0021, §S20.3

**Audit 2026-10-24 (evidence):** все AC закрыты: route `/notifications`
(`router.tsx:271-273`), фильтры type + read/unread
(`NotificationsPage.tsx:114-115`), mark individual ✅, Mark all read ✅
(`:137-196`), EmptyState «No notifications» ✅ (`:237-240`), Bell
click-to-navigate ✅ (`NotificationBell.tsx:98-103`), error-handling toast ✅
(`:43`), 8 тестов NotificationsPage (AC: 8) ✅, TS clean ✅.
Evidence: targeted vitest 29 passed (2026-10-24), CI 465-469 green.

## Objective

Improve notification UX: full notifications page with filters, click-to-navigate, error handling on mark-read, type filtering.

## Acceptance Criteria

1. `/notifications` page exists with:
   - List of all notifications (paginated)
   - Filter by type (dropdown)
   - Filter by read/unread
   - Mark individual as read
   - Mark all as read button
   - Empty state when no notifications
2. NotificationBell click on individual notification navigates to entity (if entity_type/entity_id present)
3. Mark-read operations have error handling with toast on failure
4. Type filter dropdown on notifications page
5. All existing tests pass + 8 new notification tests
6. TypeScript clean, pre-commit hooks pass

## Design Decisions

- Notifications page uses same layout pattern as other pages (heading + filters + content)
- Type filter uses a Select dropdown with "All types" as default
- Entity navigation: `/projects/{project_id}/{entity_type}/{entity_id}` — but since notifications don't store project_id, we'll navigate to the entity directly or skip navigation if project context is unknown
- Mark-read error handling: `.catch(() => showToast.mutationError('update', 'notification'))`

## Files to Create/Modify

### Frontend
- `frontend/src/components/notifications/NotificationsPage.tsx` — new full page
- `frontend/src/components/notifications/NotificationBell.tsx` — add click-to-navigate, error handling
- `frontend/src/router.tsx` — add /notifications route
- `frontend/src/components/notifications/__tests__/NotificationsPage.test.tsx` — new tests
