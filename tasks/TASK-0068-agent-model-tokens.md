# TASK-0068 Agent Model + Tokens

Spec: SPEC-0014
Status: done
Priority: 10
Model: routine
Milestone: M7

## Goal

Agent model with token-based authentication for AI agents.

## Files likely involved

```text
backend/app/identity/agents.py        # new — Agent, AgentToken models
backend/app/identity/agent_auth.py    # new — X-Agent-Token verification
backend/tests/test_agents.py          # new
```

## Acceptance Criteria

- [ ] Agent model (name, description, is_active, created_by).
- [ ] AgentToken model (token_hash, name, scopes, expires_at, revoked_at, last_used_at).
- [ ] POST /agents — create agent (admin only).
- [ ] GET /agents — list agents.
- [ ] GET /agents/{id} — agent detail.
- [ ] POST /agents/{id}/tokens — create token (plaintext shown once).
- [ ] POST /agent-tokens/{id}/revoke — revoke token.
- [ ] Agent token auth via X-Agent-Token header.
- [ ] Tests cover all scenarios.
- [ ] Commands pass.

## DoD

- tests added and passing;
- implementation complete;
- commands pass;
- status updated.
