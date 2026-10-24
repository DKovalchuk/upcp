# SPEC-0027 — Security Findings Closure (RBAC, JWT Validation, Logout Denylist)

**Status:** APPROVED (decisions confirmed by Dmitry 2026-10-24 via
AskUserQuestion: FastAPI-dependency RBAC; middleware user-lookup + Redis
cache; Redis-denylist for logout; executed in-session — owner waived §9
Pro-model escalation for this batch)
**Amended:** 2026-10-24 (during TASK-0145 implementation — §3.1 backfill
replaced by superuser-bypass; see Deviations in TASK-0145. Rationale:
a blanket Owner-backfill would also grant Owner to the deliberately
permission-less seeder members and destroy the authz negative control
for finding 1; also no non-superuser binding-less users exist outside
test data — `/auth/setup` is the only user-creation path and it already
creates Owner binding + superuser)
**Created:** 2026-10-24
**Source:** TASK-0142 Findings 1-5 (SPEC-0024 Phase 4); doc-code mismatch
**Owner:** Dmitry

## 1. Context

SPEC-0024 Phase 4 security suite closed with 3 `strict=False` xfail tests
(documented product findings) + 2 doc/dead-path findings. None may stay
silently waived. This spec closes findings 1-5.

| # | Finding | Severity | Decision |
|---|---------|----------|----------|
| 1 | RBAC seeded (Role/Permission/RoleBinding, 4 roles) but no runtime guard; Member PATCH project → 404 not 403 | high | FastAPI-dependency `require_permission` + explicit gates |
| 2 | AuthMiddleware verifies JWT signature only; deleted/nonexistent-user token accepted until exp | high | user-existence check in middleware + Redis cache |
| 3 | Access token alive after logout (refresh revoked only) | medium | Redis denylist by token fingerprint |
| 4 | `docs/security/auth-rbac.md`: wrong logout path, false "all tokens revoked on password change" | medium | implement refresh-revocation on password change + rewrite docs |
| 5 | `PUBLIC_PATHS` lists dead `/mcp/health` (404) | low | remove entry + regression test |

Findings 6-7 (ZAP/Kali info-level) — informational, no action.

## 2. Constraints (verified against code 2026-10-24)

- Access token payload = `sub, type, iat, exp` — **no `jti` claim**
  (`token_service.py:32`); denylist keys on token fingerprint instead.
- Auth router mounted at prefix **`/auth`** (`main.py:163`), not
  `/api/v1/auth/...` as docs claim. Middleware `PUBLIC_PATHS` uses
  `/auth/*` paths.
- Domain routers (16 files in `api/v1/`) never read identity — no
  `request.state.user_id` consumers; middleware sets it
  (`middleware.py:68`).
- `RoleBinding` created only for the first user as Owner
  (`service.py:56-62`). No user-registration path exists beyond
  `/auth/setup` (single-use, superuser + Owner) — so all *real* users
  hold either a binding or superuser; binding-less identities exist
  only in seeder test data (agent users = intentional negative
  controls). No backfill needed (§3.1 amendment) — superusers bypass
  gates instead.
- `get_current_user` (`identity/auth.py:32`) powers `/auth/me`,
  logout, password change — denylist must be enforced there too
  (finding-3 xfail test goes through `/auth/me`).
- Redis client: `shared/redis.py:get_redis_client()` with established
  graceful-degradation pattern (rate limiter precedent).

## 3. Design

### 3.1 S27.1 — RBAC enforcement (finding 1)

- New dependency `require_permission(action, resource)` in
  `backend/app/identity/permissions.py` (new; identity context — no
  cross-context imports):
  1. resolve `request.state.user_id` (401 if absent — middleware
     guarantees it for domain routes);
  2. load user's `RoleBinding` (scope `global` + `org`) → `Role` →
     `RolePermission` → `Permission.action/permission` pairs;
  3. cache resolution in Redis (`rbac:user_perms:{user_id}`, TTL 60s,
     invalidatable); on Redis/DB-cache miss → direct DB query;
  4. no match → `HTTPException(403)`.
- **Gate set (Phase A — admin-dangerous only, minimal blast radius):**
  - `POST/PATCH/DELETE /api/v1/projects` → `create/update/delete:project`
    (Member PATCH project → **403** — closes xfail
    `test_rbac.py::test_member_update_project_enforces_role`);
  - agent management mutations (create/token/revoke/delete) →
    `manage:agent`;
  - user-management mutations, where endpoints exist → `manage:user`.
- **Phase B (explicitly OUT of scope, backlog):** per-CRUD gates on
  structure/delivery/quality; project-scoped bindings
  (`RoleBinding.project_id` exists but unused); org hierarchy.
- **Superuser bypass (amended 2026-10-24, replaces backfill):** the gate
  allows `is_superuser=True` users before role resolution — mirrors the
  existing `_require_agent` admin check (`agent_endpoints.py`). Covers
  `/auth/setup` first user and seeder admin without any data migration.
  Binding-less **non-superuser** users are rejected (403) — in practice
  these exist only as seeder agent users, which *must* stay
  permission-less for the authz negative controls. **Rejected
  alternative:** backfill-Owner-to-all-binding-less — would silently
  promote seeder members and falsify finding-1 closure.
- Default for ungated domain routes: **any-authenticated** (unchanged).

### 3.2 S27.2 — User-existence check in middleware (finding 2)

- In `AuthMiddleware` after `verify_access_token`, user-JWT path only
  (agent-token path already DB-checked):
  1. cache lookup `auth:user:{sub}` (`"1"` / `"0"`, TTL 60s, negative
     caching included);
  2. miss → DB: `user_account` exists AND active;
  3. absent/deleted/disabled → `401` (`WWW-Authenticate`), same shape
     as invalid token.
- Cache invalidation: TTL-bounded (60s max staleness) + explicit delete
  hook on user deletion if such path exists.
- Closes xfail `test_tokens.py::test_nonexistent_user_rejected_on_domain_endpoint`.

### 3.3 S27.3 — Logout denylist (finding 3)

- Key: `auth:deny:{sha256(raw_access_token)}`, value `1`, TTL = `exp - now`
  (≤15 min — self-expiring, no cleanup job).
- Write: `AuthService.logout()` adds fingerprint alongside refresh
  revocation.
- Read: shared helper `is_token_denied(token)` checked in **both**
  `AuthMiddleware` (user-JWT path) and `get_current_user` — after
  signature verification, before accepting.
- Redis unavailable → **degrade to allow** + structured warning log
  (matches rate-limiter precedent; availability over a ≤15-min
  revocation window; documented in auth-rbac.md).
- Closes xfail `test_tokens.py::test_access_token_rejected_after_logout`.
- All 3 xfails flip from `strict=False` to **strict pass** (xfail mark
  removed) in the same task that closes them.

### 3.4 S27.4 — Password change revocation + docs + dead path (findings 4-5)

- `AuthService.change_password` success path → revoke **all** of the
  user's refresh tokens (docs already promise this; OWASP-aligned).
  Other sessions' access JWTs remain until exp — documented limitation.
- `docs/security/auth-rbac.md` rewrite: actual paths (`/auth/*`), actual
  claims (`sub/type/iat/exp` — no `jti`, no `roles/scopes`), denylist
  behavior + Redis-degradation note, password-change semantics, RBAC
  dependency usage examples.
- Remove `/mcp/health` from `PUBLIC_PATHS`; add regression test: every
  `PUBLIC_PATHS` entry resolves to a registered route (static/docs
  entries whitelisted).

## 4. Acceptance Criteria (Given/When/Then)

- **AC1 (finding 1):** Given a user with `Member` role, When
  `PATCH /api/v1/projects/{id}` with their JWT, Then **403** (not 404);
  Given `Owner` → same PATCH succeeds; xfail removed → strict pass.
- **AC2 (gates don't regress reads):** Given any authenticated user,
  When `GET` on domain endpoints (projects list, dashboard, analytics),
  Then status unchanged from pre-spec baseline.
- **AC3 (finding 2):** Given a valid-signature JWT whose `sub` does not
  exist, When any domain GET, Then **401**; second identical request
  served from negative cache (no DB hit — verified by query counter or
  cache-spy in unit test).
- **AC4 (finding 3):** Given logged-in user, When logout succeeds, Then
  same access token → **401** on both middleware-protected domain route
  and `/auth/me`; refresh rotation of the revoked token → 401 (existing).
- **AC5 (Redis degradation):** Given Redis connection refused, When
  authenticated request arrives, Then request **succeeds** (denylist +
  cache fail-open) and a structured warning is logged.
- **AC6 (finding 4):** Given password change success, Then all user's
  refresh tokens invalid (rotation → 401); docs state actual paths and
  claims — verified by doc-literal test on logout path.
- **AC7 (finding 5):** Given new `PUBLIC_PATHS` regression test, Then
  every entry maps to a registered route (allowlist: `/docs`, `/redoc`,
  `/openapi.json`); `/mcp/health` absent.
- **AC8:** backend suite green (`pytest`), `ruff`+`mypy` clean, authz
  live suite: 55/55 with **0 xfail** (findings 1-3 strict).
- **AC9 (amended):** superuser bypass — Given a superuser **without**
  any RoleBinding (seeder-admin shape), When gated mutation with their
  JWT, Then succeeds; Given a binding-less non-superuser (seeder-member
  shape), Then 403; no data migration required.

## 5. Task decomposition

| Task | Scope | Depends on |
|------|-------|-----------|
| TASK-0145 | S27.1 RBAC dependency + Phase-A gates + superuser bypass | — |
| TASK-0146 | S27.2 middleware user-existence + Redis cache | — (parallel-safe: different middleware sections) |
| TASK-0147 | S27.3 logout denylist + `get_current_user` check + xfail flips | TASK-0146 (same middleware file) |
| TASK-0148 | S27.4 password-change revocation + docs rewrite + PUBLIC_PATHS cleanup | TASK-0145 (PUBLIC_PATHS/B) |

## 6. Test strategy

- Red first: new hermetic unit tests per AC (auth-enabled `TestClient`,
  fake/mock Redis — investigate existing auth-test harness in task);
  the 3 live-stack xfails serve as integration red until flipped.
- Green: minimal implementation per task; each task self-consistent.
- Negative/boundary: no-binding user (post-backfill), disabled user,
  expired-vs-denied distinction (expired → 401 invalid; denied → 401),
  Redis-down paths for both caches.
- Verification: targeted pytest → full backend suite → authz live suite
  against test stack (compose up → test → `docker compose stop`).

## 7. Risks & mitigigations

- **403-locking existing installs** → superuser bypass (AC9) covers
  every real user-creation path + Phase-A-only gate set + read-regression
  test (AC2).
- **Per-request Redis cost** → 2 cached reads (user-exists, denylist);
  TTL caches keep DB hits rare; measured in verification run.
- **Security-through-degradation on Redis-down** → fail-open is a
  conscious, documented tradeoff (AC5); fail-closed would mean total
  outage on Redis loss.
- **DDD:** all new code lives in `identity` context; no other context
  imports internals (dependency is a public FastAPI Depends).

## 8. Out of scope (backlog)

- Phase B per-CRUD permission gates (structure/delivery/quality).
- ZAP authenticated baseline (DAST `-H` research) — separate task.
- Security results → Grafana dashboard wiring.
- Session listing / per-device logout UI; access-token revocation on
  password change beyond refresh (needs jti → token format change).
