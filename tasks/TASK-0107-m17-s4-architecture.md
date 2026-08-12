# TASK-0107 — M17 Sprint 4: Architecture Cleanup

**Spec:** SPEC-0020
**Milestone:** M17
**Sprint:** S19.4
**Status:** PENDING
**Size:** M (5 points)

## Objective

Clean up architecture issues: notification error logging, dead code removal, agent inbox stub fix, deprecated startup hook migration, notification target resolution.

## Context

M16 audit found 6 instances of silent exception swallowing in notification triggers, a dead `auth/` module, an agent inbox that always returns empty, a deprecated FastAPI startup hook, and notifications defaulting to "system" user instead of actual users.

---

## Task 1: Add Logging to Notification Trigger Exception Handlers

**Severity:** High
**Files:** 6 files

### Problem

All notification trigger calls use `except Exception: pass` — errors are completely invisible.

### Current Pattern (6 locations)

```python
try:
    from app.reporting.trigger import NotificationTrigger
    NotificationTrigger(self._session).trigger(...)
except Exception:  # noqa: BLE001
    pass
```

### Fix

```python
import logging
logger = logging.getLogger(__name__)

try:
    from app.reporting.trigger import NotificationTrigger
    NotificationTrigger(self._session).trigger(...)
except Exception:  # noqa: BLE001
    logger.warning("Notification trigger failed for %s", event_type, exc_info=True)
```

### Files to Fix

| File | Line | Event |
|------|------|-------|
| `delivery/service.py` | ~120 | task.status_changed |
| `delivery/workflow.py` | ~52 | task.claimed |
| `delivery/workflow.py` | ~187 | clarification.asked |
| `delivery/workflow.py` | ~230 | clarification.answered |
| `quality/service.py` | ~68 | evidence.attached |
| `quality/service.py` | ~226 | review.completed/rejected |
| `delivery/stale_reaper.py` | ~53 | claim.stale |

### Acceptance Criteria

- [ ] All 7 trigger call sites log warnings on failure
- [ ] No bare `except Exception: pass` remains
- [ ] Notification failure still does not block main operation
- [ ] Log includes event type and exception info

### Acceptance Tests

```python
def test_trigger_failure_is_logged(caplog):
    """Notification trigger failure is logged, not swallowed."""
    # Given: NotificationTrigger raises an exception
    # When: TaskService.update() triggers notification
    # Then: warning is logged, task update still succeeds
    with caplog.at_level(logging.WARNING):
        # ... trigger notification that fails
        assert "Notification trigger failed" in caplog.text
```

---

## Task 2: Remove Dead auth/ Module

**Severity:** Medium
**Directory:** `backend/app/auth/`

### Problem

The `auth/` directory contains `models.py` referencing tables `rbac_user`, `rbac_role`, `rbac_permission` — these are from an earlier implementation. The active auth system lives in `identity/`.

### Fix

1. Verify no imports from `app.auth` anywhere in the codebase
2. Delete `backend/app/auth/` directory entirely
3. If any Alembic migration references these tables, add a comment noting they're legacy

### Acceptance Criteria

- [ ] `backend/app/auth/` directory deleted
- [ ] No imports from `app.auth` remain
- [ ] All tests pass

---

## Task 3: Fix Agent Inbox Stub

**Severity:** Medium
**File:** `backend/app/api/v1/agent_self.py:69`

### Problem

```python
def agent_inbox(...) -> ...:
    # MVP: empty inbox -- events will be populated by workflow actions
    return {"events": []}
```

Always returns empty list despite having `AgentInboxEvent` model.

### Fix

Query the `AgentInboxEvent` model:

```python
from app.delivery.models import AgentInboxEvent

def agent_inbox(agent_id: str, session: Session, unread_only: bool = False):
    query = session.query(AgentInboxEvent).filter_by(agent_id=agent_id)
    if unread_only:
        query = query.filter_by(is_read=False)
    events = query.order_by(AgentInboxEvent.created_at.desc()).limit(50).all()
    return {
        "events": [
            {
                "id": e.id,
                "event_type": e.event_type,
                "task_id": e.task_id,
                "message": e.message,
                "is_read": e.is_read,
                "created_at": e.created_at.isoformat(),
            }
            for e in events
        ]
    }
```

### Acceptance Criteria

- [ ] Agent inbox returns real events from `AgentInboxEvent` table
- [ ] Supports `unread_only` filter
- [ ] Returns last 50 events ordered by created_at desc
- [ ] Existing tests pass

### Acceptance Tests

```python
def test_agent_inbox_returns_events():
    """Agent inbox returns real events."""
    # Given: agent has 3 inbox events
    # When: GET /agents/self/inbox
    # Then: response contains 3 events

def test_agent_inbox_unread_only():
    """Agent inbox filters unread."""
    # Given: agent has 3 events, 2 unread
    # When: GET /agents/self/inbox?unread_only=true
    # Then: response contains 2 events
```

---

## Task 4: Migrate Deprecated Startup Hook

**Severity:** Medium
**File:** `backend/app/main.py:108`

### Problem

```python
@app.on_event("startup")
async def _start_reaper() -> None:
```

`@app.on_event("startup")` is deprecated in FastAPI. Use lifespan context manager.

### Fix

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    import asyncio
    from app.delivery.stale_reaper import stale_reaper_loop
    from app.shared.database import SessionLocal
    reaper_task = asyncio.create_task(stale_reaper_loop(SessionLocal))
    yield
    # Shutdown
    reaper_task.cancel()

app = FastAPI(..., lifespan=lifespan)
```

### Acceptance Criteria

- [ ] No `@app.on_event` decorators remain
- [ ] Reaper starts on app startup
- [ ] Reaper stops on app shutdown
- [ ] No deprecation warnings

---

## Task 5: Fix Notification Default Target

**Severity:** Low
**File:** `backend/app/reporting/trigger.py:99`

### Problem

```python
user_id = target_user_id or default_target  # default_target = "system"
```

Notifications for "system" target are invisible — the notifications endpoint filters by user_id (defaulting to "default").

### Fix

When `target_user_id` is not provided, try to resolve from entity context:

```python
def _resolve_target(self, entity_type: str, entity_id: str, actor_id: str) -> str:
    """Resolve notification target from entity context."""
    if entity_type == "task":
        from app.delivery.models import Task
        task = self._session.get(Task, entity_id)
        if task and task.assignee_id:
            return task.assignee_id
    return "system"  # fallback only when no user can be determined

user_id = target_user_id or self._resolve_target(entity_type, entity_id, actor_id)
```

### Acceptance Criteria

- [ ] Task notifications go to task assignee when no target specified
- [ ] Fallback to "system" only when assignee is not set
- [ ] Existing tests pass

---

## Files to Modify

| File | Action | Task |
|------|--------|------|
| `backend/app/delivery/service.py` | MODIFY | #1 |
| `backend/app/delivery/workflow.py` | MODIFY | #1 |
| `backend/app/delivery/stale_reaper.py` | MODIFY | #1 |
| `backend/app/quality/service.py` | MODIFY | #1 |
| `backend/app/auth/` | DELETE | #2 |
| `backend/app/api/v1/agent_self.py` | MODIFY | #3 |
| `backend/app/main.py` | MODIFY | #4 |
| `backend/app/reporting/trigger.py` | MODIFY | #5 |
| `backend/tests/test_notification_trigger.py` | MODIFY | #1, #5 |
| `backend/tests/test_agent_self.py` | MODIFY | #3 |

## Dependencies

- Depends on TASK-0105 (security hardening first)
- Task #2 (delete auth/) should be done after TASK-0105 verifies no auth bypasses

## Definition of Done

- [ ] All 7 trigger sites log warnings on failure
- [ ] Dead `auth/` module deleted
- [ ] Agent inbox returns real events
- [ ] Startup hook migrated to lifespan
- [ ] Notification target resolved from entity context
- [ ] All 705+ existing backend tests pass
- [ ] 5 new tests pass
- [ ] mypy, ruff clean
