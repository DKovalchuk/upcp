# SPEC-0028 — AuthN/AuthZ Rework: Web API vs Agent API Surfaces

**Status:** APPROVED (Dmitry review 2026-11-02 — "specs look good, work
can start"; decisions D1-D6 confirmed via AskUserQuestion 2026-11-02)
**Created:** 2026-11-02
**Owner:** Dmitry
**Source:** Dmitry 2026-11-02 review of `identity/middleware.py` +
layering audit (SPEC-0029); missed-scenario lesson → §6 Test strategy

## 1. Context — findings (verified against code 2026-11-02)

| # | Finding | Evidence | Severity |
|---|---------|----------|----------|
| 1 | Auth guard is path-string based; version/prefix change silently unprotects | `identity/middleware.py:135` (`startswith("/api/v1/")`, `startswith("/mcp")`); same hardcode `shared/rate_limit_middleware.py:33` | high |
| 2 | Everything outside the two prefixes bypasses AuthMiddleware — protection exists only if the author remembered `Depends(get_current_user)` → default-**ALLOW** | whole `/auth` router mounted at `/auth` (`main.py:164`), `/metrics`, any future prefix | high |
| 3 | `/mcp` router has zero own auth — sole protection is the string guard | `mcp/server.py:99-148` | high |
| 4 | **MCP principal not bound**: `request.state.agent_id` set by middleware never reaches handlers; tools take `agent_id` from tool **arguments** → authenticated agent A can act as agent B | `mcp/server.py` (no `Request` in dispatch), `mcp/tools.py:591+` | critical |
| 5 | Agent token `scopes` never enforced (field flows model → `CurrentAgent` → responses only) | `identity/agents.py:49`, `agent_auth.py:64` | high |
| 6 | AuthMiddleware does DB + Redis directly, embeds cache logic, duplicates agent-token logic | `middleware.py:53-91,181-217` → SPEC-0029 | high |
| 7 | Subject check duplicated: dependency re-queries DB uncached on every request | `identity/auth.py:65` | medium |
| 8 | `UPCP_DISABLE_AUTH` disables middleware **and** RBAC gates — one env opens everything (documented hermetic mode, but prod-reachable) | `config.py:55`, `permissions.py:75` | medium |
| 9 | Tests for the auth module existed yet missed the class «unauthorized request executes»: 401 asserted only on the two guarded prefixes; no enumeration over ALL routes; no MCP spoofing test; scopes untested | `tests/test_auth_middleware_protection.py` | high (process → §6) |

**Goals:** default-deny per API surface; no path strings in auth; separate
web (JWT) and agent (API key) authentication; principal bound to every
action; enforced scopes; RBAC coverage; surface-aware observability;
regression-proofed by route-enumeration tests.

## 2. Decisions (Dmitry, 2026-11-02)

- **D1 — Agent auth stays a static API key** (`X-Agent-Token`, SHA-256 at
  rest) **+ mandatory TTL + immediate revocation + hardening**: no header
  logging, `last_used_at` audit, per-surface rate limits, scope
  enforcement. Rejected for now, with reasons: key→short-lived JWT
  exchange — MCP clients cannot refresh programmatically; HMAC signing —
  clients cannot sign; mTLS — certificate ops burden. Key model kept as
  `key_id + secret` so HMAC/mTLS overlays remain possible for future
  non-MCP agent transports. Rationale: the payoffs of short-lived creds
  (bounded replay, revocability, audit) are reachable on a static key via
  TTL + revocation; the exchange flow's only extra — short wire lifetime —
  is unusable without client-side refresh.
- **D2 — Auth = FastAPI router dependencies, not middleware.**
  - Authenticated surfaces: blanket
    `include_router(..., dependencies=[Depends(web_auth)])` /
    `Depends(agent_auth)` → default-**deny** for every route of the surface.
  - Public surface: separate routers included WITHOUT auth deps —
    declared at composition root, no runtime path dictionary.
  - *Correction to the initially proposed «route decorator with empty
    deps»:* FastAPI **merges** router-level and route-level dependencies —
    a route cannot reset inherited deps. Default-deny therefore comes from
    surface-level blanket deps + a separate public router, not from
    overriding.
  - *Rejected alternative:* literal «own middleware per API» — middleware
    runs **before** routing; without reading path strings it cannot
    classify a request, which is exactly how finding 1 appeared.
    Per-API separation is preserved as per-API auth **dependencies**.
    Also rejected: `mount()` sub-applications (literal per-API middleware)
    — OpenAPI/docs merging cost + DI complexity.
  - Cross-cutting middleware (correlation, tracing, metrics, rate-limit)
    remain, differentiated by `request.state.api_surface` data (TASK-0173).
- **D3 — URL namespace:** no path changes now (agents work via MCP only);
  dedicated `/agent-api/v1` prefix — backlog §8.
- **D4 — RBAC:** extend existing `require_permission` (SPEC-0027) to the
  remaining dangerous mutations + add `require_role`/`require_superuser`.
  No policy engine.
- **D5 — Surface membership (initial):** *web* = the 16 domain routers
  under `/api/v1` incl. agent-management admin routes (JWT);
  *agent* = agent-self, workflow (claims/heartbeats), `/mcp` (agent key);
  *public* = `/auth/{setup,login,refresh}`, `/health`, `/api/v1/health`,
  `/metrics`, `/docs`, `/openapi.json`, `/redoc`. **Constraint:** TASK-0171
  inventories actual MCP callers first — AuthMiddleware accepts Bearer JWT
  on `/mcp` today; if internal callers rely on it, dual-accept temporarily
  with a tracked tightening.
- **D6 — Test process:** before implementing each task, jointly pin down
  behavior / boundaries / conditions / AC / test matrix (Dmitry
  2026-11-02). «Tests exist» is never evidence of completeness (§6).

## 3. Design

### 3.1 S28.1 — Surface registry + contract test — TASK-0168
- `app/api/registry.py`: `WEB_ROUTERS`, `AGENT_ROUTERS`, `PUBLIC_ROUTERS`
  + prefix constants — single source of truth; `main.py` includes routers
  from the registry (composition-time declaration, not runtime strings).
- Contract test: every registered route belongs to exactly one group;
  app-level direct routes (`/health`, `/metrics`, docs) registered
  explicitly in `PUBLIC_ROUTERS`; adding a route to an unclassified
  router fails the test.

### 3.2 S28.2 — Web auth dependency — TASK-0169 (depends: 0168, 0174, 0175)
- `web_auth` async dependency: Bearer extract → `TokenService.verify` →
  denylist → `SubjectStateService` (SPEC-0029) → `CurrentUser` +
  `request.state.api_surface="web"`. Sync I/O via `run_in_threadpool`
  inside the async dep (no event-loop blocking — also fixes finding 6's
  blocking behavior on the hot path).
- Blanket `dependencies=[Depends(web_auth)]` on web-surface includes;
  `/auth` protected routes keep `get_current_user`, which is reimplemented
  on top of the same services (SPEC-0029 S29.5).
- `AuthMiddleware` and `PUBLIC_PATHS` retired; test harness migrated
  (tests currently `add_middleware(AuthMiddleware)`); 401 response shapes
  preserved exactly (missing / invalid / denylisted / unknown-subject).

### 3.3 S28.3 — Agent auth dependency + key hardening — TASK-0170 (0168, 0174)
- `agent_auth` async dependency: `X-Agent-Token` → `AgentTokenService`
  (hash lookup, revoked/expired → 401, agent active, **scope check** →
  403, `last_used_at` single commit contract) → principal +
  `request.state.api_surface="agent"`.
- Scope requirements marked per route natively:
  `dependencies=[Depends(require_agent_scope("tasks:claim"))]`.
- Key policy: mandatory `expires_at` for newly issued keys (configurable
  max TTL), revocation already immediate (`revoked_at`).

### 3.4 S28.4 — MCP principal binding — TASK-0171 (depends: 0170)
- Pass the authenticated principal into JSON-RPC dispatch (route receives
  Starlette `Request`); tool handlers derive `agent_id` from the
  principal — tool-argument `agent_id` must equal it, else 403.
- Inventory MCP callers (D5) before tightening Bearer acceptance.

### 3.5 S28.5 — RBAC coverage — TASK-0172 (depends: 0169, 0175)
- `require_permission` on remaining dangerous mutations (inventory in
  task); `require_role`/`require_superuser` for admin-only operations;
  gates read principal from the new auth context; permission cache moves
  to the cache provider (SPEC-0029).

### 3.6 S28.6 — Surface-aware observability — TASK-0173 (depends: 0169, 0170)
- Auth deps set `request.state.api_surface` → correlation request-id
  prefix (`web:`/`agent:`), OTel span attributes `upcp.auth.surface`,
  Prometheus label `surface`, per-surface rate-limit policy.
- One shared implementation of each cross-cutting middleware, differentiated
  by data — no duplicated code paths.

## 4. Acceptance Criteria (Given/When/Then)

- **AC1 (default-deny, the missed scenario):** Given the auth-enabled app,
  When I enumerate **every** route of the web and agent surfaces via
  `app.routes` and request it without credentials, Then no route answers
  2xx (401 expected; only `PUBLIC_ROUTERS` members may succeed).
- **AC2 (public):** Given public routes, When requested unauthenticated,
  Then their normal behavior (login 201/200, health 200, docs 200).
- **AC3 (classification completeness):** Given a new route added to a
  router missing from the registry (or to a surface without its auth
  dep), When the contract test runs, Then it fails.
- **AC4 (agent surface isolation):** Given agent-surface routes, When
  called with missing/invalid/revoked/expired key → 401; with valid key
  but insufficient scope → 403; web JWT on agent-only routes → 401
  (subject to D5 caller inventory).
- **AC5 (principal binding):** Given authenticated agent A, When an MCP
  tool is called with `agent_id=B`, Then rejected; with `agent_id=A`, Then
  succeeds.
- **AC6 (scopes):** Given a token without the required scope, When the
  gated route is called, Then 403; with the scope → success.
- **AC7 (key lifecycle):** Given an expired key → 401; a revoked key → 401
  on the very next request (no cache window beyond existing TTLs).
- **AC8 (RBAC):** Given a user without the permission on a newly gated
  mutation → 403 (not 404); superuser → success; ungated reads unchanged
  (SPEC-0027 AC2 regression baseline).
- **AC9 (surface observability):** Given one web and one agent request,
  Then request-id prefixes, span attributes and metric labels differ by
  surface and are asserted by tests (log capture / span spy / metric read).
- **AC10 (no regressions):** full backend suite green, ruff + mypy clean,
  live authz suite 0 xfail; hermetic `disable_auth` mode still works for
  existing tests and is documented as test-only.
- **AC11 (no secret logging):** Given requests with credentials, When logs
  are captured, Then no `Authorization`/`X-Agent-Token` value appears
  (test asserts on captured log records).

## 5. Task decomposition

| Task | Scope | Depends on |
|------|-------|-----------|
| TASK-0168 | S28.1 surface registry + contract test | — |
| TASK-0169 | S28.2 web_auth dependency, AuthMiddleware retirement, test-harness migration | 0168, 0174, 0175 |
| TASK-0170 | S28.3 agent_auth dependency + key TTL/scopes | 0168, 0174 |
| TASK-0171 | S28.4 MCP principal binding + caller inventory | 0170 |
| TASK-0172 | S28.5 RBAC coverage extension | 0169, 0175 |
| TASK-0173 | S28.6 surface-aware correlation/tracing/metrics/rate-limit | 0169, 0170 |
| TASK-0174 | SPEC-0029 layering foundation (repos + cache + services) | — |
| TASK-0175 | SPEC-0029 dependency unification (`get_current_user`/`get_current_agent`/perm cache → services) | 0174 |
| TASK-0176 | SPEC-0029 cross-context cleanup (agent_endpoints/agent_self → delivery services) | 0172 |
| TASK-0177 | SPEC-0029 context-boundary contract test | — |

## 6. Test strategy (joint per-module design — Dmitry 2026-11-02)

For every task above, before implementation: a joint walkthrough producing
**behavior / boundaries / conditions / AC / test matrix** (positive,
negative, boundary × unit/integration/e2e), written into the task file.
Rules:

- Existing auth tests are a starting point, **not** proof of completeness
  (finding 9); every task explicitly lists the previously-missed scenario
  class it closes (AC1 enumeration = the canonical one).
- Security negatives are mandatory: cross-surface token use, revoked/expired
  key, scope denial, principal spoofing (AC5), unauthenticated enumeration
  (AC1), secret-in-logs (AC11).
- Red first: each task's failing tests exist before its implementation.

## 7. Risks & mitigations

- **MCP caller breakage** when Bearer is rejected on `/mcp` → D5 caller
  inventory first; dual-accept fallback tracked.
- **Test-harness migration volume** (many tests mount `AuthMiddleware`) →
  TASK-0169 keeps 401 shapes identical; migration is mechanical and
  evidenced by a full-suite run; middleware retired only after harness green.
- **Threadpool load** for auth deps → hot path is cached (subject cache,
  denylist, permission cache — SPEC-0029); measured in TASK-0173.
- **`disable_auth` remains a prod-reachable kill switch** → documented
  test-only; contract test asserts it is false in shipped config examples.
- **DDD:** new auth code stays in `identity`; surfaces consume it only via
  FastAPI `Depends` (public contract), per AGENTS §5.

## 8. Out of scope / backlog

- Dedicated `/agent-api/v1` URL prefix migration (D3).
- HMAC request signing / mTLS overlays for agent transports (D1).
- Policy engine (casbin), org/project-scoped RBAC bindings (SPEC-0027 Phase B).
- Immediate access-token revocation via `jti` (existing SPEC-0027 backlog).
