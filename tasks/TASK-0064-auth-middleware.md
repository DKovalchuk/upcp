# TASK-0064 Auth Middleware

Spec: SPEC-0014
Status: done
Priority: 10
Model: routine
Milestone: M7

## Goal

FastAPI dependency for JWT + agent token authentication. Protects all endpoints.

## Non-goals

- No RBAC permission checks yet (TASK-0066).
- No login endpoints yet (TASK-0067).
- No agent token creation yet (TASK-0068).

## Files likely involved

```text
backend/app/identity/auth.py          # new — get_current_user, get_current_agent
backend/app/identity/dependencies.py  # new — CurrentUser, CurrentAgent dataclasses
backend/tests/test_auth_middleware.py  # new
```

## TDD Steps

1. Create failing tests.
2. Implement dependencies.
3. Verify.

## Acceptance Criteria

- [ ] get_current_user extracts JWT from Authorization header.
- [ ] get_current_user returns User object for valid token.
- [ ] get_current_user raises 401 for missing/invalid/expired token.
- [ ] get_current_agent extracts token from X-Agent-Token header.
- [ ] get_current_agent returns Agent object for valid token.
- [ ] get_current_agent raises 401 for missing/invalid token.
- [ ] require_user dependency wraps get_current_user.
- [ ] require_agent dependency wraps get_current_agent.
- [ ] Tests cover all scenarios.
- [ ] make test, make lint, make typecheck pass.
- [ ] Status updated.

## DoD

- tests added and passing;
- implementation complete;
- commands pass;
- status updated.
