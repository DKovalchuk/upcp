# Agent Workflow — Specification

> Related: [UPCP v2 PRD](./upcp-v2.md) §3.2 | Milestone: M9
> **Status**: Implemented (backend M9 complete, frontend types exist)
> **Source of truth**: `backend/app/delivery/lifecycle.py` for state machine

## 1. Overview

Agent Workflow defines the task lifecycle from creation to completion, with emphasis on AI agent accountability and human control.

## 2. Task Lifecycle

> **NOTE**: The state machine below matches the actual implementation in `lifecycle.py`.
> This is the authoritative definition. Do not use older diagrams.

```
backlog ──→ ready ──→ claimed ──→ in_progress ──→ done
                │         │            │
                │         │            ├──→ blocked ──→ in_progress
                │         │            │
                │         │            ├──→ needs_clarification ──→ in_progress
                │         │            │
                │         │            └──→ ready_for_review ──→ done
                │         │                         │
                │         │                         └──→ changes_requested ──→ in_progress
                │         │
                │         └──→ backlog (claim released)
                │
                └──→ cancelled
```

### 2.1 Statuses

| Status | Description | Owner |
|--------|-------------|-------|
| `backlog` | Task created, not yet ready for work | — |
| `ready` | Task is ready to be claimed | owner/admin |
| `claimed` | Agent has claimed the task | agent |
| `in_progress` | Agent is actively working | agent |
| `blocked` | Blocked by external dependency | system |
| `needs_clarification` | Agent requested clarification, awaiting answer | agent / human |
| `ready_for_review` | Work complete, awaiting review | reviewer |
| `changes_requested` | Reviewer requested changes | reviewer |
| `done` | Task completed and approved | — |
| `cancelled` | Task cancelled | human (admin/owner) |

### 2.2 Transitions (from `lifecycle.py`)

| From | To | Who | Condition |
|------|----|-----|-----------|
| backlog | ready | owner/admin | Task prepared for work |
| backlog | cancelled | admin | Task cancelled |
| ready | claimed | agent | `POST /tasks/{id}/claim` |
| ready | backlog | owner/admin | Moved back to backlog |
| ready | cancelled | admin | Task cancelled |
| claimed | in_progress | agent | Agent starts working |
| claimed | backlog | system/agent | Claim released or expired |
| in_progress | done | agent | Direct completion (no review required) |
| in_progress | blocked | system | External dependency |
| in_progress | needs_clarification | agent | `POST /tasks/{id}/clarifications` |
| in_progress | ready_for_review | agent | `POST /tasks/{id}/submit-review` |
| blocked | in_progress | system/human | Blocker resolved |
| needs_clarification | in_progress | human | `POST /clarifications/{id}/answer` |
| ready_for_review | done | reviewer | `POST /review-rounds/{id}/verdict` (approve) |
| ready_for_review | changes_requested | reviewer | Verdict: needs_changes |
| changes_requested | in_progress | agent | Agent resumes work |

## 3. Claim

### API
```
POST /api/v1/tasks/{task_id}/claim
Authorization: ApiKey <agent-key>
```

### Rules
- Task must be in `ready` status (see lifecycle in §2)
- Only `agent` role can claim
- One agent — one active claim (configurable via `max_active_claims` in the project)
- Claim is atomic (row-level lock)

### Release
```
POST /api/v1/tasks/{task_id}/release
```
- Agent can release a task voluntarily
- System automatically releases on heartbeat timeout

## 4. Heartbeat

### Mechanism
```
POST /api/v1/tasks/{task_id}/heartbeat
Authorization: ApiKey <agent-key>
Body: { "message": "Running integration tests...", "progress": 60 }
```

### Timeouts

| Parameter | Value | Description |
|-----------|-------|-------------|
| `heartbeat_interval` | 30–60 sec | Recommended interval |
| `heartbeat_stale` | 5 min | Task is considered abandoned |
| `heartbeat_dead` | 15 min | Automatic release + notification |

> **NOTE**: The architecture state-machine doc previously specified 120 seconds.
> The agent-playbook specified 30 minutes. These are both incorrect.
> Values above (5 min stale, 15 min dead) are the canonical defaults.

### Stale behavior
1. **5 min without heartbeat** → task is marked `stale`, notification sent to project owner
2. **15 min without heartbeat** → automatic release, task returns to `ready`
3. Audit event: `task.stale_detected`, `task.auto_released`

## 5. Clarification Flow

When an agent needs additional information:

```
POST /api/v1/tasks/{task_id}/clarification-request
Body: {
  "question": "What response format is expected: JSON or CSV?",
  "context": "Both options are mentioned in the specification"
}
```

### Behavior
- Task transitions to `blocked`
- Clarification is created as a child entity of the task
- Notification sent to the responsible human
- Heartbeat paused (stale timer paused while task is blocked)

### Answer
```
POST /api/v1/tasks/{task_id}/clarifications/{id}/resolve
Body: { "answer": "JSON, with a metadata field for extensions" }
```

## 6. Agent Inbox

Each agent has an inbox for receiving messages:

### Structure
```python
class InboxMessage:
    id: str
    agent_id: str
    task_id: str | None
    from_type: Literal["human", "agent", "system"]
    from_id: str
    subject: str
    body: str
    priority: Literal["low", "normal", "high", "urgent"]
    read: bool
    created_at: datetime
```

### API
```
GET  /api/v1/agents/{agent_id}/inbox?unread=true
POST /api/v1/agents/{agent_id}/inbox/{id}/read
POST /api/v1/agents/{agent_id}/inbox/send
```

### Usage
- System: stale, release, changes_requested notifications
- Human: commands, context, feedback
- Other agents: collaboration requests

## 7. Agent Playbook

Each project can have a playbook — a set of instructions for agents.

### Structure
```yaml
# playbook.yaml
version: "1"
agent_instructions: |
  Use pytest for tests. Run `make test` before submit.
  Minimum coverage: 80%.
quality_gates:
  - name: lint
    command: "make lint"
    required: true
  - name: test
    command: "make test"
    required: true
  - name: typecheck
    command: "make typecheck"
    required: false
evidence_requirements:
  - type: test_result
    description: "Output of pytest with coverage"
  - type: diff
    description: "Git diff of changes"
```

### API
```
GET  /api/v1/projects/{id}/playbook
PUT  /api/v1/projects/{id}/playbook
```

## 8. MCP Interface

Agents interact via MCP (Model Context Protocol):

| MCP Tool | REST Equivalent | Description |
|----------|-----------------|-------------|
| `claim_task` | `POST /tasks/{id}/claim` | Claim a task |
| `heartbeat` | `POST /tasks/{id}/heartbeat` | Send heartbeat |
| `report_progress` | `PATCH /tasks/{id}` | Update progress |
| `report_completion` | `POST /tasks/{id}/submit-review` | Complete work |
| `report_blockage` | `POST /tasks/{id}/clarification-request` | Request clarification |
| `read_playbook` | `GET /projects/{id}/playbook` | Read instructions |
| `get_inbox` | `GET /agents/{id}/inbox` | Check inbox |

## 9. CLI Interface

```bash
upcp task list --project my-project --status open
upcp task claim <task-id>
upcp task heartbeat <task-id> --message "Working on tests"
upcp task submit <task-id> --evidence test_result:pytest.xml
```

## 10. Constraints

- Maximum 10 active claims per agent (configurable at the project level)
- Heartbeat payload no more than 1KB
- Clarification message no more than 4KB
- Inbox retains messages for 30 days, then archives
- Playbook no more than 64KB
