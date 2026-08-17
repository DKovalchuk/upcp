# Agent Playbook

> **Status**: Partially implemented. Agent API endpoints exist. Per-project playbook storage not yet implemented.
> **Source of truth**: `backend/app/delivery/workflow.py` for actual API behavior

Complete guide for AI agents working with UPCP.

## 1. Authentication

All requests require the `X-Agent-Token` header:

```
X-Agent-Token: upcp_agt_<token>
```

The token is issued when the agent is registered and is bound to a scope. The token cannot be recovered — only reissued.

### Connection Verification

```json
// MCP: whoami
{}
```

Expected response: object with `agent_id`, `name`, `scopes[]`, `assignments[]`.

---

## 2. Getting Context

### 2.1 Context Pack

Request a context pack before working on a task:

```json
// MCP: get_context_pack
{ "project_id": "...", "tier": "standard" }
```

Tiers: `minimal` | `standard` | `deep` | `debug`. See [context-packs.md](./context-packs.md).

### 2.2 Agent Inbox

Check for incoming clarification requests:

```json
// MCP: get_agent_inbox
{ "status": "open" }
```

### 2.3 Capabilities

Discover available operations:

```json
// MCP: get_capabilities
{}
```

---

## 3. Task Lifecycle

```
backlog → ready → claimed → in_progress → in_review → done
                                    ↘ blocked
                                    ↘ failed
```

### 3.1 Claim

```json
// MCP: claim_task
{ "task_id": "...", "idempotency_key": "<uuid-v4>" }
```

**Rules:**
- The task must be in `ready` or `backlog` status.
- One agent — one active claim.
- The claim expires after 5 min without heartbeat (stale notification), auto-released at 15 min.
- Re-claiming by the same agent is an idempotent operation.

### 3.2 Heartbeat

Send heartbeat every 30–60 seconds:

```json
// MCP: heartbeat_task
{ "task_id": "...", "message": "analyzing codebase" }
```

Without heartbeat the claim expires. The task returns to the pool.

### 3.3 Progress

Record progress:

```json
// MCP: report_progress
{ "task_id": "...", "summary": "unit tests written", "progress_percent": 40 }
```

### 3.4 Release

If the task cannot be completed:

```json
// MCP: release_task
{ "task_id": "...", "reason": "API contract clarification required" }
```

---

## 4. Clarification

When information is insufficient:

```json
// MCP: request_clarification
{
  "task_id": "...",
  "question": "What format is expected for due_date — ISO 8601 or Unix timestamp?",
  "blocking": true
}
```

- `blocking: true` — task goes to `blocked`, agent waits for a response.
- `blocking: false` — task continues, response is asynchronous.

Check answers: `get_agent_inbox { "status": "answered" }`.

---

## 5. Evidence

### Attaching Evidence

```json
// MCP: attach_evidence
{
  "task_id": "...",
  "evidence_type": "test_output",
  "content": "pytest: 47 passed in 3.2s"
}
```

### Evidence Types

| Type          | Description         | Example                     |
|---------------|---------------------|-----------------------------|
| `test_output` | Test output         | `pytest: 47 passed`         |
| `screenshot`  | UI screenshot       | URL or base64               |
| `log`         | Log file            | Log fragment                |
| `url`         | Resource link       | PR URL, deploy URL          |
| `file`        | File artifact       | Path to file                |

---

## 6. Submit for Review

After completing all AC and DoD:

```json
// MCP: submit_task_for_review
{ "task_id": "...", "summary": "CRUD implemented, all tests green." }
```

**Requirements:** All DoD `passed`, no blocking clarifications, at least one evidence.

---

## 7. Review Flow

Reviewer agent creates findings:

```json
// MCP: create_review_finding
{
  "review_round_id": "...",
  "severity": "medium",
  "category": "code_quality",
  "description": "Missing error handling in create()",
  "file_path": "backend/app/users/service.py",
  "line_range": "42-58"
}
```

Verdict:

```json
// MCP: submit_review_verdict
{ "review_round_id": "...", "verdict": "needs_changes", "summary": "..." }
```

By default, the agent's verdict is a recommendation. Final decision rests with the human.

---

## 8. Error Handling

| Code                      | HTTP | Action                            |
|---------------------------|------|-----------------------------------|
| `UNAUTHENTICATED`         | 401  | Check your token                  |
| `FORBIDDEN`               | 403  | Check your scope                  |
| `TASK_ALREADY_CLAIMED`    | 409  | Choose a different task           |
| `TASK_CLAIM_EXPIRED`      | 410  | Re-claim the task                 |
| `TASK_NOT_CLAIMABLE`      | 422  | Check the task status             |
| `EVIDENCE_REQUIRED`       | 422  | Attach evidence                   |
| `DOD_NOT_SATISFIED`       | 422  | Complete DoD items                |
| `CLARIFICATION_BLOCKING`  | 422  | Wait for the response             |
| `RATE_LIMITED`            | 429  | Exponential backoff               |

---

## 9. Working with Secrets

**Forbidden:** requesting secrets, including keys/passwords in evidence, logging secrets.

**Allowed:** using env vars from the runtime, referencing the secret provider.

Secrets are automatically redacted by the LLM gateway.

---

## 10. What You Must NOT Do

1. Claim a task without reading the context pack.
2. Ignore heartbeats.
3. Mark tasks done without evidence.
4. Make cross-context SQL queries.
5. Create multiple claims on one task.
6. Review your own tasks (self-review is forbidden).
7. Store secrets in evidence/heartbeat/clarification.
8. Retry without backoff.

## 11. Recovery After Failure

1. `whoami` — is the token active?
2. `get_agent_inbox` — any unfinished tasks?
3. `task_get` for the last task — what's the status?
4. If the claim expired — re-claim with `claim_task`.
5. If `blocked` — check clarification answers.
6. Send a `heartbeat` to confirm.

## 12. Best Practices

- Context pack **before** starting work.
- Heartbeat every 30–60 seconds.
- Progress at each milestone.
- Evidence as it becomes ready.
- `blocking: true` for critical clarifications.
- Check inbox on every startup.
