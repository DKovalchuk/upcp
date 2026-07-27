# Authentication and RBAC — UPCP v2

> Scope: `auth` | Owner: security-team | Version: 2.0.0

## 1. Overview

UPCP uses JWT access tokens + rotating refresh tokens for authentication.
RBAC is implemented at three levels: global, organization, project.

## 2. Tokens

### 2.1 Access Token

- Format: JWT (RS256)
- TTL: 15 minutes
- Claims: `sub`, `roles`, `scopes`, `iat`, `exp`, `jti`
- Storage: client memory only (not localStorage)

```json
{
  "sub": "usr_a1b2c3",
  "roles": ["org:admin", "proj:member"],
  "scopes": ["projects:read", "tasks:write"],
  "iat": 1721980800,
  "exp": 1721981700,
  "jti": "tok_x1y2z3"
}
```

### 2.2 Refresh Token

- Format: opaque rotating token
- TTL: 7 days
- Rotation: each refresh invalidates the previous token and issues a new pair
- Storage: httpOnly, Secure, SameSite=Strict cookie
- Reuse detection: if an already-invalidated refresh token is used, the entire chain is revoked

### 2.3 Token Lifecycle

```
Login → (access + refresh)
  ↓ (15 min)
Refresh → (new access + new refresh, old refresh invalidated)
  ↓ (7 days max)
Re-login required
```

## 3. Authentication

### 3.1 First-Run Setup

```
POST /api/v1/auth/setup
```

- Called only when no users exist in the system
- Creates the first global-level Owner
- Requires: `email`, `password`, `display_name`
- After the first user is created, the endpoint returns `410 Gone`

### 3.2 Login

```
POST /api/v1/auth/login
Body: { "email": "...", "password": "..." }
Response: { "access_token": "...", "refresh_token": "...", "expires_in": 900 }
```

- Rate limit: 5 attempts/min/IP, lockout for 15 min after 5 failures
- Logs: `auth.login.success` / `auth.login.failed`
- Disabled for deactivated accounts

### 3.3 Logout

```
POST /api/v1/auth/logout
Authorization: Bearer <access_token>
```

- Invalidates the current refresh token
- Logs: `auth.logout`

### 3.4 Password Change

```
POST /api/v1/auth/password/change
Body: { "current_password": "...", "new_password": "..." }
```

- Requires the current password
- Invalidates all of the user's refresh tokens
- Logs: `auth.password.changed`

### 3.5 Password Reset

```
POST /api/v1/auth/password/reset/request   — sends email
POST /api/v1/auth/password/reset/confirm   — reset via token
```

- Reset token: one-time use, TTL 1 hour
- Rate limit: 3 requests/hour/email

## 4. RBAC

### 4.1 Levels (Scopes)

| Level         | Description                    | Context           |
|---------------|--------------------------------|-------------------|
| `global`      | Global admin permissions       | Entire system     |
| `organization`| Permissions within an org      | `org_{id}`        |
| `project`     | Permissions within a project   | `proj_{id}`       |

### 4.2 Roles

| Role      | Description                                     |
|-----------|------------------------------------------------|
| `Owner`   | Full control, including deletion              |
| `Admin`   | Manage members, settings                      |
| `Member`  | Work with tasks, agents, files                |
| `Viewer`  | Read-only access                              |

### 4.3 Permission Matrix

| Action                            | Owner | Admin | Member | Viewer |
|-----------------------------------|:-----:|:-----:|:------:|:------:|
| View projects                     | ✅    | ✅    | ✅     | ✅     |
| Create/edit tasks                 | ✅    | ✅    | ✅     | ❌     |
| Manage agents                     | ✅    | ✅    | ✅     | ❌     |
| View audit logs                   | ✅    | ✅    | ❌     | ❌     |
| Manage members                    | ✅    | ✅    | ❌     | ❌     |
| Project settings                  | ✅    | ✅    | ❌     | ❌     |
| Delete project                    | ✅    | ❌    | ❌     | ❌     |
| Manage organization               | ✅    | ❌    | ❌     | ❌     |
| Global settings                   | ✅*   | ❌    | ❌     | ❌     |

\* Global Owner only

### 4.4 Access Resolution

1. Check authentication (valid access token)
2. Determine context (global/org/project)
3. Check role within context
4. Check specific permission for the role
5. If no permission → `403 Forbidden`

### 4.5 Inheritance

```
global:Owner → all permissions on everything
global:Admin → manage organizations (no deletion)
org:Owner → all permissions within the organization
org:Admin → manage organization members
proj:Owner → all permissions within the project
proj:Member → task CRUD, work with agents
proj:Viewer → read-only
```

Permissions do not auto-inherit between levels.
An organization Owner has no permissions in projects they are not added to.

## 5. Security

- Passwords: bcrypt, min 12 characters
- JWT signature: RS256, keys stored in SecretProvider
- Refresh tokens stored in DB with hash (not plaintext)
- All authentication endpoints — HTTPS only
- Account lockout: 5 failed attempts → 15 min lockout
- All tokens revoked on password change / deactivation
