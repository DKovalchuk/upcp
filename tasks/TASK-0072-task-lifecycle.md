# TASK-0072 Task Lifecycle State Machine

Spec: SPEC-0014
Status: done
Priority: 10
Model: routine
Milestone: M9

## Goal

Enforce valid task status transitions per the state machine.

## State Machine

```text
backlog → ready → claimed → in_progress → done
              │       │           │
              │       │           ├──→ blocked → in_progress
              │       │           ├──→ needs_clarification → in_progress
              │       │           └──→ ready_for_review → done
              │       │                        │
              │       │                        └──→ changes_requested → in_progress
              │       └──→ backlog (claim released/expired)
              └──→ cancelled
```

## Files likely involved

```text
backend/app/delivery/lifecycle.py       # new — transition validation
backend/app/delivery/service.py         # update TaskService to use lifecycle
backend/tests/test_lifecycle.py         # new
```

## Acceptance Criteria

- [ ] VALID_TRANSITIONS dict maps every status to its allowed next statuses.
- [ ] validate_transition(old, new) raises on illegal transition.
- [ ] TaskService.update_status() uses validate_transition.
- [ ] States: backlog, ready, claimed, in_progress, done, blocked, needs_clarification, ready_for_review, changes_requested, cancelled.
- [ ] Tests cover all valid and invalid transitions.

## DoD

- tests added and passing;
- implementation complete;
- commands pass;
- status updated.
