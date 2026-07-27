# PROJECT_STATUS

Updated: 2026-07-27
Milestone: M9 — Agent Workflow MVP (In Progress)
Current Task: M9 complete → next: M10 Evidence & Review Engine
Blockers: none

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

### Test Coverage
- Frontend: 119 tests across 19 test files, all passing
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
