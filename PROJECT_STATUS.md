# PROJECT_STATUS

Updated: 2026-08-14
Version: 0.21.0 (see `VERSIONING.md` for scheme)
Milestone: M19 — Test Quality & Architecture (COMPLETE)
Current Task: M20 S22.4 (next sprint)
Blockers: none
Roadmap: See `ROADMAP_UNIFIED.md` for post-M15 plan (M16-M20, ~23 weeks)

## M17 Summary — Security & Stability

All 4 sprints completed and merged:

| Sprint | TASK | Focus | Status |
|--------|------|-------|--------|
| S19.1 | TASK-0104 | Critical bug fixes (5 frontend bugs) | ✅ Done |
| S19.2 | TASK-0105 | Security hardening (MCP auth, LLM, CSP, ownership, env flags) | ✅ Done |
| S19.3 | TASK-0106 | Database hardening (17 indexes, 26 ondelete, N+1 fix) | ✅ Done |
| S19.4 | TASK-0107 | Architecture cleanup (logging, dead code, inbox, lifespan, target) | ✅ Done |

**Evidence:** 732 tests pass, ruff + mypy clean, all pipelines green

## UPCP v2 Project (Stage)

**Project ID:** d9313eae-7e0b-4060-85ca-2e5591faefd2
**Stage URL:** http://localhost:3080
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
- **Stage**: deployed and healthy on localhost:3080
- **Backend**: localhost:38081 (healthy, DB + Redis connected)
- **Fixes**: Redis port 36382 (avoids dev conflict), hardcoded UPCP_SECRET_KEY

## Roadmap to 1.0.0

```
0.17.0 (done) → 0.18.0 → 0.19.0 → 0.20.0 → 0.21.0 → 0.22.0 → 1.0.0
   M15           M16       M17       M18       M19       M20      (after M20)
```

See `ROADMAP_UNIFIED.md` for full plan with sprint breakdown.

### M16: 0.18.0 — Notifications & Reporting (S18.1 done, S18.2-S18.4 pending)
### M17: 0.19.0 — Security & Stability (planned, SPEC-0020)
### M18: 0.20.0 — UX Polish, Accessibility & Settings (planned, SPEC-0021)
### M19: 0.21.0 — Test Quality & Architecture (planned, SPEC-0022)
### M20: 0.22.0 — Extended Features (planned, SPEC-0023)
### 1.0.0 — Production Release (after M20 + hardening sprint)

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
