# MCP Tools Reference

Reference for agent MCP tools. Protocol: JSON-RPC 2.0 over HTTP POST to `/mcp/`.

---

## Read Tools

### whoami

Profile of the current agent, scopes, and assignments.

```json
{ "name": "whoami", "arguments": {} }
// → { "agent_id": "agt_...", "name": "...", "scopes": [...], "assignments": [...] }
```

---

### get_capabilities

List of available tools for the current agent based on scope.

```json
{ "name": "get_capabilities", "arguments": {} }
// → { "tools": ["project_list", "claim_task", ...], "scopes": [...] }
```

---

### project_list

List of projects with pagination.

```json
{ "name": "project_list", "arguments": { "offset": 0, "limit": 20 } }
// → { "items": [{ "id", "name", "slug", "status", ... }], "total", "offset", "limit" }
```

---

### project_get

Project details by ID.

```json
{ "name": "project_get", "arguments": { "project_id": "proj_001" } }
// → { "id", "name", "slug", "description", "status", "created_at", "updated_at" }
```

---

### feature_list / feature_get

```json
{ "name": "feature_list", "arguments": { "project_id": "proj_001", "offset": 0, "limit": 50 } }
{ "name": "feature_get", "arguments": { "feature_id": "feat_001" } }
```

---

### task_list

Project tasks (via features).

```json
{ "name": "task_list", "arguments": { "project_id": "proj_001", "offset": 0, "limit": 50 } }
// → { "items": [{ "id", "feature_id", "title", "status", "priority", "assignee_type", ... }], "total" }
```

---

### task_get

Task with nested `acceptance_criteria[]`, `dod_items[]`, `subtasks[]`.

```json
{ "name": "task_get", "arguments": { "task_id": "task_001" } }
```

---

### get_context_pack

Markdown project context. Tiers: `minimal` | `standard` | `deep` | `debug`. See [context-packs.md](./context-packs.md).

```json
{ "name": "get_context_pack", "arguments": { "project_id": "proj_001", "tier": "standard" } }
```

---

### get_agent_inbox

Incoming clarification requests. Filter: `open` | `answered` | `blocking`.

```json
{ "name": "get_agent_inbox", "arguments": { "status": "open" } }
// → { "items": [{ "id", "task_id", "question", "status", "created_at" }] }
```

---

### list_evidence

Evidence attached to a task.

```json
{ "name": "list_evidence", "arguments": { "task_id": "task_001" } }
// → { "items": [{ "id", "evidence_type", "content", "url", "verified", "created_at" }] }
```

---

### list_review_rounds

Task review rounds.

```json
{ "name": "list_review_rounds", "arguments": { "task_id": "task_001" } }
// → { "items": [{ "id", "round_number", "status", "verdict", "findings_count" }] }
```

---

## Write Tools

### claim_task

Atomic task claim. Requires `idempotency_key` (UUID v4).

```json
{ "name": "claim_task", "arguments": { "task_id": "task_001", "idempotency_key": "<uuid>" } }
// → { "task_id", "claim_id", "agent_id", "claimed_at", "expires_at" }
// Errors: TASK_ALREADY_CLAIMED, TASK_NOT_CLAIMABLE, IDEMPOTENCY_CONFLICT
```

---

### release_task

Releases a task.

```json
{ "name": "release_task", "arguments": { "task_id": "task_001", "reason": "requires clarification" } }
```

---

### heartbeat_task

Liveness signal. Refreshes the claim TTL. Send every 30–60 seconds. Without heartbeat — claim expires after 30 min.

```json
{ "name": "heartbeat_task", "arguments": { "task_id": "task_001", "message": "analyzing codebase" } }
```

---

### report_progress

Record progress.

```json
{ "name": "report_progress", "arguments": { "task_id": "task_001", "summary": "tests written", "progress_percent": 40 } }
```

---

### attach_evidence

Attach evidence. Types: `test_output`, `screenshot`, `log`, `url`, `file`.

```json
{ "name": "attach_evidence", "arguments": {
  "task_id": "task_001", "evidence_type": "test_output",
  "content": "pytest: 47 passed in 3.2s"
} }
```

---

### request_clarification

Request clarification. `blocking: true` — task goes to `blocked`. `false` — continues.

```json
{ "name": "request_clarification", "arguments": {
  "task_id": "task_001",
  "question": "Should due_date use ISO 8601 or Unix timestamp?",
  "blocking": true
} }
```

---

### reply_clarification

Reply to a clarification request.

```json
{ "name": "reply_clarification", "arguments": {
  "clarification_id": "clr_001", "answer": "Use ISO 8601 format"
} }
```

---

### submit_task_for_review

Submit for review. Requirements: all DoD `passed`, no blocking clarifications, at least one evidence.

```json
{ "name": "submit_task_for_review", "arguments": {
  "task_id": "task_001", "summary": "CRUD implemented, all tests green."
} }
// Errors: DOD_NOT_SATISFIED, EVIDENCE_REQUIRED, CLARIFICATION_BLOCKING
```

---

### create_review_finding

Finding in a review round (for reviewer agents). Severity: `info|low|medium|high|critical`. Category: `code_quality|security|performance|correctness`.

```json
{ "name": "create_review_finding", "arguments": {
  "review_round_id": "rr_001", "severity": "medium",
  "category": "code_quality",
  "description": "Missing error handling in create()",
  "file_path": "backend/app/users/service.py", "line_range": "42-58"
} }
```

### submit_review_verdict

Final verdict. Verdict: `approve` | `reject` | `needs_changes`.

```json
{ "name": "submit_review_verdict", "arguments": {
  "review_round_id": "rr_001", "verdict": "needs_changes",
  "summary": "Add error handling and edge case tests."
} }
```

## Idempotency

Write tools accept `idempotency_key` (UUID v4). A repeated request with the same key returns the previous result. Keys are stored for 24 hours.

## Pagination

List tools: `offset` (default: 0), `limit` (default: 20, max: 100).
