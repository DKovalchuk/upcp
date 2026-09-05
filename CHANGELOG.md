# Changelog

All notable changes to UPCP will be documented in this file.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
Versioning: [SemVer 2.0](https://semver.org/) — 0.x.y for pre-1.0 development, 1.0.0 when production-ready.

## [Unreleased]

### Test Environment — Phase 1: Foundation (SPEC-0024)
- **docker-compose.test.yml**: Expanded with Redis, Locust (master+workers), OWASP ZAP, Kali Linux, test data seeder, full observability stack (Prometheus, Grafana, Loki, Tempo, OTel Collector)
- **Metrics**: New `shared/metrics.py` with 11 Prometheus metrics (HTTP, business, infra) + `metrics_middleware.py` for automatic HTTP instrumentation
- **/metrics endpoint**: Added to `main.py` for Prometheus scraping
- **Observability configs**: `prometheus-test.yml`, `loki-config.yaml`, `tempo-config.yaml`, `otel-collector-config.yaml`
- **Grafana**: Provisioning for datasources + dashboards, test/overview.json dashboard
- **Test data seeder**: `tests/infrastructure/seeder.py` with small/medium/large profiles, clean-slate + seed pattern
- **Locust**: `tests/performance/locustfiles/common.py` (UPCPBaseUser) + `scenario_mixed.py` (mixed workload across all API endpoints)
- **.env.test**: 14 ports for core, perf, security, and observability services
- **SPEC-0024**: Full specification in `specs/SPEC-0024-test-environment.md`

## [0.21.0] — 2026-08-12 — M19 — Test Quality & Architecture

### S21.1: Test Infrastructure (TASK-0112)
- Centralized conftest.py with all model imports for create_all()
- Added pytest markers: slow, integration, unit
- Added @vitest/coverage-v8 to frontend

### S21.2: Service-Layer Tests (TASK-0113)
- test_delivery_service.py: FeatureService, TaskService, SubtaskService unit tests
- test_quality_service.py: EvidenceService, ReviewRoundService, QualityGate unit tests
- test_reporting_service.py: ReportService, NotificationService unit tests
- test_lifecycle_integration.py: full project→feature→task→evidence→review→complete

### S21.3: Event Bus (TASK-0114)
- shared/events.py: EventBus with subscribe/publish/error handling
- shared/event_setup.py: wires events to NotificationTrigger
- Replaced 7 direct NotificationTrigger calls with event_bus.publish()
- Wired setup_event_handlers() to app lifespan
- test_event_bus.py: 7 EventBus tests

### Bug Fixes
- Fixed 403 on GET /agents/{id} — removed ownership check for read access
- Fixed Base UI error #31 — removed Tooltip wrapper around DropdownMenuTrigger
- Fixed pipeline warnings: JWT key length, vi.mock hoisting, lint warnings, bandit B310, pip-audit fallback

## [0.20.0] — 2026-08-12 — M16 + M18 — Notifications, Analytics & UX

### M16: Notifications & Reporting (S18.2-S18.4)

#### Notification Channels (S18.2 — TASK-0101)
- NotificationChannel model: email/webhook channels with config, active toggle
- NotificationDelivery model: delivery tracking with status/errors
- Migration 0020: notification_channel + notification_delivery tables + indexes
- EmailChannel: SMTP send with TLS, config validation
- WebhookChannel: HTTP POST with HMAC-SHA256 signature, 3x retry
- ChannelService: CRUD, dispatch to all active channels, test send
- REST API: list, create, delete, toggle, test endpoints

#### Analytics Service (S18.3 — TASK-0102)
- AnalyticsService: project_trends, agent_performance, team_velocity, health_history, agents_overview
- 5 REST API endpoints with query params (weeks, days, project_id, agent_id)

#### Analytics Frontend (S18.4 — TASK-0103)
- AnalyticsPage with TrendChart, VelocityChart, AgentPerformanceCard
- ChannelsSettingsTab: backend-backed channel CRUD (replaces localStorage)
- /analytics route added
- 8 new API functions, 5 new hooks

### M18: UX Polish, Accessibility & Settings (S20.1-S20.4)

#### Accessibility (S20.1 — TASK-0108)
- BoardView: KeyboardSensor for accessible drag-and-drop
- FeatureSection/ComponentCard: div→button with aria-expanded/controls
- BreadcrumbBar: ol/li structure with aria-current="page"
- SavedViewsDropdown: aria-labels on trigger/delete buttons

#### Settings Redesign (S20.2 — TASK-0109)
- 5-tab settings page: Profile, Notifications, Channels, Appearance, About
- ARIA: tablist, tab, tabpanel roles with aria-label/aria-selected
- Toggle switches: role=switch with aria-checked

#### Notification UX (S20.3 — TASK-0110)
- Full /notifications page with type filter (Select dropdown) and read/unread toggle
- Click-to-navigate on notifications, error handling with toast
- Mark individual/all read with error handling

#### Project Dashboard (S20.4 — TASK-0111)
- HealthScoreCard: SVG ring chart with score and trend indicator
- TaskDistributionChart: SVG donut chart with legend
- VelocitySparkline: SVG bar chart (8 weeks)
- RecentActivity: audit event feed

### CI/CD Pipeline
- Restructured: CI (lint+test) → CD (build+deploy:dev auto on develop, deploy:stage manual on main)

## [0.19.0] — 2026-08-12 — M17 — Security & Stability

### Security Hardening (S19.2 — TASK-0105)
- MCP endpoints now require JWT Bearer token or X-Agent-Token (was: unauthenticated)
- LLM providers no longer return fake summaries — NullProvider raises NotImplementedError (501 for callers)
- CSP header hardened: removed unsafe-eval, added wasm-unsafe-eval
- Agent detail endpoints enforce ownership — non-admin users can only manage agents they created
- Auth/rate-limit middleware use explicit UPCP_DISABLE_AUTH / UPCP_DISABLE_RATE_LIMIT flags (was: env="test" guard)

### Database Hardening (S19.3 — TASK-0106)
- Migration 0019: 17 indexes on FK/status columns + 26 ForeignKeys with explicit ondelete (CASCADE/SET NULL)
- N+1 fix: agent_claims endpoint uses batch IN query instead of per-claim get

### Architecture Cleanup (S19.4 — TASK-0107)
- Notification triggers: all 7 exception handlers now log warnings instead of silently swallowing
- Deleted dead auth/ module (legacy RBAC, replaced by identity/)
- Agent inbox now queries AgentInboxEvent table (was: empty stub returning [])
- Migrated @app.on_event('startup') to lifespan context manager (no more deprecation warnings)
- Notification target resolves from task assignee (fallback: "system" only when no user found)

### Critical Bug Fixes (S19.1 — TASK-0104)
- Fixed fetchProjectTasks URL query string construction
- Project Settings route now shows correct tab
- TopBar Profile/Settings items navigate to /settings
- SettingsPage version reads from VITE_APP_VERSION (was: hardcoded "0.14.0")
- Dashboard "New Project" navigates to /projects

## [0.17.0] — 2026-08-11 — M15 — Agent Workflow

### Backend (S17.1)
- Clarification REST endpoints: POST /tasks/{id}/clarifications, POST /clarifications/{id}/answer
- Stale claim reaper: asyncio background loop + POST /internal/reaper/tick endpoint (5min stale, 15min dead)
- Agent inbox events: AgentInboxEvent model + CRUD (create, list, mark_read, mark_all_read, count_unread)
- Lifecycle enforcement: validate_transition() on TaskService.update() prevents illegal state changes
- Agent metrics: tasks_completed, success_rate, is_stale, status on GET /agents/{id}
- Agent detail endpoints: /agents/{id}/claims, /activity, /evidence, /reviews, /clarifications
- Migration 0018: agent_inbox_events table

### Frontend (S17.2–S17.4)
- Agent Center page: grid/table view, search, filters, create dialog (/agents)
- Agent Detail page: profile header + 5 tabs (Claims, Activity, Evidence, Reviews, Clarifications) (/agents/:id)
- TaskDetailSheet restructured: dedicated Clarifications, Evidence, Reviews tabs (6 tabs total)
- ClarificationBanner: context field, answer display, answer input, state-aware
- BoardView: agent avatar + heartbeat progress bar on task cards
- EvidenceTab: attach form, accept/reject actions
- ReviewsTab: create review round button
- Evidence/Review hooks: useCreateEvidence, useAcceptEvidence, useRejectEvidence, useCreateReviewRound

### E2E Testing
- 23 Playwright tests against real Docker environment (port 3072)
- Tests: health, projects, delivery, board, task detail, agent center, agent detail, navigation, search, dark mode
- nginx config fixes: server_name localhost, /health route to frontend

### Fixed
- TypeScript build: EvidenceCreate optional fields, null/undefined in ReviewVerdictCard, unused imports
- nginx 502: server_name missing localhost, /health proxied to backend instead of frontend
- TaskDetailSheet tab overflow: reduced from 8 to 6 tabs

## [0.16.0] — 2026-08-07 — M14 — Performance & Accessibility

### Performance (S16.1)
- Bundle splitting: lazy routes via React.lazy for all pages
- staleTime for React Query hooks (reduce unnecessary refetches)
- BoardView: single /tasks endpoint (was N parallel queries)

### Accessibility (S16.1)
- aria-labels on all icon-only buttons
- Touch targets ≥ 44px on interactive elements
- Horizontal scroll hints on wide tables

## [0.15.0] — M13 — Architecture & Backend Cleanup

### Backend (S15.1–S15.3)
- Git Provider PATCH endpoint
- OpenAPI documentation on all 12 routers
- N+1 query fixes in Search, PortfolioService (75% query reduction)
- Pagination consistency across quality endpoints
- Response schemas: Pydantic response_model on 15+ endpoints
- `/projects/{id}/tasks` endpoint with filters (status, feature, assignee)
- Eager loading for task claims, heartbeats, clarifications

### Frontend (S15.1–S15.3)
- Settings page with theme toggle, API info, about section
- `useProjectId` hook deduplication (6 components refactored)
- api.ts split into 10 domain modules
- Business logic extracted to hooks (useTaskDetail, useSubmitReviewVerdict)
- UUID resolution via component/module lookup maps
- CommandPalette cleanup, dead code removal
- Delivery bug fixes: task counter, drag-and-drop invalidation, feature status

### CI/CD
- Fixed REGISTRY variable in deploy job
- Fixed nginx DinD volume mount (Dockerfile.nginx)
- Added GIT_STRATEGY:clone + GIT_CLEAN_FLAGS for clean workspace
- Dev environment on port 3072, test on port 3071
- ENVIRONMENTS.md with all credentials and quick commands

## [0.14.0] - 2026-07-30

### Security (S14.2 — M12 Security Hardening)
- CORS: configurable origins via `UPCP_CORS_ORIGINS` env var (comma-separated)
- CORS: configurable allowed headers via `UPCP_CORS_ALLOW_HEADERS` env var
- CORS: wildcard `*` origins rejected in production envs
- SSRF: GitHub adapter validates owner/repo format (alphanumeric, dots, hyphens, underscores)
- SSRF: `validate_url_not_internal()` blocks private/internal IPs (127.x, 10.x, 192.168.x, 169.254.x, ::1)
- SSRF: `GitProviderCreate.provider_type` restricted to `Literal["github", "gitlab", "bitbucket", "local", "other"]`
- Error sanitization: catch-all `Exception` handler returns generic message (no stack traces)
- Error sanitization: git adapter errors no longer expose raw stderr
- Dependency scanning: `pip-audit`, `npm audit`, `trivy` jobs now block pipeline on failures

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
