# UPCP v2 Kickoff

Updated: 2026-07-27

## 1. Current State

### What Exists

UPCP is a working modular monolith with:

- **Backend**: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2, PostgreSQL, Alembic
- **Frontend**: React 19, TypeScript, Vite, Tailwind, shadcn/ui, TanStack Query/Router/Table
- **MCP Server**: JSON-RPC endpoint with 12 read/write tools
- **REST API**: 50+ endpoints for CRUD on all entities
- **CLI**: Typer-based CLI with project, task, status commands
- **Git Integration**: Read-only local/GitHub/GitLab adapters
- **Reporting**: Daily reports with markdown export
- **Audit**: Full audit trail for all entity changes
- **Tests**: 189 backend tests, 140 frontend tests

### Current Domain Hierarchy

```
Project
├── Component → Module
├── Feature → Task → Subtask
│   ├── AcceptanceCriterion
│   └── DoDItem
├── GitProvider → GitBranch / GitCommit
└── AuditEvent / Report
```

### Current API Endpoints

50+ REST endpoints covering CRUD for all entities, plus:

- `GET /api/v1/dashboard/stats`
- `GET /api/v1/projects/{id}/quality/stats`
- `GET /api/v1/projects/{id}/reports`
- `POST /api/v1/projects/{id}/reports/daily`
- `GET /api/v1/search`
- `POST /api/v1/tasks/{id}/complete`
- Health, MCP, and Git endpoints

### Critical Gaps

| Gap | Severity | Impact |
|-----|----------|--------|
| No authentication | Critical | Anyone can access all data |
| No authorization/RBAC | Critical | No permission control |
| No agent management | Critical | Agents are not first-class subjects |
| Hardcoded secrets | Critical | Security risk |
| No rate limiting | High | Abuse possible |
| No Redis | High | No caching, locks, or queues |
| No structured logging | Medium | Poor observability |
| No evidence engine | Medium | Done is not provable |
| No review engine | Medium | No agent-assisted review |
| No agent workflow | High | No claim/heartbeat/clarification |
| CORS too open | Medium | Security risk |
| No security headers (partial) | Medium | XSS/clickjacking risk |

### What Works Well

- Full CRUD for project hierarchy
- Frontend with dashboard, project drill-down, delivery board, quality, audit, reports
- MCP read/write tools for AI agents
- Git read-only integration
- Audit trail
- Dark mode, pagination, search, command palette

## 2. Target Vision

### UPCP v2: Identity, Agent Workflow, Evidence, Observability and Human Control UX

> An owner and AI agents can daily work in UPCP: plan, design, execute tasks, attach evidence, pass review, get reports, and have full traceability.

### Key Capabilities

1. **Identity & Access**: Users, organizations, RBAC, agent tokens, permissions
2. **Agent Workflow**: Claims, heartbeats, progress, clarifications, inbox, playbook
3. **Evidence Engine**: Evidence model, verification states, DoD requirements
4. **Review Engine**: Review rounds, findings, agent review, human approval
5. **Observability**: Structured logs, metrics, traces, dashboards
6. **Human Control UX**: Attention dashboard, project drill-down, agent center, notifications

## 3. Milestones

### M7: Identity, Access & Agent Foundation

Full users, organizations, RBAC, agents, agent tokens and permissions.

**Components**: identity-access, agent-management

### M8: Runtime Foundation

Redis, secrets, rate limiting, structured logging, metrics, tracing, observability.

**Components**: runtime-platform, observability, secrets-config

### M9: Agent Workflow MVP

Agent can fully work with a task from claim to review.

**Components**: agent-workflow

### M10: Evidence & Review Engine

Done requires evidence, DoD coverage, and review.

**Components**: quality-evidence

### M11: Human Control UX, Project Drill-down & Portfolio Insights

Full command center with drill-down to any entity.

**Components**: frontend-ui, reporting-insights, notifications

## 4. Component Map

| Component | Modules | Milestone |
|-----------|---------|-----------|
| identity-access | organizations, users, memberships, authentication, sessions, rbac | M7 |
| agent-management | agent-profiles, agent-tokens, agent-scopes, agent-roles, agent-project-assignments, agent-audit | M7 |
| agent-workflow | task-claims, heartbeats, progress-updates, clarifications, agent-inbox, agent-playbook, stale-detection | M9 |
| delivery-management | projects, structure, features, tasks, subtasks, task-lifecycle, dependencies | M9 |
| quality-evidence | acceptance-criteria, dod, evidence, quality-gates, review-rounds, review-findings, review-policies | M10 |
| runtime-platform | redis, rate-limiting, idempotency, locks, background-jobs, health-checks | M8 |
| observability | structured-logging, metrics, tracing, correlation, redaction, dashboards | M8 |
| secrets-config | secret-providers, encrypted-fields, feature-flags, settings, startup-validation | M8 |
| mcp-api-cli | mcp-tools, rest-api, cli, agent-guide, error-codes, context-packs | M9 |
| frontend-ui | app-shell, auth-ui, project-drilldown, agent-center, attention-dashboard, task-detail, evidence-ui, review-ui, notifications-ui, reports-ui, settings-ui | M11 |
| reporting-insights | daily-reports, weekly-reports, project-health, agent-activity, attention-queue, llm-summary | M11 |
| git-integration | read-only-adapters, git-links, git-ui, ci-status-future | M11 |
| notifications | in-app-notifications, notification-preferences, event-dispatch, webhooks-future | M11 |

## 5. Assumptions

1. **Single-user initially**: First user becomes owner. Public registration disabled by default.
2. **PostgreSQL stays**: No database migration planned.
3. **Redis is required**: Will be added as mandatory dependency in docker-compose.
4. **No SaaS billing now**: Architecture is multi-org ready but no billing implementation.
5. **Git stays read-only**: No write access to project repos.
6. **Agent tokens are long-lived**: With manual revocation, not auto-rotation.
7. **Default review policy**: agent_review_then_human (agent reviews first, human approves).
8. **MCP is primary agent interface**: REST API mirrors MCP capabilities.
9. **Evidence is manual + git**: No automated CI ingestion in v2 (future webhook).
10. **No OIDC in v2**: Email/password only. OIDC as future option.
11. **Existing tasks preserved**: TASK-0062 Notifications integrated into new notifications component.
12. **English for code/identifiers**: Russian for documentation only.
13. **Description field as metadata carrier**: Current API lacks milestone/label fields — encode in structured markdown blocks within descriptions.

## 6. Open Questions

1. Should agent auto-close be opt-in per project or per organization?
2. What is the maximum number of concurrent agent claims per project?
3. Should evidence support file upload or only references/snippets?
4. How to handle agent token rotation for compromised tokens?
5. Should context packs be cached in Redis or regenerated each time?
6. What retention policy for audit events and heartbeats?
7. Should notifications support real-time WebSocket or polling only?

## 7. Documentation Plan

### Product Documents
- `docs/prd/upcp-v2.md` — Full PRD
- `docs/prd/agent-workflow.md` — Agent workflow spec
- `docs/prd/evidence-and-review.md` — Evidence & review spec
- `docs/prd/human-control-ux.md` — Human control UX spec

### Architecture Documents
- `docs/architecture/system-context.md`
- `docs/architecture/ddd-contexts.md`
- `docs/architecture/data-model.md`
- `docs/architecture/api-design.md`
- `docs/architecture/mcp-tools.md`
- `docs/architecture/agent-workflow-state-machine.md`
- `docs/architecture/review-engine.md`
- `docs/architecture/observability.md`
- `docs/architecture/secrets-management.md`
- `docs/architecture/rate-limiting.md`
- `docs/architecture/multi-org-readiness.md`

### ADRs (in `docs/decisions.md`)
- ADR-0015: Redis as required runtime dependency
- ADR-0016: Multi-org ready architecture
- ADR-0017: JWT access + rotating refresh tokens
- ADR-0018: Agent tokens as first-class credentials
- ADR-0019: RBAC with global/org/project scopes
- ADR-0020: Evidence-based Done
- ADR-0021: Agent-assisted review with human final authority
- ADR-0022: OpenTelemetry observability stack
- ADR-0023: Secret provider abstraction
- ADR-0024: Read-only Git stays default
- ADR-0025: Context pack versioning and tiers
- ADR-0026: Full project drill-down UX

### Security Documents
- `docs/security/auth-rbac.md`
- `docs/security/agent-permissions.md`
- `docs/security/secrets-handling.md`
- `docs/security/rate-limiting.md`
- `docs/security/audit-events.md`
- `docs/security/threat-model.md`
- `docs/security/secure-deployment.md`

### Agent Documents
- `docs/agent/agent-playbook.md`
- `docs/agent/agent-onboarding.md`
- `docs/agent/mcp-tools.md`
- `docs/agent/cli-commands.md`
- `docs/agent/error-codes.md`
- `docs/agent/context-packs.md`
- `docs/agent/review-agent.md`

### UX Documents
- `docs/ux/information-architecture.md`
- `docs/ux/attention-dashboard.md`
- `docs/ux/project-drilldown.md`
- `docs/ux/task-detail.md`
- `docs/ux/agent-center.md`
- `docs/ux/evidence-and-review-ui.md`
- `docs/ux/notifications.md`
- `docs/ux/design-system.md`

### Ops Documents
- `docs/ops/docker-compose.md`
- `docs/ops/observability-stack.md`
- `docs/ops/grafana-dashboards.md`
- `docs/ops/backup-restore.md`
- `docs/ops/troubleshooting.md`
- `docs/ops/runbook-rate-limiting.md`
- `docs/ops/runbook-stale-claims.md`

### Testing Documents
- `docs/testing/test-plan.md`
- `docs/testing/permission-matrix-tests.md`
- `docs/testing/mcp-contract-tests.md`
- `docs/testing/e2e-critical-flows.md`

## 8. Implementation Order

### Phase 1: Foundation (M7 + M8)

Priority: Critical/High

1. Authentication module (email/password, JWT)
2. User model + registration (disabled by default)
3. Organization model + default org bootstrap
4. RBAC (roles, permissions, bindings)
5. Agent model + agent tokens
6. Redis integration
7. Rate limiting
8. Secrets management
9. Structured logging
10. Security hardening

### Phase 2: Agent Workflow (M9)

Priority: High

1. Task claim/release lifecycle
2. Heartbeats + stale detection
3. Clarification model + flow
4. Agent inbox
5. Agent playbook
6. MCP workflow tools
7. CLI workflow commands

### Phase 3: Quality (M10)

Priority: High

1. Evidence model
2. DoD evidence requirements
3. Quality gate calculation
4. Review rounds + findings
5. Agent review capability
6. Human approval flow
7. Review policies

### Phase 4: UX (M11)

Priority: Medium

1. Attention dashboard
2. Full project drill-down
3. Task detail enhancement
4. Agent center
5. Evidence/review panels
6. Notifications
7. Reports enhancement

## 9. First Implementation Tasks

1. Add User model and migration
2. Add Organization model and migration
3. Add Membership model and migration
4. Implement JWT token service
5. Add auth middleware
6. Create POST /auth/setup (first-run)
7. Create POST /auth/login
8. Add Redis client to docker-compose and backend
9. Implement rate limiting middleware
10. Add Agent model and migration
11. Add AgentToken model and migration
12. Create POST /agents endpoint
13. Create POST /agents/{id}/tokens endpoint
14. Add RBAC role/permission models
15. Seed default roles and permissions
16. Add auth to all existing endpoints
17. Implement structured JSON logging
18. Add secret provider abstraction
19. Implement agent token authentication
20. Add CORS configuration
