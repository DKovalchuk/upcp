# Changelog

All notable changes to UPCP will be documented in this file.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
Versioning: [SemVer 2.0](https://semver.org/) — 0.x.y for pre-1.0 development, 1.0.0 when production-ready.

## [Unreleased]

### Fixed (S14.1 — M12 Critical Fixes)
- `/health` endpoint now checks PostgreSQL via `SELECT 1` (was Redis-only)
- HealthPage Database card shows real connection status (was hardcoded "Connected")
- HealthPage now shows Redis status card
- `HealthResponse` schema updated with nested `db` and `redis` fields
- TaskDetailSheet Execution tab shows real agent claims, heartbeats, clarifications, evidence, reviews (was 100% hardcoded mock data)
- Added GET endpoints: `/tasks/{id}/claims`, `/tasks/{id}/heartbeats`, `/tasks/{id}/clarifications`
- AgentActivitySummary fetches real agent activity from `/dashboard/agent-activity` (was static empty state)
- Added `GET /dashboard/agent-activity` endpoint (active agents with task + heartbeat data)
- ReportsPage: fixed `createReport` URL (`/reports` → `/reports/daily`) — generation was completely broken
- ReportsPage: export uses `apiRequest` wrapper (was raw `fetch`, no auth token)
- ReportsPage: fixed `revokeObjectURL` race condition (was called synchronously after `a.click()`)
- EntityFormDialog: replaced native `<select>` with shadcn `<Select>` component
- EntityFormDialog: fixed `useEffect` dependency causing form state loss on parent re-render
- EntityFormDialog: removed dead `subtaskFields` code
- ProjectList: imports field definitions from `entity-fields.ts` (was duplicated locally)

### Added (S14.1)
- `check_db_health()` function in `database.py`
- `DashboardService.active_agents()` method
- `useTaskClaims`, `useTaskHeartbeats`, `useTaskClarifications`, `useTaskEvidence`, `useTaskReviewRounds` hooks
- `useAgentActivity()` hook
- `AgentActivityItem` TypeScript type
- `HealthCheckResult` TypeScript type
- `exportReportMarkdown()` API function
- 19 new backend tests, 8+ new frontend tests

## [0.13.0] - 2026-07-27

### Added (M11)
- AttentionDashboardService: 9 sections (needs_review, open_questions, blocked_tasks, stale_claims, failed_dod, rejected_tasks, agent_verdicts_waiting, low_health_projects, recent_activity)
- Project health score calculation (weighted formula)
- PortfolioService: aggregate stats across all projects
- Notification model + migration 0016
- NotificationService: create, list, mark_read, mark_all_read, unread_count
- API: /dashboard/attention, /projects/{id}/health, /portfolio/overview, /notifications CRUD
- Attention Dashboard frontend: 7 sections with real data, auto-refresh 30s
- Notification Bell: unread count badge, dropdown with mark-as-read
- Saved Views: localStorage-backed filter persistence
- Keyboard Navigation: j/k, Enter, Esc, [/]

### Added (M10)
- Models: Evidence, ReviewRound, ReviewFinding with state machines
- DoDItem.required_evidence_type for evidence-gated quality
- Migration: 0015_create_evidence_review
- Services: EvidenceService, ReviewRoundService, ReviewGateService
- API: Evidence CRUD, review rounds, submit-for-review gate
- MCP: 4 new tools (list_evidence, attach_evidence, list_review_rounds, submit_review_verdict)

### Added (M9)
- Models: TaskClaim, Heartbeat, ClarificationRequest, TaskDependency
- Lifecycle: state machine with 10 states, valid transitions enforced
- Dependencies: DFS cycle detection, no-self-dep check constraint
- API: 4 workflow endpoints + 3 agent self-service endpoints
- MCP: 8 new workflow tools
- Migrations: 0012, 0013, 0014

### Added (M8)
- Redis integration (docker-compose, client, health check)
- Structured JSON logging with correlation IDs
- Sliding window rate limiter (per-route limits)
- SecretProvider abstraction (env/file/composite)
- Git adapter hardening + input validation
- Security headers (CSP, HSTS, X-Frame-Options, Referrer-Policy, Permissions-Policy)
- CORS configuration

### Added (M7)
- User, Organization, Membership, Session models + migrations
- JWT token service with access/refresh tokens
- Auth middleware for all endpoints
- Role, Permission, RoleBinding models + seed roles
- Auth endpoints (setup, login, logout, refresh, me, password change)
- Agent model + agent token authentication

### Added (Frontend)
- Dashboard page with stats cards, recent projects, activity feed
- Project detail page with tabbed layout (Overview, Structure, Delivery, Quality, Audit, Reports)
- Create/edit form dialogs (EntityFormDialog for all entities)
- Structure page (components + modules with expand)
- Delivery page (features + task tables with search)
- Task detail sheet (slide-over with tabs: Details, AC, DoD, Subtasks)
- Quality page (stats cards, progress bars, quality gate)
- Audit timeline page (filterable timeline)
- Reports page (list, generate daily, export markdown)
- Health page (backend status with auto-refresh)
- Dark mode toggle (Sun/Moon/Monitor via next-themes)
- Pagination component + URL sync (all list pages)
- Board/Kanban view with status columns
- Command Palette (Cmd+K)
- Drag-and-drop for Board View (@dnd-kit)
- Git integration UI (providers, branches, commits)
- Global search (CommandPalette debounced)

## [0.8.0] - 2026-07-26

### Added (M6 — Reports & LLM)
- Daily report generation with markdown export
- LLM summary layer for reports
- LLM redaction for secrets in output

### Added (M5 — Frontend Foundation)
- React 19 + Vite + Tailwind CSS scaffold
- shadcn/ui (base-ui variant) component library
- TanStack Router + Query integration
- App Shell with Sidebar and TopBar
- Design system components (StatusBadge, PriorityDot, EmptyState, ErrorState, ConfirmDialog)
- TypeScript types, API client, and React Query hooks
- Lazy loading, 404 route, ErrorBoundary

### Added (M4 — MCP & CLI)
- MCP server scaffold with JSON-RPC endpoint
- MCP tools: project_list, project_get, task_list, task_get, feature_list, feature_get
- MCP write tools: feature_update, task_update
- Context pack generator
- CLI with project, task, status commands
- Dashboard Stats, Quality Stats, Audit List API endpoints

### Added (M3 — Git Read)
- Git read integration with local adapter
- GitHub REST API adapter
- Git branches and commits endpoints

## [0.4.0] - 2026-07-25

### Added (M2 — Structure, Delivery, Quality)
- Component and Module CRUD (structure context)
- Feature, Task, Subtask CRUD (delivery context)
- Acceptance criteria, DoD items, quality gate
- Quality stats endpoint

## [0.3.0] - 2026-07-24

### Added (M1 — Projects & RBAC)
- Project CRUD with pagination, filters, sorting
- RBAC placeholder models (User, Role, Permission)
- Shared pagination, entity ID, response schemas

## [0.2.0] - 2026-07-24

### Added (M0 — Foundation)
- Repository scaffold with agent docs, Docker, Makefile
- Health endpoint (GET /health)
- Config, logging setup, error taxonomy
- Database engine, session, Base, Alembic setup
- Audit event append-only model and AuditService

## [0.1.0] - 2026-07-24

### Added
- Initial project setup
