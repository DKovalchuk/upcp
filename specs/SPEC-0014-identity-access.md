# SPEC-0014 Identity & Access Foundation

Status: in-progress
Owner: project-owner
Milestone: M7
Related tasks: TASK-0062, TASK-0063, TASK-0064, TASK-0065, TASK-0066, TASK-0067, TASK-0068, TASK-0069

## Problem

UPCP has no authentication, authorization, or user management. Anyone can access all data and mutate any entity. This is the single most critical gap blocking production use.

## Goal

Provide:

- User model with email/password authentication
- Organization model (multi-org ready, single-org initially)
- Membership model (user ↔ org with role)
- JWT access + rotating refresh tokens
- First-run setup flow (creates owner)
- Auth middleware protecting all endpoints
- RBAC with roles, permissions, and bindings
- Agent model with token-based authentication

## Non-goals

- OIDC / SSO (future)
- Public registration (disabled by default)
- SaaS billing
- Password reset flow (future)
- Email verification (future)

## Architecture

### Domain Model

```
Organization (id, name, slug, is_default)
├── User (id, email, password_hash, display_name, is_active, is_superuser)
│   └── Membership (user_id, org_id, role)
├── Role (id, name, scope: global|org|project)
│   └── Permission (id, action, resource)
│       └── RoleBinding (user_id, role_id, org_id?, project_id?)
├── Agent (id, name, description, is_active, created_by)
│   └── AgentToken (id, agent_id, token_hash, name, scopes, expires_at, revoked_at, last_used_at)
└── Session (id, user_id, refresh_token_hash, expires_at)
```

### State Machines

**User lifecycle**: active ↔ disabled
**AgentToken lifecycle**: active → revoked | expired
**Session lifecycle**: active → expired | revoked

### API Contracts

```yaml
POST /auth/setup          # First-run only. Creates owner + default org.
POST /auth/login          # Email/password → JWT pair
POST /auth/logout         # Invalidate refresh token
POST /auth/refresh        # Rotate refresh token
GET  /auth/me             # Current user + org + memberships
POST /auth/password/change

GET  /agents              # List agents (admin+)
POST /agents              # Create agent (admin+)
GET  /agents/{id}         # Agent detail
POST /agents/{id}/tokens  # Create token (plaintext shown once)
POST /agent-tokens/{id}/revoke

GET  /agent/me            # Agent self-service (X-Agent-Token auth)
```

### Security

- JWT access token: 15min, stateless
- Refresh token: 7d, DB-stored, rotating
- Agent tokens: long-lived, SHA-256 hashed, manual revocation
- Password: bcrypt with configurable rounds
- Rate limiting: 5 login attempts/min/IP
- CORS: explicit origins only

## Requirements

1. User can sign up via first-run setup (creates owner + default org).
2. User can login with email/password, receive JWT pair.
3. All protected endpoints require valid JWT or agent token.
4. RBAC checks permissions before allowing mutations.
5. Agent tokens authenticate via X-Agent-Token header.
6. Refresh tokens rotate on each use.
7. Old refresh tokens are invalidated when new one issued.
8. Passwords are bcrypt-hashed, never stored in plaintext.
9. Audit events track all auth actions.

## Acceptance Criteria

- User model with email (unique), password_hash, display_name, is_active, is_superuser.
- Organization model with name, slug, is_default.
- Membership model linking User ↔ Organization with role field.
- Role model with name, scope (global/org/project).
- Permission model with action, resource.
- RoleBinding model linking User ↔ Role with optional org/project scope.
- Agent model with name, description, is_active, created_by.
- AgentToken model with token_hash (unique), name, scopes, expires_at, revoked_at.
- JWT service: create_access_token, create_refresh_token, verify_token.
- Auth middleware: extracts user/agent from request, adds to state.
- POST /auth/setup: creates User + Organization + Membership (owner role).
- POST /auth/login: validates credentials, returns JWT pair.
- POST /auth/refresh: rotates refresh token.
- GET /auth/me: returns current user + org + memberships.
- POST /auth/password/change: validates current password, updates hash.
- POST /agents: creates agent (admin only).
- POST /agents/{id}/tokens: creates token, returns plaintext once.
- POST /agent-tokens/{id}/revoke: marks token revoked.
- GET /agent/me: agent self-service with X-Agent-Token.
- All existing endpoints protected by auth middleware.
- Default roles seeded: Owner, Admin, Member, Viewer (global scope).
- Default organization created on first setup.
- `make test` passes.
- `make lint` passes.
- `make typecheck` passes.

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Auth breaks existing integrations | High | Feature flag for graceful fallback during migration |
| JWT secret key hardcoded in defaults | Critical | Require UPCP_SECRET_KEY env var in production |
| Password storage vulnerability | High | bcrypt with 12 rounds |
| Token compromise | Medium | Revocation endpoint, audit trail |
| Migration complexity | Medium | Test migrations thoroughly, backup before |

## DoD

- Spec approved.
- All tasks implemented with TDD.
- All tests pass.
- Lint and typecheck pass.
- Auth covers all existing endpoints.
- Default roles and org seeded.
- Statuses updated.
