# TASK-0101 — M16 Sprint 2: Notification Channels (Email + Webhook)

**Spec:** SPEC-0019
**Milestone:** M16
**Sprint:** S18.2
**Status:** PENDING
**Size:** L

## Objective

Implement email and webhook notification channels with CRUD API.

## Acceptance Criteria

- [ ] NotificationChannel model with channel_type, name, config, is_active
- [ ] NotificationDelivery model for delivery logging
- [ ] Migration 0019 created
- [ ] EmailChannel class: SMTP send, config validation, error handling
- [ ] WebhookChannel class: HTTP send, HMAC signature, retry
- [ ] Channel CRUD API: create, list, delete, test
- [ ] Notification delivery logged on each send
- [ ] All existing tests pass
- [ ] New tests: 6 channel tests + 3 API tests

## Implementation Plan

### Step 1: Models + Migration
- `backend/app/reporting/models.py` — add NotificationChannel, NotificationDelivery
- `backend/alembic/versions/0019_add_notification_channels.py`

### Step 2: Channel Interface + Implementations
- `backend/app/reporting/channels/base.py` — abstract base
- `backend/app/reporting/channels/email.py` — SMTP implementation
- `backend/app/reporting/channels/webhook.py` — HTTP implementation

### Step 3: Channel Service + API
- `backend/app/reporting/channel_service.py` — CRUD + dispatch
- `backend/app/api/v1/notification_channels.py` — REST endpoints

### Step 4: Tests
- `backend/tests/test_notification_channels.py`

## Files to Create/Modify

| File | Action |
|------|--------|
| `backend/app/reporting/models.py` | MODIFY — add 2 models |
| `backend/alembic/versions/0019_*.py` | CREATE |
| `backend/app/reporting/channels/base.py` | CREATE |
| `backend/app/reporting/channels/email.py` | CREATE |
| `backend/app/reporting/channels/webhook.py` | CREATE |
| `backend/app/reporting/channel_service.py` | CREATE |
| `backend/app/api/v1/notification_channels.py` | CREATE |
| `backend/app/main.py` | MODIFY — register router |
| `backend/tests/test_notification_channels.py` | CREATE |
