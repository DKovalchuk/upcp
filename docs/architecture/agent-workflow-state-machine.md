# Agent Workflow State Machines — UPCP v2

## Overview

UPCP uses finite state machines to manage the lifecycle of tasks, claims, clarification requests, and review rounds. All transitions are strictly defined and logged in the audit trail.

---

## 1. Task State Machine

### Diagram

```
                        ┌──────────────┐
                        │   backlog    │
                        └──────┬───────┘
                               │ set_ready
                               ▼
                        ┌──────────────┐
                   ┌───▶│    ready     │◀─────────────────────────┐
                   │    └──────┬───────┘                          │
                   │           │ claim_task                        │
                   │           ▼                                   │
                   │    ┌──────────────┐                          │
                   │    │   claimed    │                          │
                   │    └──────┬───────┘                          │
                   │           │ start_work                        │
                   │           ▼                                   │
                   │    ┌──────────────┐                          │
                   │    │ in_progress  │◀────────────┐            │
                   │    └──┬───┬───┬───┘            │            │
                   │       │   │   │                │            │
       release_task│       │   │   │ request_       │            │
                   │       │   │   │ clarification   │            │
                   │       │   │   ▼                │            │
                   │       │   │ ┌──────────────────┴──┐         │
                   │       │   │ │needs_clarification   │         │
                   │       │   │ └──────────┬───────────┘         │
                   │       │   │            │ clarify_resolved    │
                   │       │   │            └─────────────────────┘
                   │       │   │                                    │
                   │       │   │ block                              │
                   │       │   ▼                                    │
                   │       │ ┌──────────────┐                      │
                   │       │ │   blocked    │──────────────────────┘
                   │       │ └──────┬───────┘      unblock
                   │       │        │ block_resolved
                   │       │        └──▶ in_progress
                   │       │
                   │       │ submit_for_review
                   │       ▼
                   │ ┌───────────────────┐
                   │ │  ready_for_review  │
                   │ └───────┬───────────┘
                   │         │
                   │    ┌────┴────┐
                   │    │         │
                   │    ▼         ▼
                   │ ┌──────┐ ┌──────────────────┐
                   │ │ done │ │changes_requested  │
                   │ └──────┘ └────────┬──────────┘
                   │                   │ rework
                   │                   └──▶ in_progress
                   │
                   │ cancel
                   ▼
              ┌──────────┐
              │ cancelled │
              └──────────┘
```

### States

| State | Description | Allowed Transitions |
|-------|-------------|---------------------|
| `backlog` | Task created, not ready for work | → `ready` |
| `ready` | Ready for agent claim | → `claimed`, → `cancelled` |
| `claimed` | Claimed by agent, not yet started | → `in_progress`, → `ready` (release) |
| `in_progress` | Agent is working | → `blocked`, → `needs_clarification`, → `ready_for_review`, → `ready` (release) |
| `blocked` | Blocked by external factor | → `in_progress` (unblock) |
| `needs_clarification` | Waiting for owner response | → `in_progress` (resolved), → `cancelled` |
| `ready_for_review` | Submitted for review | → `done`, → `changes_requested` |
| `changes_requested` | Review requires rework | → `in_progress` (rework) |
| `done` | Task completed | — (terminal) |
| `cancelled` | Cancelled | — (terminal) |

### Transition Rules

1. **backlog → ready**: Owner or admin only
2. **ready → claimed**: Atomic operation, only via `claim_task`
3. **claimed → in_progress**: Agent calls `start_work` (via first heartbeat)
4. **in_progress → ready**: Agent releases the task
5. **in_progress → blocked**: Agent specifies blocking reason
6. **in_progress → needs_clarification**: Agent sends a clarification request
7. **in_progress → ready_for_review**: Agent confirms completion
8. **ready_for_review → done**: Review approved
9. **ready_for_review → changes_requested**: Review rejected
10. **changes_requested → in_progress**: Agent begins rework
11. **Any → cancelled**: Owner/admin only, except `done`

---

## 2. TaskClaim State Machine

### Diagram

```
          ┌──────────┐
          │  active   │
          └──┬──┬──┬──┘
             │  │  │
    release  │  │  │ task_completed
             │  │  │
             ▼  │  ▼
     ┌────────┐ │ ┌───────────┐
     │released│ │ │ completed  │
     └────────┘ │ └───────────┘
                │
         heartbeat_timeout
                │
                ▼
         ┌──────────┐
         │  expired  │
         └──────────┘
```

### States

| State | Description | Trigger |
|-------|-------------|---------|
| `active` | Claim is active | `claim_task` |
| `released` | Agent voluntarily released | `release_task` |
| `expired` | Heartbeat timeout | Automatic |
| `completed` | Task completed | `submit_for_review` → approved |

### Heartbeat Timeout

- Default: 120 seconds without heartbeat → claim expired
- Configurable per-project (`heartbeat_timeout_sec`)
- Expired claim releases the task → state `ready`
- Audit event: `claim.expired`

---

## 3. ClarificationRequest State Machine

### Diagram

```
          ┌──────────┐
          │   open    │
          └──┬────┬───┘
             │    │
     answer  │    │ cancel
             ▼    ▼
     ┌──────────┐ ┌───────────┐
     │ answered │ │ cancelled  │
     └────┬─────┘ └───────────┘
          │
     resolve
          │
          ▼
     ┌──────────┐
     │ resolved  │
     └──────────┘
```

### States

| State | Description | Trigger |
|-------|-------------|---------|
| `open` | Question asked, awaiting response | `request_clarification` |
| `answered` | Owner responded | `answer_clarification` |
| `resolved` | Agent confirmed receipt of answer | Agent calls `resolve_clarification` |
| `cancelled` | Cancelled (by owner or if task is cancelled) | `cancel_clarification` |

### Rules

1. A clarification request pauses the task (`in_progress` → `needs_clarification`)
2. Owner's answer returns the task to `in_progress` (automatically)
3. If the task is cancelled — all open clarification requests → `cancelled`
4. An agent can cancel its own clarification request

---

## 4. ReviewRound State Machine

### Diagram

```
          ┌───────────┐
          │  pending   │
          └─────┬──────┘
                │ start_review
                ▼
          ┌───────────┐
          │in_progress │
          └──┬─────┬──┘
             │     │
    approve  │     │ reject
             ▼     ▼
     ┌──────────┐ ┌──────────┐
     │ completed │ │ completed │
     │ (approved)│ │ (rejected)│
     └──────────┘ └──────────┘

    (Any non-terminal → cancelled)
```

### States

| State | Description | Trigger |
|-------|-------------|---------|
| `pending` | Review created, awaiting reviewer | `submit_task_for_review` |
| `in_progress` | Reviewer has started | `start_review` |
| `completed` | Review completed with verdict | `submit_review_verdict` |
| `cancelled` | Review cancelled | `cancel_review` |

### Verdicts

| Verdict | Action | Next Task State |
|---------|--------|-----------------|
| `approved` | Task considered done | `done` |
| `rejected` | Task returned for rework | `changes_requested` |

### Rules

1. A review round is created automatically on `submit_task_for_review`
2. The reviewer is determined by the project policy
3. An agent reviewer can review only if the policy = `agent_review_then_human` or `agent_auto_close_if_allowed`
4. With `agent_auto_close_if_allowed`: the agent can approve without human review (if task is low/medium priority)
5. With `agent_review_then_human`: human confirmation is required after agent review
6. A human can override the agent's verdict at any time
7. A new review round is created on rework (changes_requested → in_progress → ready_for_review)

---

## Audit Trail

Each state machine transition writes an audit event:

```json
{
    "action": "task.state_changed",
    "entity_type": "task",
    "entity_id": "01934b35-...",
    "metadata": {
        "from_state": "in_progress",
        "to_state": "ready_for_review",
        "trigger": "submit_for_review",
        "actor_type": "agent",
        "actor_id": "01934b2a-..."
    }
}
```

---

## Timeouts and Auto-Recovery

| Situation | Timeout | Action |
|-----------|---------|--------|
| Heartbeat missing | 120 sec | Claim expired → task goes to `ready` |
| Clarification unanswered | 7 days | Notification → owner |
| Review pending | 3 days | Notification → reviewer |
| Task in progress | 14 days | Notification → owner (configurable) |

---

## Implementation

The state machine is implemented in the `agent_workflow` bounded context:

```
src/upcp/contexts/agent_workflow/
├── state_machine.py          # Transition definitions
├── transitions.py            # Guards and actions
├── services/
│   ├── claim_service.py      # Claim/release/expiry
│   ├── heartbeat_service.py  # Heartbeat recording
│   ├── clarification_service.py
│   └── review_service.py
└── models/
    ├── task_claim.py
    ├── heartbeat.py
    ├── clarification.py
    └── review_round.py
```
