# SPEC-0029 — Identity Layering: Services → Repository + Cache Provider

**Status:** APPROVED (Dmitry review 2026-11-02 — "specs look good, work
can start"; design confirmed via discussion 2026-11-02)
**Created:** 2026-11-02
**Owner:** Dmitry
**Source:** Dmitry 2026-11-02 remark on `identity/middleware.py` +
full identity/layering audit of 2026-11-02

## 1. Context — findings (verified against code 2026-11-02)

Dmitry's rule (recorded): **middleware (presentation) must not touch DB or
Redis directly — only through a service; inside the service, data access
goes through a repository; caching is a separate service/provider that
talks to the cache subsystem and falls back to the DB via the repository
when the cache is stale/absent.**

| # | Finding | Evidence |
|---|---------|----------|
| 1 | Middleware queries the DB directly (`SessionLocal` + `db.get(User)`) | `middleware.py:53-70` |
| 2 | Agent-token branch does inline queries + `db.commit()` inside dispatch | `middleware.py:181-217` |
| 3 | Cache-aside logic (Redis → DB → best-effort write) embedded in middleware as module functions — source cannot be swapped through a service | `middleware.py:73-91` |
| 4 | Agent-token verification duplicated: middleware (`commit()`) vs `agent_auth.py` (`flush()`) — two different write semantics for `last_used_at`; `_hash_token` duplicated twice | `middleware.py:38,181-217`, `agent_auth.py:11,30-65` |
| 5 | Subject check duplicated: `get_current_user` re-queries DB **uncached** on every request while middleware uses a cache | `auth.py:65` |
| 6 | **No repository layer exists anywhere in the project** (`class *Repository` — 0 matches); all services query models directly through injected `Session` | repo-wide grep 2026-11-02 |
| 7 | `permissions.py` embeds DB query + Redis cache logic inline (same layering shape as finding 3) | `permissions.py:71-133` |
| 8 | `SessionLocal()` fallbacks outside DI | `mcp/tools.py:897`, `mcp/context_pack.py:25` |
| 9 | No boundary enforcement tooling (import-linter/contract tests); audits claimed «no cross-context violations» while `identity/agent_endpoints.py` imports `app.delivery.models`/`app.quality.models` and `api/v1/agent_self.py` imports delivery models | grep + `AUDIT_M16_COMPREHENSIVE.md:33` |

## 2. Decisions (Dmitry, 2026-11-02)

- **D1 — Target layering:** endpoint/dependency/middleware → **service**
  (business logic + cache policy) → **repository** (only `db.query` /
  `SessionLocal` in the auth path) + **cache provider** (only Redis access
  in the auth path). Presentation layer does zero data access.
- **D2 — Pilot on identity.** The pattern is established in the identity
  context (auth hot path) and replicated to other contexts in follow-up
  tasks — not a big-bang repository retrofit across 29 services.
- **D3 — Test seams move with the code**: tests currently patch
  `app.shared.database.SessionLocal` and `mw._fetch_user_state`
  (`tests/conftest.py:94`, `test_auth_middleware_user_check.py:131`) —
  seams relocate to repository/service and the tests are updated without
  losing coverage.
- **D4 — Behavior parity**: this is a refactor — 401/403 semantics, cache
  TTLs, fail-open/fail-closed behavior and commit invariants stay
  byte-for-byte equivalent unless SPEC-0028 explicitly changes them.

## 3. Design

### 3.1 S29.1 — Repositories — TASK-0174
```
identity/repositories.py
  UserRepository.get_auth_state(user_id) -> "active"|"unknown"|"disabled"
  AgentTokenRepository.find_by_hash(token_hash) -> AgentToken | None
  AgentTokenRepository.touch_last_used(record, when)   # single commit point
  AgentRepository.get(agent_id) -> Agent | None
```
- The only module in the auth path importing `SessionLocal`/`db.query`.
- Lazy `SessionLocal` import preserved (test seam per D3).

### 3.2 S29.2 — Cache provider — TASK-0174
```
identity/cache_provider.py
  AuthCacheProvider: get(key) / set(key, value, ttl) / delete(key)
  — wraps app.shared.redis.get_redis_client(), never raises to callers
  — injectable (constructor), tests substitute a fake provider
```
- Provider owns **access** to the cache subsystem only; TTL/strategy lives
  in services (D1).

### 3.3 S29.3 — SubjectStateService — TASK-0174
- `get(user_id) -> "active" | "unknown" | "disabled"`:
  provider.get(`auth:user:{sub}`) → hit returns; miss →
  `UserRepository.get_auth_state` → best-effort provider.set(TTL 60s).
  Redis outage → DB query (no auth bypass); DB authoritative.
- Single point of truth for SPEC-0028 `web_auth` and `get_current_user`.

### 3.4 S29.4 — AgentTokenService — TASK-0174
- `verify(raw_token, now) -> AgentPrincipal | None`: one `sha256`
  (removes `_hash_token` duplication), revoked/expired checks, agent
  active, `last_used_at` via `AgentTokenRepository.touch_last_used` with
  the **single** commit contract (service.py invariant: commit before
  response; replaces today's `commit()`-vs-`flush()` divergence).

### 3.5 S29.5 — Dependency unification — TASK-0175
- `get_current_user` / `get_current_agent` reimplemented over
  `SubjectStateService` / `AgentTokenService` (dedupe findings 4-5).
- `permissions.py` permission cache moves to `AuthCacheProvider`; DB query
  moves to a `PermissionRepository`; `require_permission` gate logic
  (fail-closed order, superuser bypass) unchanged.

### 3.6 S29.6 — Cross-context cleanup — TASK-0176
- `identity/agent_endpoints.py` (delivery/quality model imports) and
  `api/v1/agent_self.py` stop querying foreign contexts directly: foreign
  data access moves behind delivery/quality services (public contracts
  consumed via service calls; DDD per AGENTS §5).

### 3.7 S29.7 — Boundary enforcement — TASK-0177
- Contract test (import-linter or equivalent AST/grep gate): contexts may
  import only `shared` + their own internals + other contexts' public
  service/schema surfaces; `SessionLocal` outside `shared`/repositories
  flagged.

## 4. Acceptance Criteria (Given/When/Then)

- **AC1 (layering — amended 2026-11-04 after aspect review, scope made
  precise):** Given the request-auth hot path — `web_auth`, `agent_auth`,
  `get_current_user`, `permissions` — When grepping those modules for
  `SessionLocal`/`db.query`/direct redis access, Then hits exist only in
  `identity/repositories.py` + `identity/cache_provider.py` (enforced by
  `tests/test_identity_layering_contract.py`); package-wide `SessionLocal`
  is enforced by the boundary gate (rule 3). Known remaining violations
  outside the hot path, tracked in TASK-0178: `token_service.py`,
  `agent_endpoints.py`, `seed.py` still query directly; `denylist.py`
  still imports `app.shared.redis`; `permissions.py` still does
  `db.get(User, …)` for the superuser check.
- **AC2 (behavior parity):** Given the migrated auth stack, When the full
  backend suite runs, Then all existing auth/RBAC tests pass unchanged in
  semantics (401 shapes, TTL 60s, Redis-outage fail-open on
  denylist/subject cache, fail-closed RBAC).
- **AC3 (cache policy in service):** Given a cold cache, When
  `SubjectStateService.get` runs, Then exactly one DB read + one cache
  write; second call → zero DB reads (cache-spy test); Redis outage →
  served from DB without exception.
- **AC4 (single agent-token path):** Given middleware-deps and
  `/auth`-dependencies both authenticate agent tokens, Then one
  implementation verifies them; `last_used_at` written at one point with
  the commit-before-response invariant (regression test on immediate
  follow-up request).
- **AC5 (dedupe):** `sha256` token hashing and subject-state lookup each
  have exactly one implementation (import/grep contract).
- **AC6 (test seams):** tests can redirect DB and cache sources via the
  repository/provider seams; no test patches module-private middleware
  functions anymore (`mw._fetch_user_state` references gone).
- **AC7 (boundaries):** cross-context contract test green;
  `agent_endpoints.py`/`agent_self.py` contain no foreign-context model
  imports (TASK-0176 evidence).
- **AC8 (no regressions):** full suite green, ruff + mypy clean,
  coverage gate held (≥80%).

## 5. Task decomposition

| Task | Scope | Depends on |
|------|-------|-----------|
| TASK-0174 | S29.1-S29.4 repositories + cache provider + SubjectStateService + AgentTokenService | — |
| TASK-0175 | S29.5 dependency/permission-cache unification on services | 0174 |
| TASK-0176 | S29.6 cross-context cleanup of agent endpoints | 0172 (RBAC gates in same files) |
| TASK-0177 | S29.7 context-boundary contract test | — |

SPEC-0028 consumes this foundation: TASK-0169/0170 depend on 0174/0175.

## 6. Test strategy (joint per-module design — Dmitry 2026-11-02)

Each task carries a written **behavior / boundaries / conditions / AC /
matrix** before code (red first):

- Unit: repository query semantics per state; provider outage paths;
  service cache hit/miss/outage/stale-TTL; verify() lifecycle matrix
  (valid / revoked / expired / inactive agent / scope miss).
- Integration: real DB + fake Redis and real Redis + downed DB — both
  directions of the fallback; commit-invariant regression.
- Contract: AC1/AC5/AC7 as automated import/grep gates (not manual review).
- Parity: existing auth tests run against the new wiring unmodified
  where possible — divergence is a bug, not an update.

## 7. Risks & mitigations

- **Test-churn from seam moves (D3)** → done inside TASK-0174 with the
  full-suite run as the gate; no coverage loss (AC6).
- **Perf** — extra object indirection per request is negligible vs I/O;
  hot path stays cached (AC3); no per-request session creation added.
- **Scope creep to all 29 services** → D2 pilot; replication is backlog.
- **Async blocking (found in audit)** → SPEC-0028 S28.2/S28.3 declare
  auth deps as `async` with `run_in_threadpool` for the sync I/O this
  spec's services perform.

## 8. Out of scope / backlog

- Repository/cache retrofit for non-identity contexts (replication backlog).
- Async SQLAlchemy / async redis client migration.
- `mcp/tools.py`/`context_pack.py` `SessionLocal` fallbacks — folded into
  TASK-0176/0177 enforcement once MCP principal binding (SPEC-0028
  TASK-0171) lands.
