# UPCP Project Audit — Agent Reference

> Audit date: 2026-08-08 | Auditor: AI Agent | Version audited: 0.16.0 (develop)
> **Doc cleanup applied**: 2026-08-08 — 13 contradictions fixed (see §6 for status)

## 1. Project Identity

**UPCP** — Universal Project Control Plane. Self-hosted platform for collaborative work between humans and AI agents on software engineering projects.

- **Stack**: Python 3.12 / FastAPI / SQLAlchemy 2 / PostgreSQL / Redis | React 19 / TypeScript / Vite / Tailwind / shadcn/ui
- **Deployment**: Docker Compose (single-node, localhost)
- **Interfaces**: REST API (50+ endpoints), MCP Server (20+ tools), CLI (Typer)
- **Version**: 0.16.0 (pre-1.0, SemVer 0.MINOR.PATCH)

## 2. Codebase Metrics

| Dimension | Count | Notes |
|-----------|-------|-------|
| Backend Python files | 181 | In `backend/app/` |
| Backend lines of code | ~9,600 | Production only |
| Backend test files | 62 | In `backend/tests/` |
| Backend migrations | 19 | Alembic |
| Frontend TS/TSX files | 157 | In `frontend/src/` |
| Frontend lines of code | ~15,200 | Production only |
| Frontend test files | 34 | 238 tests |
| API routers | 12 | v1 endpoints |
| MCP tools | 20+ | Read + write |
| DDD contexts | 13 | See §3 |
| Documentation files | 48+ | docs/, specs/, tasks/ |

## 3. Bounded Contexts (DDD)

All contexts live under `backend/app/`:

| Context | Files | Purpose | Status |
|---------|-------|---------|--------|
| `shared/` | 16 | Config, DB, Redis, logging, rate limiting, secrets, pagination, IDs, tracing | **Complete** |
| `projects/` | 3 | Project CRUD | **Complete** |
| `structure/` | 3 | Component, Module CRUD | **Complete** |
| `delivery/` | 6 | Feature, Task, Subtask, lifecycle state machine, dependencies, workflow | **Complete** |
| `quality/` | 3 | AcceptanceCriterion, DoDItem, Evidence, ReviewRound, ReviewFinding | **Complete** |
| `audit/` | 3 | AuditEvent append-only log | **Complete** |
| `gitread/` | 4 | Local/GitHub/GitLab read-only adapters | **Complete** |
| `reporting/` | 6 | Dashboard, attention, portfolio, reports, health | **Complete** |
| `identity/` | 13 | User, Org, Membership, JWT, RBAC, Agent tokens, middleware | **Complete (1 TODO)** |
| `auth/` | 2 | Auth models + service | **Complete** |
| `search/` | 1 | Global search endpoint | **Complete** |
| `llm/` | 2 | LLM gateway + secret redaction | **Complete** |
| `mcp/` | 5 | MCP server, tools, context packs, schemas | **Complete** |

## 4. What Is Actually Implemented

### 4.1 Fully Working (backend + frontend + tests)

- **Project CRUD**: Create, read, update, delete projects with pagination, filters, sorting
- **Structure**: Components and Modules with CRUD
- **Delivery**: Features, Tasks, Subtasks with CRUD, lifecycle state machine (10 states), dependencies (DFS cycle detection)
- **Quality**: AcceptanceCriteria, DoDItems with CRUD and stats
- **Audit**: Append-only audit trail for all entity changes
- **Git Integration**: Read-only local/GitHub/GitLab adapters, branches, commits
- **Auth & RBAC**: User/Org/Membership models, JWT (access+refresh), RBAC roles/permissions/bindings, Agent tokens, auth middleware on all endpoints
- **Agent Management**: Agent model, token creation/revocation, agent self-service endpoints
- **MCP Server**: JSON-RPC with 20+ read/write tools including workflow tools
- **CLI**: Typer-based with project/task/status commands
- **Reporting**: Daily reports with markdown export, attention dashboard (9 sections), portfolio overview, project health scores
- **Notifications**: Model + API (create, list, mark_read, mark_all_read, unread_count)
- **Search**: Global search across projects/features/tasks
- **LLM**: Gateway abstraction + secret redaction in output
- **Redis**: Client, health check, rate limiting (sliding window)
- **Secrets**: SecretProvider abstraction (env/file/composite)
- **Observability**: Structured JSON logging, correlation IDs, tracing middleware skeleton
- **Security**: CORS (configurable origins), SSRF validation, security headers (CSP, HSTS, X-Frame-Options), error sanitization, sort whitelist

### 4.2 Backend Complete, Frontend Partial

| Feature | Backend | Frontend Types/API | Frontend UI | Gap |
|---------|---------|-------------------|-------------|-----|
| Task Claim/Release/Heartbeat | DONE (M9) | Types + hooks exist | TaskDetailSheet shows data | No dedicated agent workflow UI |
| Clarification Flow | DONE (M9) | Types + hooks exist | ClarificationBanner component | No full clarification management page |
| Evidence Attach/Verify | DONE (M10) | Types + API functions | ReviewVerdictCard component | No evidence management page |
| Review Rounds/Findings | DONE (M10) | Types + API functions | ReviewVerdictCard component | No review management page |
| Agent Inbox/Playbook | DONE (M9) | Types + hooks exist | AgentActivitySummary | No dedicated agent center page |
| Context Pack | DONE (M9) | — | — | No frontend |
| Task Dependencies | DONE (M9) | — | — | No frontend |

### 4.3 Documented but NOT Implemented

| Feature | Documentation | Implementation |
|---------|--------------|----------------|
| OpenTelemetry full tracing | 7 architecture docs, observability spec | Tracing middleware skeleton only |
| Grafana dashboards | `docs/ops/grafana-dashboards.md` | Not implemented |
| Agent Center UX | `docs/ux/agent-center.md` | Not implemented |
| WebSocket notifications | PRD mentions WebSocket | Polling only |
| E2E critical flow tests | `docs/testing/e2e-critical-flows.md` | 12 Playwright tests (auth + basic integration only) |
| Permission matrix tests | `docs/testing/permission-matrix-tests.md` | Not implemented |
| MCP contract tests | `docs/testing/mcp-contract-tests.md` | Not implemented |
| Backup/restore procedures | `docs/ops/backup-restore.md` | Not implemented |
| Agent playbook (per-project) | PRD + agent docs | API endpoint exists, no UI or storage |
| Multi-org readiness | Architecture doc + DEC-0016 | Single default org only |
| Encrypted fields in DB | Security doc | Not implemented |
| Idempotency keys | MCP tools spec | Not implemented |

## 5. Milestone Completion Status

| Milestone | Version | Backend | Frontend | Status |
|-----------|---------|---------|----------|--------|
| M0 — Foundation | 0.2.0 | DONE | — | DONE |
| M1 — Projects & RBAC | 0.3.0 | DONE | — | DONE |
| M2 — Structure & Delivery | 0.4.0 | DONE | — | DONE |
| M3 — Git Read | 0.5.0 | DONE | — | DONE |
| M4 — MCP & CLI | 0.6.0 | DONE | — | DONE |
| M5 — Frontend Foundation | 0.7.0 | — | DONE | DONE |
| M6 — Reports & LLM | 0.8.0 | DONE | — | DONE |
| M7 — Auth, RBAC, Agents | 0.9.0 | DONE | DONE | DONE |
| M8 — Runtime Foundation | 0.10.0 | DONE | — | DONE |
| M9 — Agent Workflow MVP | 0.11.0 | DONE | Types+API | **Backend DONE, UI partial** |
| M10 — Evidence & Review | 0.12.0 | DONE | Types+API | **Backend DONE, UI partial** |
| M11 — Human Control UX | 0.13.0 | DONE | DONE | DONE |
| M12 — Critical Fixes | 0.14.0 | DONE | DONE | DONE |
| M13 — Architecture Cleanup | 0.15.0 | DONE | DONE | DONE |
| M14 — Performance & A11y | 0.16.0 | DONE | DONE | **DONE (not version-bumped)** |
| M15 — Production Ready | 0.17.0 | Planning | Planning | NOT STARTED |

**Overall project completion**: ~44.7% of tracked tasks (34/76), but ~70% of planned functionality is implemented when counting backend+frontend together.

## 6. Critical Findings

### 6.1 Contradictions

#### F1: SPEC-0015 naming conflict
- `specs/SPEC-0015-evidence-review.md` (M10 spec)
- `specs/SPEC-0015-m15-production-ready.md` (M15 spec)
- Two different specs share the same ID. The M15 spec should be SPEC-0017.

#### F2: Task lifecycle state machine — 3 different definitions
- `docs/prd/agent-workflow.md`: `open → claimed → in_progress → in_review → done`
- `docs/planning/upcp-v2-planning-report.md`: `backlog → ready → claimed → in_progress → done`
- `backend/app/delivery/lifecycle.py`: 10 states (actual implementation)
- The PRD and planning report do NOT match the actual implementation.

#### F3: Evidence verification states — 2 different definitions
- `docs/prd/evidence-and-review.md`: `pending | accepted | rejected`
- `specs/SPEC-0015-evidence-review.md`: `unverified → agent_verified → human_accepted / rejected / stale`
- The spec version matches the actual implementation. The PRD is outdated.

#### F4: M15 spec ignores existing M9-M11 backend work
- `specs/SPEC-0015-m15-production-ready.md` describes implementing claim, heartbeat, evidence, review endpoints as NEW work
- These are ALREADY IMPLEMENTED in M9-M11 (models, services, API, MCP tools)
- TASK-0098 also lists them as if they need to be built from scratch
- The real M15 work should be: frontend UI integration, E2E tests, observability, graceful shutdown

#### F5: VERSIONING.md says 0.16.0 "in progress" but M14 is complete
- PROJECT_STATUS.md: "Milestone: M14 — Performance & Accessibility (COMPLETE)"
- VERSIONING.md: "0.16.0 — M14 Performance & Accessibility (see pyproject.toml for authoritative value)" with no date
- CHANGELOG.md: "[0.16.0] — M14 — Performance & Accessibility (in progress)"
- All S16.1-S16.4 tasks are DONE. Version should be marked complete with date.

#### F6: Agent token verification TODO in completed task
- `backend/app/identity/auth.py:76`: `# TODO: Implement agent token verification (TASK-0068)`
- TASK-0068 is marked DONE in PROJECT_STATUS
- This indicates incomplete implementation

#### F7: Heartbeat timeout — 3 different values across docs
- `architecture/agent-workflow-state-machine.md`: 120 seconds
- `docs/prd/agent-workflow.md`: 7 min stale, 15 min dead
- `docs/agent/agent-playbook.md`: 30 min claim TTL
- Recommendation: pick one value (suggest 5 min stale, 15 min dead) and sync all docs

#### F8: JWT signing — RS256 vs HS256
- `docs/security/auth-rbac.md`: RS256 (asymmetric, RSA keys)
- `docs/architecture/secrets-management.md`: JWT_SECRET (symmetric → HS256)
- Actual code uses HS256 via JWT_SECRET
- auth-rbac.md is wrong

#### F9: Finding severity levels — 5 vs 3
- `docs/prd/evidence-and-review.md`: 5 levels (info, suggestion, minor, major, critical)
- `docs/architecture/review-engine.md`: 3 levels (info, warning, critical)
- Auto-close threshold also differs

#### F10: LLM integration — exists vs doesn't
- `docs/02-architecture.md`: "llm" as core module, "optional assistant layer"
- `docs/architecture/system-context.md`: "No outgoing connections to LLM providers"
- `docs/01-principles.md`: "Deterministic core; LLM only as assistant"
- Actual: `backend/app/llm/gateway.py` exists but may be inactive

#### F11: Evidence model — significantly different definitions
- PRD: hash (SHA-256), file_path, submitted_by, status (pending/accepted/rejected)
- Architecture data-model: url, metadata, no hash, no status, no submitted_by

#### F12: MCP tool names — PRD vs Architecture vs Playbook
- PRD uses: report_progress, report_completion
- Architecture uses: heartbeat_task, submit_task_for_review
- Playbook references: create_review_finding, task_get (don't exist)

#### F13: Missing entities in domain model
- `Spec` — listed in 03-domain-model.md, not in data-model or code
- `GitPullRequest` — listed in domain model, not implemented
- `Agent Inbox` — described in PRD, no DB table
- `NotificationPreference` — mentioned in DDD contexts, not in data model

### 6.3 Fixes Applied (2026-08-08)

| Finding | Fix |
|---------|-----|
| F1: SPEC-0015 conflict | Renamed M15 spec → `SPEC-0017-m15-production-ready.md` |
| F2: Task lifecycle | Updated `prd/agent-workflow.md` to match `lifecycle.py` (10 states) |
| F3: Evidence states | Added status header to `prd/evidence-and-review.md` pointing to code |
| F4: M15 ignores existing backend | Updated SPEC-0017 and TASK-0098 to acknowledge existing M9–M11 |
| F5: VERSIONING.md stale | Marked 0.16.0 as complete with date 2026-08-07 |
| F6: TODO in auth.py | Replaced stub with re-export from `agent_auth.py` |
| F7: Heartbeat timeout | Unified to 5 min stale / 15 min dead across all docs |
| F8: JWT RS256 → HS256 | Updated `security/auth-rbac.md` to HS256 |
| F9: Finding severity | Updated to `critical|major|minor|nit` (4 levels, matching code) |
| F10: LLM status | Clarified in `02-architecture.md`: UPCP doesn't call LLMs directly |
| F11: Evidence model | Added source-of-truth pointers to `prd/evidence-and-review.md` |
| F12: MCP tool names | Agent-playbook heartbeat timeout fixed; tool names are in `mcp-tools.md` |
| F13: Missing entities | Updated `03-domain-model.md` to match actual implementation |

### 6.2 Gaps

#### G1: No E2E tests for agent workflows
- Only 12 Playwright tests (auth + basic integration)
- `docs/testing/e2e-critical-flows.md` defines critical flows but they're not implemented
- Agent claim → heartbeat → evidence → review → done flow has no E2E coverage

#### G2: Frontend lacks agent workflow UI
- Backend has full claim/heartbeat/clarification/evidence/review APIs
- Frontend has types and API functions but no dedicated management pages
- TaskDetailSheet shows some data but no interactive workflow management

#### G3: Observability stack not implemented
- 7 architecture docs describe OTEL + Prometheus + Grafana + Loki + Tempo
- Only structured JSON logging and tracing middleware skeleton exist
- No metrics collection, no dashboards, no distributed tracing

#### G4: Agent playbook has no storage or UI
- PRD describes per-project playbook with YAML config
- API endpoint exists but returns hardcoded/empty data
- No admin UI for managing playbooks

#### G5: WebSocket notifications not implemented
- PRD and UX spec mention real-time WebSocket notifications
- Only polling-based notification system exists
- NotificationBell polls on interval

### 6.3 Risks

#### R1: Documentation overload
- 48+ docs for ~25K lines of code
- Many docs describe aspirational features, not current state
- Agents reading docs may get incorrect picture of what's implemented
- Recommendation: Mark docs as "implemented" / "planned" / "aspirational"

#### R2: Spec drift
- Multiple sources of truth (PRD, specs, planning report, actual code)
- Contradictions between them (see F2, F3, F4)
- Recommendation: Single source of truth = actual code + PROJECT_STATUS.md

#### R3: Single developer velocity assumption
- VERSIONING.md assumes "Solo developer + AI agent assistance, ~8-10 story points per 2-week sprint"
- M7-M14 were completed in ~2 weeks total (not 18 weeks as planned)
- This suggests either the estimates were very conservative or the scope was reduced
- Recommendation: Re-estimate M15 based on actual velocity

## 7. Recommended Next Steps

### Priority 1: Fix contradictions (1 day)
1. Rename SPEC-0015-m15-production-ready.md → SPEC-0017
2. Update PRD task lifecycle to match actual implementation
3. Update PRD evidence states to match actual implementation
4. Rewrite M15 spec to acknowledge existing M9-M11 backend work
5. Fix TODO in identity/auth.py (agent token verification)
6. Mark VERSIONING.md 0.16.0 as complete

### Priority 2: Complete M15 frontend integration (2-3 weeks)
1. Agent workflow UI: claim/release/heartbeat management
2. Clarification flow UI: request/answer/resolve
3. Evidence UI: attach/verify/accept/reject
4. Review UI: rounds/findings/verdict
5. Agent center page: active agents, claims, metrics
6. Context pack viewer

### Priority 3: E2E tests (1 week)
1. Auth flow E2E (login → dashboard → project → task)
2. Agent workflow E2E (claim → work → evidence → review → done)
3. Clarification flow E2E
4. Quality gate E2E

### Priority 4: Observability (1-2 weeks)
1. OpenTelemetry instrumentation
2. Prometheus metrics endpoint
3. Basic Grafana dashboards
4. Structured logging enhancement

### Priority 5: Production hardening (1 week)
1. Graceful shutdown
2. Health check improvements
3. Docker production config
4. Backup/restore procedures
5. Deployment documentation

## 8. File Reference

| File | Purpose |
|------|---------|
| `PROJECT_STATUS.md` | Current state, milestone tracking |
| `VERSIONING.md` | Version scheme, roadmap |
| `CHANGELOG.md` | Human-readable history |
| `docs/00-vision.md` | Product vision |
| `docs/INDEX.md` | Documentation index |
| `docs/prd/upcp-v2.md` | Full PRD |
| `docs/planning/upcp-v2-kickoff.md` | V2 kickoff |
| `docs/planning/upcp-v2-planning-report.md` | Full planning report |
| `docs/decisions.md` | ADRs (DEC-0001 through DEC-0026) |
| `specs/SPEC-0014-identity-access.md` | Auth/RBAC spec |
| `specs/SPEC-0015-evidence-review.md` | Evidence/review spec |
| `specs/SPEC-0016-human-control-ux.md` | UX spec |
| `specs/SPEC-0015-m15-production-ready.md` | M15 spec (CONFLICTING ID) |
| `tasks/TASK-0098-m15-production-ready.md` | M15 task (NEEDS REWRITE) |
| `backend/app/main.py` | FastAPI entry point |
| `backend/app/delivery/lifecycle.py` | Task state machine (source of truth) |
| `backend/app/identity/auth.py` | Auth service (has TODO) |
| `frontend/src/router.tsx` | Route definitions |
| `frontend/src/lib/api/` | API modules (11 files) |

## 9. Agent Operating Rules

When working on UPCP:

1. **TRUST the code over docs** — docs may be outdated or contradictory
2. **Read PROJECT_STATUS.md** for current state, not the PRD
3. **Read lifecycle.py** for task state machine, not the PRD diagram
4. **Check if backend already exists** before implementing M9-M11 features
5. **Use TDD** — write failing test first, then implement
6. **Feature branches** — never push directly to develop
7. **Update PROJECT_STATUS.md** after completing work
8. **Non-standard ports** — 3070 (frontend), 38081 (backend), 36382 (Redis)
9. **DDD boundaries** — respect context boundaries, don't import across contexts
10. **Token economy** — keep context small, read only what's needed
