# Changelog

All notable changes to UPCP will be documented in this file.

## [1.0.0] - 2026-07-27

### Added
- M7: User, Organization, Membership, Session models + migrations
- M7: JWT token service with access/refresh tokens
- M7: Auth middleware for all endpoints
- M7: Role, Permission, RoleBinding models + seed roles
- M7: Auth endpoints (setup, login, logout, refresh, me, password change)
- M7: Agent model + agent token authentication
- M8: Redis integration (docker-compose, client, health check)
- M8: Structured JSON logging with correlation IDs
- M8: Sliding window rate limiter (per-route limits)
- M8: SecretProvider abstraction (env/file/composite)
- M8: Git adapter hardening + input validation
- M8: Security headers (CSP, HSTS, X-Frame-Options, Referrer-Policy)
- M8: CORS configuration
- M9: TaskClaim + Heartbeat models + migrations
- M9: ClarificationRequest model + migration
- M9: Task lifecycle state machine (10 states)
- M9: Task dependencies with DFS cycle detection
- M9: Agent workflow endpoints (claim, release, heartbeat, progress)
- M9: Agent inbox + playbook endpoints
- M9: 8 MCP workflow tools
- M10: Evidence, ReviewRound, ReviewFinding models + migration
- M10: DoDItem.required_evidence_type for evidence-gated quality
- M10: EvidenceService (create, list, verify, accept, reject)
- M10: ReviewRoundService (create, start, add_finding, submit_verdict)
- M10: ReviewGateService (submit-for-review quality gate)
- M10: Evidence & review API endpoints
- M10: 4 MCP evidence/review tools
- M11: AttentionDashboardService (9 sections)
- M11: Project health score calculation
- M11: PortfolioService (aggregate stats)
- M11: Notification model + migration 0016
- M11: NotificationService (CRUD + unread count)
- M11: Dashboard attention API + health + portfolio endpoints
- M11: Notification API endpoints
- M11: Attention Dashboard frontend (7 sections, auto-refresh)
- M11: Notification Bell (unread count, dropdown, mark-as-read)
- M11: Saved Views (localStorage-backed filter persistence)
- M11: Keyboard Navigation (j/k, Enter, Esc, [/])

## [Unreleased]

### Added
- M0: Repository scaffold, health endpoint, config, logging, errors
- M0: Database base, Alembic migrations
- M0: Audit event append-only model
- M1: Project CRUD with pagination, filters, sorting
- M1: RBAC placeholder (User, Role, Permission)
- M1: Shared pagination, IDs, response schemas
- M2: Component and Module CRUD (structure context)
- M2: Feature, Task, Subtask CRUD (delivery context)
- M2: Acceptance criteria, DoD items, quality gate
- M3: Git read integration (local + GitHub adapters)
- M4: MCP server, tools, context pack generator
- M4: Typer CLI with project/task/status commands
- M5: React frontend with Vite, Tailwind, shadcn/ui
- M6: Report generation, markdown export, LLM summary
- M6: LLM redaction layer for secrets
- Phase 1 audit fixes: DRY helpers, DDD boundaries, FK indexes

### Fixed
- Added missing FK indexes (migration 0008)
- Moved RBAC models to app/auth/ context
- Fixed quality→delivery boundary inversion

## [0.1.0] - 2026-07-24

### Added
- Initial project setup
