# Error Codes

Complete catalog of UPCP API and MCP error codes.

---

## Response Format

```json
{
  "error": "error_code",
  "detail": "Human-readable description"
}
```

HTTP MCP:
```json
{
  "jsonrpc": "2.0",
  "error": { "code": -32000, "message": "error_code", "data": { "detail": "..." } },
  "id": 1
}
```

---

## Authentication and Authorization

### UNAUTHENTICATED

**HTTP:** 401
**Description:** Agent token is missing or invalid.
**Causes:** `X-Agent-Token` header not sent, token expired, token not found in DB.
**Resolution:** Check the header. Reissue the token if expired.

### FORBIDDEN

**HTTP:** 403
**Description:** Insufficient permissions to perform the operation.
**Causes:** Token scope does not include the required operation.
**Resolution:** Check scope via `whoami`. Request scope expansion from an administrator.

### AGENT_TOKEN_REVOKED

**HTTP:** 401
**Description:** Token was revoked by an administrator.
**Causes:** Administrator revoked the token via UI or API.
**Resolution:** Reissue the token through Agent Center.

### AGENT_SCOPE_INSUFFICIENT

**HTTP:** 403
**Description:** Agent scope does not cover the requested operation.
**Causes:** Token was issued with a restricted scope.
**Resolution:** Add the required scope in the agent profile.

### SECRET_ACCESS_DENIED

**HTTP:** 403
**Description:** Agent is attempting to access secrets.
**Causes:** Secrets are protected from agent access.
**Resolution:** Secrets are provided through the runtime environment, not via API.

---

## Resources

### NOT_FOUND

**HTTP:** 404
**Description:** The requested resource was not found.
**Causes:** Invalid ID, resource deleted, no access to the project.
**Resolution:** Check the ID. Verify the agent's project assignment.

### VALIDATION_ERROR

**HTTP:** 422
**Description:** Invalid input data.
**Causes:** Required field missing, invalid format, constraint violation.
**Resolution:** Check request fields. See tool documentation.

### CONFLICT

**HTTP:** 409
**Description:** State conflict.
**Causes:** Unique field duplication, concurrent modification.
**Resolution:** Check current resource state. Retry with a new idempotency key.

---

## Tasks

### TASK_NOT_CLAIMABLE

**HTTP:** 422
**Description:** Task cannot be claimed.
**Causes:** Task status is not `ready` and not `backlog`. Task is in `done`, `archived`, or `blocked`.
**Resolution:** Check the task status. Request `task_get` for the current state.

### TASK_ALREADY_CLAIMED

**HTTP:** 409
**Description:** Task is already claimed by another agent.
**Causes:** Another agent has an active claim.
**Resolution:** Wait for the claim to expire (TTL 30 min) or choose a different task.

### TASK_CLAIM_EXPIRED

**HTTP:** 410
**Description:** Claim on the task has expired.
**Causes:** No heartbeat was sent within the TTL.
**Resolution:** Re-claim with `claim_task`. Start sending heartbeats regularly.

### TASK_NOT_READY_FOR_REVIEW

**HTTP:** 422
**Description:** Task is not ready for review submission.
**Causes:** Prerequisites not met (DoD, evidence, clarifications).
**Resolution:** Check `task_get` — which DoD items are not passed, whether blocking clarifications exist.

---

## Evidence and Quality

### EVIDENCE_REQUIRED

**HTTP:** 422
**Description:** Evidence must be attached before proceeding.
**Causes:** Project policy requires evidence for this task type.
**Resolution:** Attach evidence via `attach_evidence`.

### DOD_NOT_SATISFIED

**HTTP:** 422
**Description:** Not all Definition of Done items are completed.
**Causes:** One or more DoD items have status `pending` or `failed`.
**Resolution:** Complete all DoD items. Check status via `task_get`.

---

## Clarification

### CLARIFICATION_BLOCKING

**HTTP:** 422
**Description:** Unresolved blocking clarifications exist.
**Causes:** Agent sent a `blocking: true` clarification and has not received a response.
**Resolution:** Wait for a response via `get_agent_inbox`. Or release the task.

### CLARIFICATION_NOT_FOUND

**HTTP:** 404
**Description:** Clarification request not found.
**Causes:** Invalid ID, clarification already answered or deleted.
**Resolution:** Check the ID via `get_agent_inbox`.

---

## Review

### SELF_REVIEW_FORBIDDEN

**HTTP:** 403
**Description:** Agent cannot review a task they performed themselves.
**Causes:** Attempt to create a finding or verdict for a task the agent claimed/performed.
**Resolution:** Assign a different reviewer agent or human.

### REVIEW_POLICY_VIOLATION

**HTTP:** 422
**Description:** Review policy violated.
**Causes:** Attempt to auto-close without explicit permission. Attempt to approve with unresolved critical findings.
**Resolution:** Check the project's review policy. Resolve critical findings.

### REVIEW_ROUND_NOT_FOUND

**HTTP:** 404
**Description:** Review round not found.
**Resolution:** Check the ID. Request `list_review_rounds` for the task.

---

## Idempotency

### IDEMPOTENCY_CONFLICT

**HTTP:** 409
**Description:** A request with this idempotency_key was already executed with different parameters.
**Causes:** Repeated request with the same key but different arguments.
**Resolution:** Use a new idempotency key for the new request.

---

## Rate Limiting

### RATE_LIMITED

**HTTP:** 429
**Description:** Request limit exceeded.
**Headers:** `Retry-After: <seconds>`
**Resolution:** Use exponential backoff. Start with `Retry-After` seconds.

---

## Git Integration

### GIT_ADAPTER_ERROR

**HTTP:** 502
**Description:** Error communicating with the Git provider.
**Causes:** GitLab/GitHub API unavailable, invalid webhook, provider token expired.
**Resolution:** Check the Git provider status. Update the token.

---

## Internal

### INTERNAL_ERROR

**HTTP:** 500
**Description:** Internal server error.
**Resolution:** Retry after 5 seconds. Maximum 3 attempts. If it persists — contact the administrator.

---

## Retry Matrix

| Code                            | Retry? | Backoff        | Max Attempts |
|---------------------------------|--------|----------------|--------------|
| `401 UNAUTHENTICATED`          | No     | —              | —            |
| `403 FORBIDDEN`                | No     | —              | —            |
| `404 NOT_FOUND`                | No     | —              | —            |
| `409 TASK_ALREADY_CLAIMED`     | No     | —              | —            |
| `409 CONFLICT`                 | No     | —              | —            |
| `409 IDEMPOTENCY_CONFLICT`     | No     | —              | —            |
| `410 TASK_CLAIM_EXPIRED`       | Yes (claim) | 0s        | 1            |
| `422 VALIDATION_ERROR`         | No     | —              | —            |
| `429 RATE_LIMITED`             | Yes    | exponential    | 5            |
| `500 INTERNAL_ERROR`           | Yes    | 5s             | 3            |
| `502 GIT_ADAPTER_ERROR`        | Yes    | 10s            | 3            |
