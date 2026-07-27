# TASK-0066 Auth Endpoints

Spec: SPEC-0014
Status: done
Priority: 10
Model: routine
Milestone: M7

## Goal

Auth API endpoints: setup, login, logout, refresh, me, password change.

## Security Requirements

- Rate limit: 5 login attempts/min/IP (per security-code-review skill)
- bcrypt password hashing (12 rounds)
- Account lockout after 5 failed attempts (30min)
- Audit all auth events via LoginAudit
- No user enumeration (generic error messages)
- Token rotation on refresh
- Refresh token revocation on logout

## Files likely involved

```text
backend/app/identity/endpoints.py    # new
backend/app/identity/service.py      # new — AuthService
backend/tests/test_auth_endpoints.py # new
```

## Acceptance Criteria

- [ ] POST /auth/setup — first-run only, creates owner + org
- [ ] POST /auth/login — email/password → JWT pair
- [ ] POST /auth/logout — revokes refresh token
- [ ] POST /auth/refresh — rotates refresh token
- [ ] GET /auth/me — current user + org + memberships
- [ ] POST /auth/password/change — validates current, updates hash
- [ ] Rate limiting on login
- [ ] Account lockout after failed attempts
- [ ] Audit logging for all events
- [ ] Generic error messages (no user enumeration)
- [ ] Tests cover all scenarios
- [ ] Commands pass

## DoD

- tests added and passing;
- implementation complete;
- commands pass;
- status updated.
