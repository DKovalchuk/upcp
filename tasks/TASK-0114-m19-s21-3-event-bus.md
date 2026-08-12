# TASK-0114 — M19 S21.3: Event Bus

**Milestone:** M19
**Sprint:** S21.3
**Status:** IN PROGRESS
**Spec:** SPEC-0022
**Estimate:** 8pts

## Objective

Replace direct `NotificationTrigger` calls with an in-process event bus for decoupled cross-context communication.

## Acceptance Criteria

- [ ] `shared/events.py` — EventBus class with subscribe/publish
- [ ] Services emit events via EventBus instead of direct trigger calls
- [ ] NotificationTrigger subscribes to events
- [ ] All existing tests pass
- [ ] Event bus tests added

## Direct trigger calls to replace (7 locations)

1. `delivery/workflow.py:55` — task claimed
2. `delivery/workflow.py:190` — task completed
3. `delivery/workflow.py:233` — clarification requested
4. `delivery/service.py:124` — task status changed
5. `delivery/stale_reaper.py:53` — claim expired
6. `quality/service.py:71` — evidence submitted
7. `quality/service.py:229` — review round created
