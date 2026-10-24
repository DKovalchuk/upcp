# Authentication and RBAC — UPCP v2

**EN** | [RU](auth-rbac.ru.md)

> Scope: `auth` | Owner: security-team | Version: 3.0.0
> Rewritten 2026-10-24 against the real code (SPEC-0027 §3.4, findings 4-5).
> Every endpoint path below is contract-tested against the OpenAPI schema
> (`backend/tests/test_public_paths.py`).

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

- JWT access tokens + rotating refresh tokens.
- `AuthMiddleware` authenticates every `/api/v1/*` and `/mcp/*` request
  except `PUBLIC_PATHS`; `/auth/*` routes rely on the `get_current_user`
  dependency.
- `PUBLIC_PATHS`: `/health`, `/api/v1/health`, `/auth/setup`,
  `/auth/login`, `/auth/refresh`, `/docs`, `/redoc`, `/openapi.json` —
  every entry is regression-tested to be a registered route
  (the dead `/mcp/health` entry was removed in TASK-0148).
- Authorization: route-level `require_permission(action, resource)` gates
  (see [RBAC](#6-rbac)); ungated reads require any authenticated user.

## 2. Tokens

### 2.1 Access token

- Format: JWT (HS256, symmetric key from `UPCP_SECRET_KEY`).
- TTL: 15 minutes.
- Claims: `sub`, `type`, `iat`, `exp`.
  There is **no `jti` claim and no embedded roles/scopes** — permissions
  are resolved per request from the database (Redis-cached, 60 s).
- Storage: client memory only (not localStorage).

```json
{
  "sub": "9646cb69-24c3-456e-b128-6f7ac2c1140c",
  "type": "access",
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

The denylist is enforced in `AuthMiddleware` (domain routes) and in
`get_current_user` (`/auth/*`): a denylisted access token gets **401**
with `WWW-Authenticate`, the same shape as an invalid token
(`action=auth.token_denied`, metric `upcp_auth_token_denials_total`).

**Redis degradation:** if Redis is unreachable, reads fail **open** —
the request is allowed and a structured warning is logged. Tradeoff:
availability over a revocation window of at most 15 minutes
(SPEC-0027 AC5). Writes degrade the same way; the refresh revocation in
the database is unaffected.

Additionally, after signature verification the middleware checks that
the subject **exists and is active** (`auth:user:{sub}` cache, 60 s) —
an unknown or disabled subject gets 401 even with a valid signature.

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

Gate semantics (fail-closed, in order):

1. `UPCP_DISABLE_AUTH=true` → gates inert (hermetic mode; the middleware
   is not mounted either);
2. no identity → **401**;
3. unknown or inactive subject → **401**;
4. `is_superuser=True` → bypass (covers `/auth/setup` owner and seeder
   admins without data migration);
5. no matching role permission → **403** (structured log +
   `upcp_rbac_denials_total`).

Permission resolution is cached in Redis (`rbac:user_perms:{user_id}`,
TTL 60 s). Phase B (per-CRUD gates on structure/delivery/quality,
org/project-scoped bindings) is backlog — scoped binding columns exist
but are not resolved yet.

## 7. Rate limits and lockout

- `POST /auth/login`: 5 attempts per minute per IP → **429** with
  `retry_after` (see [Rate Limiting](rate-limiting.md)).
- 5 failed attempts → account locked for **30 minutes** → **423**.
- Audit actions recorded in `login_audit`: `login_success`,
  `login_failed`, `account_locked`, `logout`, `password_change`.

## 8. Known limitations

- **Access JWTs survive logout/password change until `exp`** (≤ 15 min)
  for sessions other than the one that made the request — no `jti`
  claim, so a single token cannot be killed early.
- **Refresh reuse detection stops at rejecting the reused token** (401);
  the replacement chain is not family-revoked (no token-family table).
- **Password reset by email does not exist.**
- **Phase B permission gates** (structure/delivery/quality CRUD, scoped
  bindings) are not enforced yet.

## Related documents

- [Rate Limiting](rate-limiting.md)
- [Secrets Handling](secrets-handling.md)
- [Threat Model](threat-model.md)
- [Agent Permissions](agent-permissions.md)
- [Docs index](../INDEX.md)
