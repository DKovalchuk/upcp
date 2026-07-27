# Bounded Contexts — UPCP v2

## Overview

UPCP is organized as a modular monolith with clear bounded context boundaries. Each context is an autonomous module with its own domain model, services, and ports. Contexts communicate through explicit interfaces (services, events, ACL).

---

## Context Map

```
┌─────────────────────────────────────────────────────────────────────┐
│                         API Gateway                                  │
│                   (FastAPI routes + MCP tools)                       │
└────────┬──────────┬──────────┬──────────┬──────────┬────────────────┘
         │          │          │          │          │
    ┌────▼───┐ ┌────▼───┐ ┌───▼────┐ ┌───▼────┐ ┌──▼──────┐
    │Identity│ │ Agent  │ │Delivery│ │Quality │ │Runtime  │
    │& Access│ │Mgmt    │ │Mgmt    │ │Evidence│ │Platform │
    └────┬───┘ └────┬───┘ └───┬────┘ └───┬────┘ └──┬──────┘
         │          │         │          │          │
    ┌────▼───┐ ┌────▼───┐ ┌───▼────┐ ┌───▼────┐ ┌──▼──────┐
    │Secrets │ │Agent   │ │Git     │ │Observ- │ │Report-  │
    │& Config│ │Workflow │ │Integr. │ │ability │ │ing      │
    └────────┘ └────────┘ └────────┘ └────────┘ └─────────┘
                                │
                           ┌────▼─────┐
                           │Notifica- │
                           │tions     │
                           └──────────┘
         ┌──────────────────────────────────┐
         │        Shared Kernel             │
         │  (base models, events, errors,   │
         │   pagination, idempotency)       │
         └──────────────────────────────────┘
```

---

## Context Descriptions

### 1. Identity & Access (`identity_access`)

**Purpose:** Authentication, authorization, user, role, and organization management.

**Key entities:**
- `Organization` — multi-tenant unit
- `User` — authenticated user
- `Membership` — User ↔ Organization link with role
- `Session` — active session (JWT)
- `Role`, `Permission`, `RoleBinding` — RBAC model

**Public interface:**
- `AuthService` — login, refresh, revoke
- `UserService` — user CRUD
- `OrgService` — organization management
- `RBACService` — permission checks

**ACL:** No inbound dependencies from other contexts.

---

### 2. Agent Management (`agent_management`)

**Purpose:** Managing AI agents, their tokens, scopes, and project assignments.

**Key entities:**
- `Agent` — registered agent (name, type, capabilities)
- `AgentToken` — authentication token (MCP)
- `AgentScope` — agent restrictions (projects, operations)
- `AgentProjectAssignment` — agent-to-project binding

**Public interface:**
- `AgentService` — agent CRUD
- `AgentTokenService` — token issuance/revocation
- `AgentScopeService` — scope management

**ACL:** → `identity_access` (owner verification)

---

### 3. Agent Workflow (`agent_workflow`)

**Purpose:** Task state machine, heartbeat, claim/release, clarification flow.

**Key entities:**
- `TaskClaim` — active claim on a task
- `Heartbeat` — periodic liveness signal
- `ClarificationRequest` — clarification request from an agent
- `Subtask` — subtask within a Task

**Public interface:**
- `TaskStateMachineService` — state transitions
- `ClaimService` — claim/release with atomicity
- `HeartbeatService` — heartbeat recording and validation
- `ClarificationService` — clarification flow management

**ACL:** → `delivery_management` (Task), → `agent_management` (Agent)

---

### 4. Delivery Management (`delivery_management`)

**Purpose:** Managing projects, components, modules, features, and tasks.

**Key entities:**
- `Project` — root work unit
- `Component` — structural unit of a project
- `Module` — module within a component
- `Feature` — business-level feature/task
- `Task` — specific work unit for an agent
- `AcceptanceCriterion` — acceptance criterion
- `DoDItem` — Definition of Done item

**Public interface:**
- `ProjectService` — project CRUD
- `ComponentService`, `ModuleService`, `FeatureService` — hierarchy CRUD
- `TaskService` — task CRUD, lifecycle management

**ACL:** → `identity_access` (membership check)

---

### 5. Quality & Evidence (`quality_evidence`)

**Purpose:** Managing evidence, review rounds, review findings, DoD verification.

**Key entities:**
- `Evidence` — proof artifact (type, URL, content)
- `ReviewRound` — review round
- `ReviewFinding` — review finding (severity, status)
- `ContextSnapshot` — agent context snapshot at time of execution

**Public interface:**
- `EvidenceService` — evidence CRUD
- `ReviewService` — review round management
- `ReviewPolicyService` — review policy enforcement

**ACL:** → `delivery_management` (Task, Feature), → `agent_management` (Agent)

---

### 6. Runtime Platform (`runtime_platform`)

**Purpose:** Infrastructure services — DB, cache, queues, rate limiting, health checks.

**Key components:**
- Database connection pool (asyncpg)
- Redis pool (redis-py async)
- Rate limiter (sliding window)
- Health check aggregation
- Background task scheduler

**Public interface:**
- `HealthService` — readiness/liveness
- `RateLimiter` — limit checking
- `CacheService` — cache operations

**ACL:** No domain dependencies.

---

### 7. Observability (`observability`)

**Purpose:** Collecting metrics, traces, logs, and audit events.

**Key entities:**
- `AuditEvent` — audit record (actor, action, entity, timestamp)

**Key components:**
- OpenTelemetry SDK integration
- Structured logging (structlog)
- Audit trail writer
- Prometheus metrics registry

**Public interface:**
- `AuditService` — audit event recording
- `MetricsService` — custom metrics

**ACL:** → all contexts (audit)

---

### 8. Secrets & Config (`secrets_config`)

**Purpose:** Managing secrets, configuration, and encrypted fields.

**Key components:**
- `SecretProvider` — secret reading abstraction
- `ConfigProvider` — configuration management
- `EncryptionService` — field encryption/decryption

**Public interface:**
- `SecretService` — secret retrieval
- `ConfigService` — configuration CRUD

**ACL:** No domain dependencies.

---

### 9. MCP, API & CLI (`mcp_api_cli`)

**Purpose:** Transport layer — MCP tools, REST endpoints, CLI commands. Orchestration of calls to domain services.

**Key components:**
- MCP tool handlers (read/write/admin)
- FastAPI route handlers
- CLI command handlers
- Request/response serialization
- Idempotency middleware

**Public interface:**
- MCP tools (see `mcp-tools.md`)
- REST endpoints (see `api-design.md`)

**ACL:** → all domain contexts (transport layer)

---

### 10. Frontend UI (`frontend_ui`)

**Purpose:** React 19 SPA — dashboards, project management, reviews, agents.

**Key components:**
- React 19 + TypeScript
- TanStack Router + Query
- Tailwind CSS + shadcn/ui
- WebSocket for real-time updates

**ACL:** → REST API (http client)

---

### 11. Reporting & Insights (`reporting_insights`)

**Purpose:** Report generation, analytics, data export.

**Key entities:**
- `Report` — generated report (type, period, format)

**Public interface:**
- `ReportService` — report generation
- `AnalyticsService` — data aggregation

**ACL:** → `delivery_management`, `quality_evidence`, `agent_workflow`

---

### 12. Git Integration (`git_integration`)

**Purpose:** Read-only integration with Git providers. Synchronizing commits, branches, MR/PR.

**Key entities:**
- `GitProvider` — connected provider (GitLab, GitHub)
- `GitBranch` — tracked branch
- `GitCommit` — synchronized commit
- `GitLink` — commit-to-task/feature link

**Public interface:**
- `GitSyncService` — provider synchronization
- `WebhookService` — webhook processing
- `GitLinkService` — link management

**ACL:** No internal dependencies (external API)

---

### 13. Notifications (`notifications`)

**Purpose:** Notifications for users and agents.

**Key entities:**
- `Notification` — notification (type, recipient, channel, status)

**Public interface:**
- `NotificationService` — notification creation and delivery
- `NotificationPreferenceService` — delivery settings

**ACL:** → `identity_access` (recipients), ← all contexts (event sources)

---

## Shared Kernel

Common components used by all contexts:

- `BaseModel` — base ORM model (id, created_at, updated_at)
- `PaginationParams`, `PaginatedResponse` — pagination
- `DomainEvent` — base domain event class
- `DomainError`, `NotFoundError`, `ConflictError` — errors
- `IdempotencyKey` — idempotency
- `UUID` — UUID generation and validation

---

## Interaction Rules

1. Contexts do NOT make direct SQL queries to each other's tables
2. Communication is through public services or domain events
3. ACL (Anti-Corruption Layer) translates models from one context into DTOs for another
4. Shared Kernel contains only primitives, no business logic
5. Changing a context's public interface requires updating all consumers
