# Authentication and RBAC — UPCP v2

**EN** | [RU](auth-rbac.ru.md)

> Scope: `auth` | Owner: security-team | Version: 3.2.0
> Rewritten 2026-10-24 against the real code (SPEC-0027 §3.4, findings 4-5);
> auth reworked to dependency-based surface guards 2026-11-04
> (SPEC-0028, TASK-0169/TASK-0170); Phase-B RBAC gate table appended
> 2026-11-04 (TASK-0172).
> Every endpoint path below is contract-tested against the OpenAPI schema
> (`backend/tests/test_auth_docs_contract.py`).

## Table of contents

- [1. Overview](#1-overview)
- [2. Tokens](#2-tokens)
- [3. Endpoints](#3-endpoints)
- [4. Logout denylist](#4-logout-denylist)
- [5. Password change](#5-password-change)
- [6. RBAC](#6-rbac)
- [7. Rate limits and lockout](#7-rate-limits-and-lockout)
- [8. Known limitations](#8-known-limitations)
- [Related documents](#related-documents)

## 1. Overview

- JWT access tokens + rotating refresh tokens for users; static API keys
  for the agent surface (see [Agent API key](#23-agent-api-key-x-agent-token)).
- Authentication is implemented as FastAPI route dependencies, not
  middleware (SPEC-0028 D2). The surface registry
  (`app/api/registry.py`) attaches a default-deny blanket to every
  surface: `web_auth` (Bearer JWT) on all web routes under `/api/v1`
  and `/auth`, `agent_auth` (`X-Agent-Token`) on the agent routes
  (agent self-service, workflow claims/heartbeats, everything under
  `/mcp`). Public routes (`/auth/setup`, `/auth/login`, `/auth/refresh`,
  `/health`, `/api/v1/health`, `/metrics`, docs) are declared public in
  the registry — there is no runtime path dictionary
  (`AuthMiddleware`/`PUBLIC_PATHS` retired in TASK-0170). Coverage:
  `backend/tests/test_api_surface_registry.py` (classification) and
  `backend/tests/test_auth_enumeration.py` (every web/agent route
  answers 401 without credentials).
- Agent routes additionally enforce per-key scopes (AC6 — see
  [Agent API key](#23-agent-api-key-x-agent-token)).
- Authorization: route-level `require_permission(action, resource)` gates
  (see [RBAC](#6-rbac)); ungated reads require any authenticated user.

## 2. Tokens

### 2.1 Access token

- Format: JWT (HS256, symmetric key from `UPCP_SECRET_KEY`).
- TTL: 15 minutes.
- Claims: `sub`, `type`, `jti`, `iat`, `exp`.
  The `jti` claim is a random UUIDv4 minted per token, so two tokens
  issued in the same wall-clock second are never byte-identical
  (regression guard, TASK-0159). There are **no embedded roles/scopes** —
  permissions are resolved per request from the database (Redis-cached, 60 s).
- Storage: client memory only (not localStorage).

```json
{
  "sub": "9646cb69-24c3-456e-b128-6f7ac2c1140c",
  "type": "access",
  "jti": "7f9f6f0a-1c3d-4e2b-9a85-3b6d2f1c4a10",
  "iat": 1761334440,
  "exp": 1761335340
}
```

### 2.2 Refresh token

- Format: opaque random string, stored **hashed** (SHA-256) in the
  database; TTL 7 days.
- Returned **in the JSON response body** (`refresh_token` field) — the
  server does not set an httpOnly cookie.
- Rotation: `POST /auth/refresh` issues a new pair and revokes the used
  refresh token; reuse of a rotated-away token → 401.
- Chain (token-family) revocation on reuse is **not** implemented —
  see [Known limitations](#8-known-limitations).

### 2.3 Agent API key (`X-Agent-Token`)

- Transport: static API key in the `X-Agent-Token` header, valid for the
  whole agent surface (agent self-service, workflow, `/mcp`). Web JWTs
  are rejected there with 401 — `/mcp` is agent-key-only (SPEC-0028 D5,
  caller inventory in TASK-0170).
- Storage: SHA-256 hash at rest; the plaintext is returned exactly once
  by the issuing endpoint.
- Issuance: every newly issued key gets an `expires_at` — default TTL
  **90 days** (`UPCP_AGENT_TOKEN_TTL_DAYS`); an explicit `expires_at`
  must be in the future (422 otherwise). Keys issued before TASK-0170
  may carry `expires_at=NULL` and stay valid until revoked
  (grandfathered).
- Revocation: immediate (`revoked_at`) — an expired or revoked key
  fails the very next request with 401 (`Agent token has expired` /
  `Agent token has been revoked`).
- Scopes (AC6): a per-key `scopes` list gates the surface —
  `agent:self` (agent profile, inbox, playbook), `agent:workflow`
  (claims, heartbeats, progress, clarifications) and `agent:mcp`
  (everything under `/mcp`). A key missing the required scope →
  **403** `{"detail": "Insufficient scope"}` (metric
  `upcp_agent_scope_denials_total`, span attribute
  `upcp.auth.scope_denied`). Legacy keys with `scopes=null` are
  grandfathered and pass every scope gate until reissued; a NEW key
  issued without `scopes` is stored as `[]` (deny-all) and gets no
  access until scopes are granted (fail-closed issuance).
- Hermetic test mode (`UPCP_DISABLE_AUTH=true`, test-only): the surface
  blankets and scope gates short-circuit, mirroring the retired
  middleware's conditional mounting (AC10).
- Issuing endpoint: `POST /api/v1/agents/{agent_id}/tokens`.

## 3. Endpoints

Mounted at prefix `/auth` (not `/api/v1/auth`):

| Endpoint | Purpose | Notes |
|----------|---------|-------|
| `POST /auth/setup` | First-run owner creation | 201; **409** once any user exists |
| `POST /auth/login` | Credentials → token pair | 200 / 401 / 423 (locked) / 429 (rate) |
| `POST /auth/logout` | Revoke refresh + denylist access | Bearer required |
| `POST /auth/refresh` | Rotate the refresh token | 200 / 401 |
| `GET /auth/me` | Current user profile | 401 without a live token |
| `POST /auth/password/change` | Self-service password change | 400 wrong current / 422 weak |

Service endpoints (public): `GET /health`, `GET /api/v1/health`,
`GET /metrics`.

Password reset by email (`/auth/password/reset/*`) is **not implemented**
— the previous document described endpoints that do not exist.

## 4. Logout denylist

`POST /auth/logout` does two things:

1. revokes the presented refresh token;
2. writes `auth:deny:{sha256(access_token)}` to Redis with TTL
   `exp − now` (self-expiring, no cleanup job).

The denylist is enforced in the `web_auth` dependency (web routes) and in
`get_current_user` (`/auth/*`): a denylisted access token gets **401**
with `WWW-Authenticate`, the same shape as an invalid token
(`action=auth.token_denied`, metric `upcp_auth_token_denials_total`).

**Redis degradation:** if Redis is unreachable, reads fail **open** —
the request is allowed and a structured warning is logged. Tradeoff:
availability over a revocation window of at most 15 minutes
(SPEC-0027 AC5). Writes degrade the same way; the refresh revocation in
the database is unaffected.

Additionally, after signature verification the `web_auth` dependency
checks that the subject **exists and is active** (`auth:user:{sub}` cache,
60 s) — an unknown or disabled subject gets 401 even with a valid
signature.

## 5. Password change

`POST /auth/password/change` requires the current password:

- on success **all of the user's refresh tokens are revoked** in the
  same transaction (implemented in TASK-0148 — the docs promised this
  before the code did);
- other sessions' access JWTs remain valid until `exp` (≤ 15 min) —
  see [Known limitations](#8-known-limitations);
- wrong current password → 400; new password shorter than 8 characters
  → 422.

## 6. RBAC

Seeded roles: `Owner`, `Admin`, `Member`, `Viewer`, with a permission
catalog (`Permission` / `RolePermission` / `RoleBinding` tables).

Runtime guard — a FastAPI dependency:

```python
from fastapi import Depends
from app.identity.permissions import require_permission

@router.post(
    "/projects",
    dependencies=[Depends(require_permission("create", "project"))],
)
def create_project(...) -> ...: ...
```

Enforced today (Phase A — admin-dangerous mutations):

- `POST /api/v1/projects` → `create:project`
- `PATCH /api/v1/projects/{project_id}` → `update:project`
- `DELETE /api/v1/projects/{project_id}` → `delete:project`
- agent management mutations (`POST /api/v1/agents`, token issuance and
  revocation under `/api/v1/agents/{agent_id}`) → `manage:agent`

Phase B (TASK-0172) — every dangerous mutation on the web surface
(per-route inventory and no-gate justifications:
`tasks/TASK-0172-rbac-coverage.md`):

| Endpoint | Permission |
|----------|------------|
| `POST /api/v1/projects/{project_id}/components` | `create:component` |
| `PATCH /api/v1/components/{component_id}` | `update:component` |
| `DELETE /api/v1/components/{component_id}` | `delete:component` |
| `POST /api/v1/components/{component_id}/modules` | `create:module` |
| `PATCH /api/v1/modules/{module_id}` | `update:module` |
| `DELETE /api/v1/modules/{module_id}` | `delete:module` |
| `DELETE /api/v1/features/{feature_id}` | `delete:feature` |
| `PATCH /api/v1/tasks/bulk` | `update:task` |
| `DELETE /api/v1/tasks/{task_id}` | `delete:task` |
| `DELETE /api/v1/subtasks/{subtask_id}` | `delete:subtask` |
| `POST /api/v1/tasks/{task_id}/acceptance-criteria` | `create:acceptance_criteria` |
| `PATCH`/`DELETE /api/v1/acceptance-criteria/{ac_id}` | `update`/`delete:acceptance_criteria` |
| `POST /api/v1/tasks/{task_id}/dod-items` | `create:dod_item` |
| `PATCH`/`DELETE /api/v1/dod-items/{item_id}` | `update`/`delete:dod_item` |
| `POST /api/v1/tasks/{task_id}/complete` | `update:task` |
| `POST /api/v1/tasks/{task_id}/submit-review`, `POST /api/v1/tasks/{task_id}/review-rounds` | `create:review_round` |
| `POST /api/v1/review-rounds/{round_id}/start`, `POST /api/v1/review-rounds/{round_id}/verdict` | `update:review_round` |
| `POST /api/v1/review-rounds/{round_id}/findings` | `create:review_finding` |
| `POST /api/v1/tasks/{task_id}/evidence`, `POST /api/v1/tasks/{task_id}/evidence/upload` | `create:evidence` |
| `POST /api/v1/evidence/{evidence_id}/agent-verify`, `/human-accept`, `/reject` | `update:evidence` |
| `POST /api/v1/notification-channels` | `create:notification_channel` |
| `PATCH /api/v1/notification-channels/{channel_id}` | `update:notification_channel` |
| `DELETE /api/v1/notification-channels/{channel_id}` | `delete:notification_channel` |
| `POST /api/v1/notification-channels/{channel_id}/toggle`, `/test` | `update:notification_channel` |
| `POST /api/v1/projects/{project_id}/git-providers` | `create:git_provider` |
| `PATCH`/`DELETE /api/v1/git-providers/{provider_id}` | `update`/`delete:git_provider` |
| `DELETE /api/v1/git-links/{link_id}` | `delete:git_link` |
| `POST /api/v1/internal/reaper/tick` | superuser only — `require_superuser()` → 403 `{"detail": "Superuser required"}` |

Also available: `require_role(role)` → 403 `{"detail": "Insufficient role"}`
(superusers bypass, like the permission gate). No production route is
role-semantic yet — the factory ships for the first one (decision table
in `tasks/TASK-0172-rbac-coverage.md`).

Deliberately ungated (any-authenticated, per SPEC-0027 AC2 baseline):
all reads; routine single-item creates/updates on delivery work items
(feature/task/subtask/comment); notification read-state (`mark-read`);
reporting generation/summarization; `POST /api/v1/git-links`. Agent
workflow mutations (claims/heartbeats/clarifications) live on the agent
surface and are gated by API-key scopes instead (AC6).

Gate semantics (fail-closed, in order):

1. `UPCP_DISABLE_AUTH=true` → gates inert (hermetic mode — the surface
   auth dependencies short-circuit the same way);
2. no identity → **401**;
3. unknown or inactive subject → **401**;
4. `is_superuser=True` → bypass (covers `/auth/setup` owner and seeder
   admins without data migration);
5. no matching role permission → **403** (structured log +
   `upcp_rbac_denials_total`).

`require_role`/`require_superuser` follow the same order; their denials
answer **403** `{"detail": "Insufficient role"}` / `{"detail":
"Superuser required"}` (metric `upcp_rbac_denials_total` with labels
`action=role`/`action=superuser`).

Permission resolution is cached in Redis (`rbac:user_perms:{user_id}`,
TTL 60 s). Per-CRUD gates for dangerous mutations are enforced
(Phase B, TASK-0172 — table above). Still backlog: org/project-scoped
bindings (columns exist but are not resolved) and `require_role`
production usage.

## 7. Rate limits and lockout

- `POST /auth/login`: 5 attempts per minute per IP → **429** with
  `retry_after` (see [Rate Limiting](rate-limiting.md)).
- 5 failed attempts → account locked for **30 minutes** → **423**.
- Audit actions recorded in `login_audit`: `login_success`,
  `login_failed`, `account_locked`, `logout`, `password_change`.

## 8. Known limitations

- **Access JWTs survive logout/password change until `exp`** (≤ 15 min)
  for sessions other than the one that made the request — the token now
  carries a unique `jti` claim, but revocation is keyed by
  `sha256(raw token)` (see [Logout denylist](#4-logout-denylist)), so a
  denylist entry kills only the exact token presented, not every token
  issued to the subject.
- **Refresh reuse detection stops at rejecting the reused token** (401);
  the replacement chain is not family-revoked (no token-family table).
- **Password reset by email does not exist.**
- **Scoped bindings are not resolved yet** (`RoleBinding.org_id`/
  `project_id` columns exist, every binding resolves globally).
  Routine single-item creates/updates on delivery work items, notification
  read-state and reporting mutations stay any-authenticated by decision
  (TASK-0172 inventory).

## Related documents

- [Rate Limiting](rate-limiting.md)
- [Secrets Handling](secrets-handling.md)
- [Threat Model](threat-model.md)
- [Agent Permissions](agent-permissions.md)
- [Docs index](../INDEX.md)
