# PROJECT_STATUS

Updated: 2026-10-17
Version: 0.22.0 (see `VERSIONING.md` for scheme)
Milestone: M19 ✅ DONE; M20 ✅ DONE (0.22.0 bumped 2026-10-17)
Current Task: root `tests/e2e` re-run fixed (branch `fix/root-e2e-networkidle`, MR pending); next from Queued
Blockers: none
Roadmap: See `ROADMAP_UNIFIED.md` (M16-M20) + SPEC-0025/0026 for current batch
Specs: SPEC-0024 (Test Environment — Comprehensive Quality Gate), SPEC-0025 (Dashboard Redesign, APPROVED), SPEC-0026 (Universal Filtering, DRAFT)

## Current Work (2026-10-17)

**Incident 2026-10-17 — dev/stage backend crash-loop (~10h) — RESOLVED:**
`alembic upgrade head` on container start failed on `DuplicateTable:
ix_task_feature_id`. Root causes: migration **0019** recreated 17 indexes
already created by 0008 (could never pass on any real DB — stage/test stuck
at `0017`); migration **0023** re-added columns from 0021 (would fail next).
Latent since August, exposed by the TASK-0136 deploy fix (MR !56) which made
compose run the freshly built image. Masked twice: the old deploy health loop
fell through to "complete", and jobs run on `network_mode=gitlab-local_default`
so host-loopback `wget localhost:38081` was never reachable from a job.
**Fixed via MR !60 (hotfix):** 0019/0023 made idempotent (red→green: empty-DB
full chain 24 upgrades → `0023 (head)`), deploy health checks now fail the job
(`exit 1` + compose logs), new `backend:migrations` CI job runs
`alembic upgrade head` on a fresh postgres:16 in the test stage.
**Fixed via MR !62:** health probe moved inside the app container
(`docker compose exec app`, 40×3s budget). **MR !61** added TASK-0128 Parts
C/D/E. Post-merge: stage healthy (`alembic 0023`, `RestartCount=0`, host 200).

**Merged 2026-10-17:** MR **!60** `hotfix/migrations-idempotent`
(`4a0e647`), MR **!61** `feature/TASK-0128-parts-cde` (`fd5a709`),
MR **!62** `fix/deploy-health-probe` (`ee3c45e`) — all pipelines green.

**Closed 2026-10-17 — TASK-0128 Parts C/D/E:** Part C e2e
(`dashboard-redesign.spec.ts`, 15 tests: 5-row visual+console-errors, KPI
drill-down, donut, attention/View-all, selector URL scoping, responsive
1440/768/375, mocked SSE critical event, dark mode, load <3s), Part D a11y
(+8 D1-D8 tests, aria-labels on KPI/donut), Part E security
(`test_dashboard_security.py`, 32 tests: 401s, SQLi, XSS JSON boundary,
rate-limit 429, CORS — no production gaps). Evidence: new specs 30/30 green;
full e2e vs baseline identical per-file failures (104→102, all pre-existing
mock rot) — no regressions; backend 944 passed; frontend 336/336.
TASK-0128 status → **PARTIAL**: A/B matrix rows (A5 velocity negative/boundary,
A8/A9 portfolio, part of B) remain untested.

### Prior session (2026-10-16) — see task files for detail

**Merged:** MR **!56** `feature/sprint7-polish` (sprint stack + dashboard AC
closure TASK-0120-0127 + CI tag mismatch fix + retention TASK-0136 + SPEC-0024
Phase 1 + npm lock fix; `develop` had been deleted server-side and was
restored first at `d73868e`). MR **!57** TASK-0119 port externalization
(`f79ca77`). MR **!58** docs sync (`126f37f`). MR **!59** version bump 0.22.0
(`3fcae74`, M20 ✅ — S22.1-S22.5 all closed).

**Known discrepancies (to sync):**
- SPEC-0024 Phase 2-5 pending (Phase 1 в develop).
- ~~Дубль файла TASK-0116~~ — resolved: помечен DUPLICATE (канонический `...-evidence.md`, DONE).

**Queued:**
- ~~TASK-0128 A/B matrix rows~~ — closed 2026-10-17 (see below, branch `feature/TASK-0128-parts-ab`).
- ~~Pre-existing e2e debt~~ — closed 2026-10-17 (TASK-0138): full `frontend/e2e` suite **153 passed / 0 failed** (was 102 failed). Root causes: mock catch-all registered LIFO-shadowing specific mocks, stale route shapes/selectors vs dashboard redesign+filtering, `networkidle` never settles with SSE, live-backend rate limiter 429, non-idempotent create data. 5 deleted tests = removed UI feature (verdict accept/reject buttons) + 1 vacuous stub, justified in TASK-0138.
- Product bug found via TASK-0138: public pages (`/setup`) get hard-redirected to `/login` by background notification polling — `notifications/unread-count` 401 on unauthenticated visit → `client.ts:83-90` `window.location.href='/login'`. Should skip polling (or tolerate 401) when unauthenticated; test-side workaround in `auth.spec.ts` (mocked endpoints).
- ~~Root `tests/e2e` suite re-run~~ — closed 2026-10-17: **21 passed / 0 failed** against the live dev stack (3 failures were `waitForLoadState('networkidle')` never settling with SSE open — same root cause fixed in `frontend/e2e/comprehensive-ui.spec.ts`; replaced with `'load'` in `tests/e2e/navigation.spec.ts`).
- SPEC-0024 Phase 2-5 (performance → chaos → security → integration).
- `bootstrap_upcp.py` scaffold port-var modernization (legacy `UPCP_HTTP_PORT`-style names).

**Merged:** MR **!56** `feature/sprint7-polish` → `develop` merged 2026-10-16
(merge commit `96b80ae`, pipeline green). Note: `develop` branch had been
deleted server-side and was restored first at its last known SHA `d73868e`.

**Branch:** `feature/sprint7-polish` — merged; 20 commits включая 5 коммитов
закрытия (dashboard AC, CI/CD fix, docs sync, SPEC-0024 Phase 1, lock fix):

| Batch | Scope | Status |
|-------|-------|--------|
| Dashboard Sprints 1-4 | SPEC-0025 S25.1-S25.8: KPI drill-down, donut, velocity, clickable attention, portfolio table, project selector, SSE activity, responsive + fix | ✅ merged |
| Filtering | SPEC-0026: backend filters + shared FilterBar/URL-sync, StructurePage, AgentCenter fix | ✅ merged (спека всё ещё DRAFT, задачи TASK-0129-0135 не созданы) |
| Sprint 5 | Core UX: task editing + password change | ✅ merged |
| Sprint 6 | Git-links wiring in TaskDetailSheet | ✅ merged |
| Sprint 7 | Quality tab CRUD + dead code cleanup | ✅ merged |
| Closure batch | TASK-0120-0127 AC gaps, test regressions, CI/CD fix, SPEC-0024 Phase 1, npm lock fix | ✅ merged (MR !56) |

**In progress:** none — next: pick from Queued.

**Known discrepancies (to sync):**
- SPEC-0024 Phase 2-5 pending (Phase 1 files теперь в develop после MR !56).
- ~~Дубль файла TASK-0116~~ — resolved 2026-10-16: `TASK-0116-m20-s22-2-file-uploads.md` помечен DUPLICATE (канонический файл — `...-evidence.md`, DONE).

**Closed 2026-10-16 — dashboard tasks TASK-0120…0127 (SPEC-0025):** all 8
tasks DONE after AC gap closure — status-filtered KPI drill-down, donut/velocity
sector click-through, "View all →" in attention, PortfolioTable (Status column,
row click, Show more >5), attention scoping by `?project_id` (backend endpoint
now accepts it), sticky project selector (fixed `main { overflow-x-hidden }`
silently breaking descendant sticky). Deviations recorded in task files:
single-select status filter (no comma-multi), no `week`/`since` params (not
consumed by delivery), portfolio done/total + server-side status not in schema.
Evidence: frontend 47 files / **336/336 tests pass** (34 regressions from
filter/sprint commits fixed in test mocks — verified against develop baseline),
backend 31 dashboard+attention tests pass, ruff/mypy/tsc/lint clean.
TASK-0128 marked **PARTIAL** — unit levels green, Parts C/D/E (e2e, a11y,
security) + dark-mode/responsive visual checks remain.

**Closed 2026-10-16 — CI deploy tag mismatch:** compose referenced port-less
`registry.gitlab.local/...:stage` (stale 2-month local images) while CI's
`upcp-*-stage` aliases were unread — deploys silently served old images. Fixed:
per-branch `FLOAT_TAG` (`:dev` on develop, `:stage` on main — main no longer
overwrites `:dev`), compose images parametrized via `UPCP_BACKEND_IMAGE` /
`UPCP_FRONTEND_IMAGE` (default `:5050/...:stage` for manual runs), deploy jobs
export the exact pulled tag, dead aliases removed. Evidence: CI lint
`valid: true`, `docker compose config` resolves expected refs, docs updated
(`docs/ops/docker-compose.md`, `docs/ops/ci-retention.md`).

**Done 2026-10-16 — CI retention (TASK-0136, variant A):** registry expiration
policy enabled (keep_n=10, SHA-only, dev/stage/latest protected; older_than=null —
OCI-index tags have no created_at), registry tags 81/58 → 11/11, build jobs now
drop local SHA tags + prune dangling after push, manual `maintenance:cleanup` job
added (lint valid), one-time host cleanup: 44 orphaned runner cache volumes
(18.84→11.43GB) + dead stage aliases removed, online GC confirmed automatic.
Docs: `docs/ops/ci-retention.md`.

**Known CI findings:** deploy tag mismatch и коллизия `:dev` исправлены
2026-10-16 (см. выше «Closed 2026-10-16 — CI deploy tag mismatch»).
Дополнительно в MR !56: `frontend/package-lock.json` синхронизирован с
recharts-деревом (npm ci в CI падал на рассинхроне lock-файла).

**Closed 2026-10-17 — TASK-0119 port externalization (S22.5):** all 14 AC
verified against real files. Gaps closed this session: `docker-compose.yml`
legacy vars (`UPCP_HTTP_PORT`/`UPCP_REDIS_PORT`/`UPCP_PROMETHEUS_PORT`/
`UPCP_GRAFANA_PORT`) renamed → `UPCP_PORT_*`; `docker-compose.stage.yml`
hardcoded redis `36382` + backend `38081` → `${UPCP_PORT_*:-default}`;
`.env.example` + local `.env` renamed to match. Evidence:
`docker compose --env-file .env.{dev,test,stage} config` resolves expected
ports for all three envs; backend 912 passed, frontend 336/336, tsc clean.
Follow-up: `bootstrap_upcp.py` scaffold templates still use legacy names
(internally consistent — separate modernization task).

**Merged 2026-10-17:** MR **!57** `feature/TASK-0119-port-externalization` →
`develop` (merge commit `f79ca77`, pipeline success).

**Queued:**
- ~~Version bump~~ — done 2026-10-17: **0.22.0** (M20 ✅).
- Component-gap follow-ups from B-matrix blocked rows (6): negative-count clamp in Dashboard health fallback (`?? 100` masks missing score), donut decimal rounding, `PortfolioProject` lacks `tasks_done/tasks_total` (needs type+backend), agent rows not navigable (`/agents/:id`), `progress_percent` not capped at 100, ProjectSelector `project_id` no client-side validation. Low/Medium severity — see TASK-0128 AC notes.
- SPEC-0024 Phase 2-5 (performance → chaos → security → integration).
- `bootstrap_upcp.py` scaffold port-var modernization (legacy `UPCP_HTTP_PORT`-style names).

## M17 Summary — Security & Stability

All 4 sprints completed and merged:

| Sprint | TASK | Focus | Status |
|--------|------|-------|--------|
| S19.1 | TASK-0104 | Critical bug fixes (5 frontend bugs) | ✅ Done |
| S19.2 | TASK-0105 | Security hardening (MCP auth, LLM, CSP, ownership, env flags) | ✅ Done |
| S19.3 | TASK-0106 | Database hardening (17 indexes, 26 ondelete, N+1 fix) | ✅ Done |
| S19.4 | TASK-0107 | Architecture cleanup (logging, dead code, inbox, lifespan, target) | ✅ Done |

**Evidence:** 732 tests pass, ruff + mypy clean, all pipelines green

## Test Environment — Comprehensive Quality Gate (SPEC-0024)

Three pillars: **Performance**, **Chaos Engineering**, **Security Testing**.

### Phase 1: Foundation ✅ Complete (2026-08-18)

| Component | Status | Files |
|-----------|--------|-------|
| docker-compose.test.yml | ✅ Expanded | Redis, Locust (master+workers), ZAP, Kali, seeder, observability stack |
| .env.test | ✅ Updated | 14 ports: core + perf + security + observability |
| Metrics middleware | ✅ Created | `backend/app/shared/metrics.py`, `metrics_middleware.py` |
| /metrics endpoint | ✅ Added | `backend/app/main.py` |
| Prometheus config | ✅ Created | `observability/prometheus-test.yml` |
| Loki config | ✅ Created | `observability/loki-config.yaml` |
| Tempo config | ✅ Created | `observability/tempo-config.yaml` |
| OTel Collector config | ✅ Created | `observability/otel-collector-config.yaml` |
| Grafana provisioning | ✅ Created | datasources + dashboards provisioning |
| Grafana dashboard | ✅ Created | `test/overview.json` — request rate, latency, errors, DB pool |
| Test data seeder | ✅ Created | `tests/infrastructure/seeder.py` — small/medium/large profiles |
| Locust mixed scenario | ✅ Created | `tests/performance/locustfiles/scenario_mixed.py` |
| Locust base class | ✅ Created | `tests/performance/locustfiles/common.py` — UPCPBaseUser |
| SPEC-0024 | ✅ Created | Full spec in `specs/SPEC-0024-test-environment.md` |

**Verification:** ruff clean, mypy clean, docker-compose valid, 16 existing tests pass.

### Test Environment Ports

| Service | Port | Purpose |
|---------|------|---------|
| Frontend | 3071 | Nginx → frontend |
| Backend API | 38082 | FastAPI + /metrics |
| PostgreSQL | 35434 | Database |
| Redis | 36383 | Cache/rate-limit |
| Locust | 38089 | Load testing UI |
| OWASP ZAP | 38090 | DAST security |
| Kali | 38091 | Pentest agent |
| Prometheus | 39091 | Metrics |
| Grafana | 33001 | Dashboards (8 total) |
| Loki | 3101 | Logs |
| Tempo | 3201 | Traces |
| OTel Collector | 4319/4320 | Telemetry |

### Phase Roadmap

| Phase | Scope | Status |
|-------|-------|--------|
| Phase 1: Foundation | docker-compose, metrics, seeder, basic Locust | ✅ Done |
| Phase 2: Performance | All Locust scenarios, concurrency, SLI/SLO, analyzer | Pending |
| Phase 3: Chaos | Docker chaos scripts, assertions, cascade failures | Pending |
| Phase 4: Security | SAST, DAST, API fuzzing, auth tests, Kali pentest agent | Pending |
| Phase 5: Integration | Aggregate reporter, CI/CD, Makefile targets, docs | Pending |

## UPCP v2 Project (Stage)

**Project ID:** d9313eae-7e0b-4060-85ca-2e5591faefd2
**Stage URL:** http://localhost:3070
**API:** http://localhost:38081

### Population Summary

| Entity | Count | Status |
|--------|-------|--------|
| Project | 1 | active |
| Components | 13 | all active |
| Modules | 81 | all active |
| Features | 26 | all active |
| Tasks | 56 | 34 done, 42 backlog |
| DoD Items | 105 | per done task |
| Acceptance Criteria | 33 | per done task |

### Overall Completion: **44.7%** (34/76 tasks done)

### Component Completion

| Component | Done | Total | % |
|-----------|------|-------|---|
| Auth Pages & Dashboard | 3 | 3 | 100% |
| Board View & Task Detail | 2 | 2 | 100% |
| MCP Server & REST API | 3 | 3 | 100% |
| Project Views | 2 | 2 | 100% |
| Settings & Accessibility | 2 | 2 | 100% |
| Task Claim & Heartbeat | 3 | 3 | 100% |
| Clarification Flow | 2 | 2 | 100% |
| Evidence Attachment & Verification | 2 | 2 | 100% |
| Review Rounds | 2 | 2 | 100% |
| User Registration & Login | 7 | 14 | 50% |
| RBAC & Authorization | 3 | 6 | 50% |
| Agent CRUD & Tokens | 2 | 4 | 50% |
| Redis Integration & Rate Limiting | 2 | 4 | 50% |
| Secret Management | 2 | 4 | 50% |
| Structured Logging & Metrics | 2 | 4 | 50% |
| Reports & Analytics | 0 | 2 | 0% |
| Notification System | 0 | 1 | 0% |
| Notification Channels | 0 | 2 | 0% |

## Sprint History (M15)

- [x] S17.1 (done) — Backend gaps: clarification REST, stale reaper, inbox events, lifecycle enforcement, agent metrics, agent detail endpoints
- [x] S17.2 (done, !35) — Agent Center page + Agent Detail page with metrics, claims, activity, clarifications
- [x] S17.3 (done, !36) — TaskDetailSheet dedicated tabs: Clarifications, Evidence, Reviews
- [x] S17.4 (done, !37) — Evidence/Review UI, Playwright E2E (23 tests), bugfixes

## Sprint History (M14)

- [x] S16.1 (done) — Performance: bundle, staleTime, BoardView. A11y: aria, touch targets
- [x] S16.2 (done) — Performance: lazy mount, dnd-kit, responsive. UX: password toggle, search, CommandPalette
- [x] S16.3 (done, !30) — Tests: ProjectList, TopBar, AppShell, AuthContext, api/client, e2e integration
- [x] S16.4 (done, !31) — Polish: transitions, micro-interactions. Test cleanup: 32→0 `as any`, shared helpers

## Stage Deployment

- **MR !15**: develop → main merged (2026-07-30)
- **Stage**: deployed and healthy (ports from `.env.stage`)
- **Backend**: healthy, DB + Redis connected
- **Fixes**: Redis port conflict resolved, hardcoded UPCP_SECRET_KEY

## Roadmap

```
0.17.0 ✅ → 0.18.0 → 0.19.0 ✅ → 0.20.0 → 0.21.0 ✅ → 0.22.0 ✅ → ...
   M15         M16        M17         M18         M19         M20
```

See `ROADMAP_UNIFIED.md` for full plan with sprint breakdown.

### M16: 0.18.0 — Notifications & Reporting (S18.1 done, S18.2-S18.4 pending)
### M17: 0.19.0 — Security & Stability ✅ DONE
### M18: 0.20.0 — UX Polish, Accessibility & Settings (planned, SPEC-0021)
### M19: 0.21.0 — Test Quality & Architecture ✅ DONE
### M20: 0.22.0 — Extended Features ✅ DONE (S22.1-S22.5 закрыты 2026-10-17)

### Comprehensive Audit (2026-08-12)

Full audit across all dimensions. See `AUDIT_M16_COMPREHENSIVE.md`.

**Scorecard:** 6.5/10
- Stability: 7/10 | Reliability: 7/10 | Code Quality: 6/10
- UX: 6/10 | Architecture: 7/10 | Completeness: 6/10

**Key findings:** 2 Critical, 14 High, 28 Medium, 16 Low
- Critical: query string bug, MCP auth bypass
- High: LLM stubs, broken Project Settings route, TopBar no-ops, missing indexes
- All findings mapped to M17-M20 tasks

## S15.1 Progress (Complete)

- [x] TASK-0091: S15.1 Quick Wins (2.4, 2.8, 2.10, 3.2, 3.4, 3.5)

### S15.1 Summary

**Backend:**
- PATCH endpoint for git providers (`/git-providers/{provider_id}`)
- `GitProviderUpdate` schema with optional fields
- `update_provider()` service method with partial update support
- OpenAPI documentation: summary + description on all 12 routers
- OpenAPI tags with descriptions in `main.py`
- 5 new PATCH endpoint tests (all passing)

**Frontend:**
- Settings page with theme toggle, API info, and about section
- `useProjectId` deduplication: 6 components refactored to use hook
- CommandPalette cleanup: removed inline projectId extraction
- Dead code removal: HealthScore, PageHeader, unused type definitions, stale assets
- **Delivery bug fixes (MR !17):**
  - Task counter: always fetch tasks regardless of expanded state
  - Drag-and-drop: explicit queryClient.invalidateQueries for all feature task queries after mutation; prevent onClick during drag
  - Feature status badge: compute from actual task statuses (done/in-progress/review) instead of stored API value
- TypeScript: 0 errors

**Verification:**
- Backend: 615/615 tests passed
- Frontend: 161/161 tests passed
- Ruff: All checks passed
- Mypy: 0 errors
- TypeScript: 0 errors

**Files Changed:** 34 files (722 insertions, 258 deletions)

## S15.2 Progress (Complete)

- [x] TASK-0092: S15.2 Backend N+1/Eager Loading/Pagination + Frontend api.ts Split (2.1, 2.2, 2.3, 3.1)

### S15.2 Summary

**Backend:**
- PortfolioService: batch queries (41→10 queries, 75% reduction)
- AttentionDashboardService: new `get_projects_health_batch()` method for batch health calculation
- Quality endpoints: added PaginationParams to AC, DoD, evidence, review-rounds list APIs
- Service methods return `(items, total)` tuples for pagination support
- MCP tools updated for new return type

**Frontend:**
- Split api.ts (600+ lines) into 10 domain modules:
  - `api/client.ts` — Core API client
  - `api/projects.ts`, `api/components.ts`, `api/modules.ts` — Structure CRUD
  - `api/features.ts`, `api/tasks.ts` — Delivery CRUD + agent workflow
  - `api/quality.ts` — AC, DoD, Evidence, Review
  - `api/dashboard.ts` — Dashboard, Stats, Notifications
  - `api/git.ts` — Git providers, branches, commits
  - `api/index.ts` — Re-exports all
- Backward-compatible re-exports via original api.ts

**Tests:**
- 17 new tests (N+1 query count, batch health, pagination)
- Backend: 632/632 tests passed
- Frontend: 161/161 tests passed
- Ruff: All checks passed
- Mypy: 0 errors
- TypeScript: 0 errors

**Files Changed:** 22 files (1553 insertions, 849 deletions)
**MR:** !18

## M11 Progress (Complete)

- [x] TASK-0083: Attention Dashboard API
- [x] TASK-0084: Attention Dashboard Frontend
- [x] TASK-0085: Notification Model & API
- [x] TASK-0086: Notification Frontend
- [x] TASK-0087: Project Health & Portfolio API
- [x] TASK-0088: Project Drill-down UX

### M11 Summary

**Backend:**
- AttentionDashboardService: 9 sections (needs_review, open_questions, blocked_tasks, stale_claims, failed_dod, rejected_tasks, agent_verdicts_waiting, low_health_projects, recent_activity)
- Project health score calculation (weighted formula)
- PortfolioService: aggregate stats across all projects
- Notification model + migration 0016
- NotificationService: create, list, mark_read, mark_all_read, unread_count
- API: /dashboard/attention, /projects/{id}/health, /portfolio/overview, /notifications CRUD

**Frontend:**
- Attention Dashboard: 7 sections with real data from API, auto-refresh 30s
- Notification Bell: unread count badge, dropdown with mark-as-read
- Saved Views: localStorage-backed filter persistence
- Keyboard Navigation: j/k, Enter, Esc, [/]
- TypeScript compiles, 140+ tests passing

## M10 Progress (Complete)

- [x] TASK-0077: Evidence + ReviewRound + ReviewFinding models + migration
- [x] TASK-0078: Evidence service + API endpoints
- [x] TASK-0079: Review service + API endpoints
- [x] TASK-0080: Submit-for-review gate
- [x] TASK-0081: MCP tools for evidence & review
- [x] TASK-0082: Evidence & review frontend (types + API functions)

### M10 Summary

**Backend:**
- Models: Evidence, ReviewRound, ReviewFinding with state machines
- DoDItem.required_evidence_type for evidence-gated quality
- Migration: 0015_create_evidence_review
- Services: EvidenceService, ReviewRoundService, ReviewGateService
- API: Evidence CRUD, review rounds, submit-for-review gate
- MCP: 4 new tools (list_evidence, attach_evidence, list_review_rounds, submit_review_verdict)
- Tests: 50 new, 537 total passing

**Frontend:**
- Types: Evidence, ReviewRound, ReviewFinding TypeScript interfaces
- API functions: evidence CRUD, review round operations
- TypeScript compiles, 140 tests passing

## M9 Progress (Complete)

- [x] TASK-0070: TaskClaim + Heartbeat Models
- [x] TASK-0071: ClarificationRequest Model
- [x] TASK-0072: Task Lifecycle State Machine
- [x] TASK-0073: Task Dependencies
- [x] TASK-0074: Agent Workflow Endpoints (claim, release, heartbeat, progress)
- [x] TASK-0075: Agent Inbox + Playbook (me, inbox, playbook endpoints)
- [x] TASK-0076: MCP Workflow Tools (8 tools: claim, release, heartbeat, clarification, review, inbox, playbook)

### M9 Summary

**Backend:**
- Models: TaskClaim, Heartbeat, ClarificationRequest, TaskDependency
- Lifecycle: state machine with 10 states, valid transitions enforced
- Dependencies: DFS cycle detection, no-self-dep check constraint
- API: 4 workflow endpoints + 3 agent self-service endpoints
- MCP: 8 new workflow tools
- Migrations: 0012 (claim/heartbeat), 0013 (clarification), 0014 (dependencies)
- Tests: 479 passing (was 396)

**Frontend:**
- Types: TaskClaim, Heartbeat, ClarificationRequest, AgentMe, AgentEvent
- API functions: claimTask, releaseTask, sendHeartbeat, updateProgress, getAgentMe, getAgentInbox, getAgentPlaybook
- TypeScript compiles, 140 tests passing

## M7 Progress (Complete)

- [x] TASK-0062: User/Org/Membership/LoginAudit models
- [x] TASK-0063: JWT Token Service
- [x] TASK-0064: Auth Middleware
- [x] TASK-0065: RBAC Models
- [x] TASK-0066: Auth Endpoints
- [x] TASK-0067: Auth Middleware for All Routes
- [x] TASK-0068: Agent Model + Tokens
- [x] TASK-0069: Seed Default Roles

## M8 Progress (Complete)

- [x] Redis integration (docker-compose, client, health check)
- [x] Structured JSON logging + correlation IDs
- [x] Sliding window rate limiter (per-route limits)
- [x] SecretProvider abstraction (env/file/composite)
- [x] Git adapter hardening + input validation
- [x] Security headers (CSP, HSTS, X-Frame-Options)
- [x] CORS configuration

## Comprehensive Audit (2026-07-25)

Full audit across API, UI, MCP, Security dimensions.

### Audit Results
- **API**: 20 findings (2C, 4H, 7M, 4L) — see COMPREHENSIVE_API_AUDIT_REPORT.md
- **UI/UX**: 44 findings (2C, 9H, 19M, 14L) — see frontend audit agent
- **Security**: 11 findings (3C, 3H, 3M, 2L) — OWASP Top 10
- **MCP**: 6 observations, 12 tools functional, 79 tests pass

### Issues Fixed (26 total)
- Test isolation bug (5 failing search tests)
- Mypy type errors (dashboard.py, quality.py)
- Docker frontend missing deps (cmdk, @dnd-kit)
- Health page proxy (/api/v1/health endpoint)
- Missing /reports route + empty projectId handler
- Breadcrumb showing UUID → filtered with label map
- ProjectTable rows not clickable → navigate on click
- ProjectTable not using StatusBadge → replaced
- New Project button non-functional → EntityFormDialog wired
- Edit/Delete buttons on ProjectDetail → handlers added
- Settings tab renamed to Reports
- TaskDetailSheet: AC/DoD/Subtask creation added
- TaskDetailSheet: responsive width (w-full sm:max-w)
- TaskDetailSheet: ListSection keys by item.id
- ConfirmDialog async-aware (doesn't close before mutation)
- PriorityDot accessibility (role=img, aria-label, tabIndex)
- useProjectId hook extracted (eliminates 7x duplication)
- formatRelativeTime utility extracted (eliminates 2x duplication)
- API sort_by whitelist (prevents injection)
- Security headers: CSP, Referrer-Policy, Permissions-Policy
- Vite proxy target fixed for local dev
- docker-compose.yml: VITE_API_URL + vite.config.ts mount

### Remaining (documented in COMPREHENSIVE_AUDIT_REPORT.md)
- No authentication (Critical — known, deferred to TASK-0062+)
- No rate limiting (High)
- Hardcoded secrets in defaults (Critical)
- Missing /settings page (Medium)
- Dead CSS custom properties (Medium)

## Last Result

TASK-0061 completed: Global Search.

- Backend /api/v1/search endpoint (projects, features, tasks)
- Frontend searchGlobal API function
- CommandPalette debounced search with results group
- 6 backend tests, 140 frontend tests, build passes

TASK-0060 completed: Git Integration UI.

- Git types, API functions, React hooks for git endpoints
- GitIntegrationPage with providers, branches, commits tables
- Git tab added to ProjectDetail, route /projects/:id/git
- 5 new tests, 140 total passing

TASK-0059 completed: Drag-and-drop for Board View.

- @dnd-kit/core for draggable cards + droppable columns
- DragOverlay shows card being dragged
- Column highlights on drag-over
- Dropping card on different column updates task status
- 2 new tests, 135 total passing

TASK-0058 completed: Command Palette (Cmd+K).

- Installed cmdk, created shadcn Command components
- CommandPalette with navigation + project-specific commands
- Global Cmd+K / Ctrl+K shortcut, TopBar search trigger
- Fuzzy search, keyboard navigation
- 7 new tests, 133 total passing

TASK-0056 completed: Pagination wired into all list pages.

- DataTablePagination integrated into ProjectList, DeliveryPage, AuditPage, ReportsPage
- useUrlPagination hook manages page/pageSize URL search params
- All API hooks pass offset/limit to backend
- Build passes, 126 tests passing

TASK-0057 completed: Board/Kanban view for Delivery page.

- BoardView component with 4 status columns (Backlog, In Progress, Review, Done)
- View toggle (List / Board) in DeliveryPage header
- Tasks fetched via useQueries for all features in parallel
- Click status badge to cycle task status
- Click task card to open TaskDetailSheet
- Search filter works in board view
- 7 new tests, 126 total passing

### Phase 0 (Foundation) — DONE
- TASK-0043: Fix type mismatches + sidebar navigation
- TASK-0044: Skeleton loading + toast system
- TASK-0056: Pagination component + URL sync (integrated into all list pages)

### Phase 1 (Core Pages) — DONE
- TASK-0045: Dashboard page with stats cards, recent projects, activity feed
- TASK-0046: Project detail page with tabbed layout (Overview, Structure, Delivery, Quality, Audit, Settings)
- TASK-0047: Create/edit form dialogs (EntityFormDialog for all entities)
- TASK-0048: Structure page (components + modules with expand)
- TASK-0049: Delivery page (features + task tables with search)
- TASK-0050: Task detail sheet (slide-over with tabs: Details, AC, DoD, Subtasks)

### Phase 2 (Extended) — DONE
- TASK-0051: Quality page (stats cards, progress bars, quality gate)
- TASK-0052: Audit timeline page (filterable timeline)
- TASK-0053: Reports page (list, generate daily, export markdown)
- TASK-0054: Health page (backend status with auto-refresh)

### Phase 3 (Polish) — DONE
- TASK-0055: Dark mode toggle (Sun/Moon/Monitor via next-themes)

### Key Decisions (ADRs)
- DEC-0006: Use URL pathname parsing instead of useParams for sub-routes
- DEC-0007: Sheet component for task detail (not a route)
- DEC-0008: Tabbed layout for project detail (URL-synced tabs)
- DEC-0009: EntityFormDialog pattern for all CRUD forms
- DEC-0010: 6-color palette with CSS variables for dark mode
- DEC-0011: sonner for toast notifications
- DEC-0012: PageSkeleton for loading states
- DEC-0013: URL-synced pagination with search params
- DEC-0014: Design system components (StatusBadge, PriorityDot, EmptyState, ErrorState, ConfirmDialog)

### Test Coverage (updated 2026-08-07)
- Frontend: 238 tests across 34 test files, all passing
- E2E: 12 Playwright tests (auth, integration)
- Backend: 189 tests, 90% coverage

## M5 Completed (Previous)
- MCP server scaffold with JSON-RPC endpoint
- MCP tools: project_list, project_get, task_list, task_get, feature_list, feature_get
- MCP write tools: feature_update, task_update (TASK-0042)
- Context pack generator
- CLI with project, task, status commands
- Dashboard Stats, Quality Stats, Audit List API endpoints

## Remaining Work

### Future Backlog (from SPEC-0013 §6)
- Notifications system
- Auth/RBAC UI

## UPCP v2 Planning (2026-07-27)

Full v2 planning completed. Documentation, UPCP population, and design.

### What was created

- **Kickoff doc**: `docs/planning/upcp-v2-kickoff.md`
- **Planning report**: `docs/planning/upcp-v2-planning-report.md`
- **PRD docs**: 4 files in `docs/prd/`
- **Architecture docs**: 11 files in `docs/architecture/`
- **Security docs**: 7 files in `docs/security/`
- **Agent docs**: 7 files in `docs/agent/`
- **UX docs**: 8 files in `docs/ux/`
- **Ops docs**: 7 files in `docs/ops/`
- **Testing docs**: 4 files in `docs/testing/`
- **ADRs**: DEC-0015 through DEC-0026 in `docs/decisions.md`

### UPCP populated

- Project: UPCP v2
- Components: 13
- Modules: 81
- Features: 26
- Tasks: ~50 with full metadata (milestone, priority, size, dependencies)

### Milestones defined

- **M7**: Identity, Access & Agent Foundation (Critical)
- **M8**: Runtime Foundation (Critical/High)
- **M9**: Agent Workflow MVP (High)
- **M10**: Evidence & Review Engine (High)
- **M11**: Human Control UX, Project Drill-down & Portfolio Insights (Medium)

### Next implementation

Start M7+M8 in parallel. First task: Add User model and migration.
See `docs/planning/upcp-v2-planning-report.md` §18 for full task list.

## Important Notes

- Use non-standard Docker ports.
- Use TDD.
- Keep context small.
- Read `AGENTS.md` before any task.
- All work via feature branches → merge to `develop`.
