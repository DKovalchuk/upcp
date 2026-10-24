# TASK-0100 — M16 Sprint 1: Notification Auto-Generation

**Spec:** SPEC-0019
**Milestone:** M16
**Sprint:** S18.1
**Status:** DONE
**Size:** L

**Audit 2026-10-24 (evidence):** все AC закрыты. `reporting/trigger.py` (8 event
типов, `NotificationTrigger.trigger`), интеграция через event bus
(`shared/event_setup.py` подписывает все 10 событий; legacy-AC «интеграция с
TaskService.update()» выполнен как `event_bus.publish` в
`delivery/service.py:138` — рефакторинг TASK-0114), stale-уведомления в
`stale_reaper.py`, `test_notification_trigger.py` = 10 тестов (8+2 по AC).
Evidence: targeted pytest 130 passed (2026-10-24), CI pipelines 465-469 green
(quality:gate passed).

## Objective

Auto-generate notifications from workflow events so users are alerted without manual intervention.

## Acceptance Criteria

- [ ] NotificationTrigger service created with trigger() method
- [ ] 8 event types supported: task.claimed, clarification.asked/answered, evidence.attached, review.completed/rejected, claim.stale, task.status_changed
- [ ] Each event creates a Notification with correct user_id, type, title, message, entity_type, entity_id
- [ ] Integration with TaskService.update() for status changes
- [ ] Integration with clarification/evidence/review services
- [ ] Background task for stale claim notifications
- [ ] All existing tests pass
- [ ] New tests: 8 trigger tests + 2 integration tests

## Implementation Plan

### Step 1: NotificationTrigger Service
- File: `backend/app/reporting/trigger.py`
- Method: `trigger(session, event_type, *, entity_type, entity_id, actor_id, metadata)`
- Maps event_type to notification title/message templates

### Step 2: Event Hooks
- TaskService.update() → trigger on status change
- ClarificationService.create() → trigger on clarification asked
- ClarificationService.answer() → trigger on clarification answered
- EvidenceService.attach() → trigger on evidence attached
- ReviewRoundService.create() → trigger on review started
- ReviewRoundService.complete() → trigger on review completed/rejected
- StaleReaper.reaper_tick() → trigger on stale claim

### Step 3: Tests
- `backend/tests/test_notification_trigger.py`
- Test each event type creates correct notification
- Test integration with services

## Files to Create/Modify

| File | Action |
|------|--------|
| `backend/app/reporting/trigger.py` | CREATE |
| `backend/app/delivery/service.py` | MODIFY — add trigger calls |
| `backend/app/delivery/workflow.py` | MODIFY — add trigger calls |
| `backend/app/delivery/stale_reaper.py` | MODIFY — add trigger calls |
| `backend/tests/test_notification_trigger.py` | CREATE |
