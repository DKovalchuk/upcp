# SPEC-0022 — M19: Test Quality & Architecture

**Milestone:** M19
**Version:** 0.21.0
**Status:** PLANNED
**Created:** 2026-08-12
**Source:** M16 Audit findings T1-T11, A1-A2

## 1. Problem

Test infrastructure has duplication (8+ files with own engine setup), service-layer business logic is tested only via HTTP endpoints (not in isolation), and cross-context communication uses ad-hoc direct calls.

## 2. Scope

### S21.1: Test Infrastructure (TASK-0112, 5pts)

| Finding | Fix |
|---------|-----|
| Engine duplication in 8+ test files | Centralize in conftest.py with all model imports |
| conftest.py incomplete model registration | Import all models in conftest for create_all() |
| No pytest markers | Add `@pytest.mark.slow`, `@pytest.mark.integration` |
| No frontend coverage | Add `@vitest/coverage-v8` to frontend |

### S21.2: Service-Layer Tests (TASK-0113, 8pts)

| Missing Test | Priority |
|-------------|----------|
| `delivery/service.py` unit tests | High |
| `quality/service.py` unit tests | High |
| `reporting/service.py` unit tests | Medium |
| `/api/v1/notifications` endpoint tests | High |
| `/api/v1/reaper` endpoint tests | Medium |
| Full lifecycle integration test | High |

### S21.3: Event Bus (TASK-0114, 8pts)

Replace direct `NotificationTrigger` calls with in-process event bus:

```python
# shared/events.py
class EventBus:
    _handlers: dict[str, list[Callable]] = {}

    def subscribe(self, event_type: str, handler: Callable): ...
    def publish(self, event_type: str, **data): ...

# Services emit events
event_bus.publish("task.status_changed", task_id=..., old_status=..., new_status=...)

# Trigger subscribes
event_bus.subscribe("task.status_changed", notification_trigger.handle)
```

## 3. Exit Criteria

- All test files use shared conftest fixtures
- Service-layer unit tests for 3 core services
- Full lifecycle integration test passes
- Event bus replaces all direct trigger calls
- Frontend coverage reporting enabled
- `as any` reduced by 50% in test files
- All existing tests pass + 30 new tests
