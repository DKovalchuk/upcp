# UPCP v2 Planning Report

Updated: 2026-07-27

## 1. Executive Summary

UPCP v2 — это следующая версия Universal Project Control Plane, которая превращает рабочий прототип в production-ready платформу для совместной работы людей и AI-агентов.

**Текущее состояние**: рабочий модулярный монолит с CRUD для иерархии проектов, MCP-сервером, REST API, CLI, фронтендом с dashboard/kanban/search, аудитом и отчётами. Без аутентификации, авторизации, агентного workflow, evidence engine и полной observability.

**Целевое состояние**: полноценная платформа с identity/access, RBAC, агентами как first-class субъектами, task lifecycle с claim/heartbeat/clarification, evidence-based Done, agent-assisted review, observability и attention-first UX.

**Объём документации**: 48 файлов (11 architecture, 7 security, 7 agent, 8 UX, 4 PRD, 7 ops, 4 testing).

**Объём заполнения UPCP**: 1 проект, 13 компонентов, 81 модуль, 26 фичей, ~50 задач с полными метаданными.

## 2. Assumptions

| # | Assumption | Rationale |
|---|-----------|-----------|
| 1 | Single-user initially. First user = owner | Standalone deployment |
| 2 | PostgreSQL stays as primary DB | No reason to change |
| 3 | Redis is required runtime dependency | Rate limiting, locks, cache |
| 4 | No SaaS billing in v2 | Architecture is multi-org ready |
| 5 | Git stays read-only | Safety by design |
| 6 | Agent tokens are long-lived with manual revocation | Simplicity |
| 7 | Default review: agent_review_then_human | Balance automation and control |
| 8 | MCP is primary agent interface | Already working |
| 9 | Evidence is manual + git references | No CI auto-ingestion in v2 |
| 10 | No OIDC in v2 | Email/password only |
| 11 | Description field encodes metadata | Current API lacks milestone/label fields |
| 12 | English for code/identifiers | Russian for docs only |
| 13 | Existing tasks preserved (TASK-0062 integrated) | No data loss |
| 14 | Agent auto-close is opt-in, not default | Safety |

## 3. Target Vision

> Владелец и AI-агенты ежедневно работают в UPCP: планируют, проектируют, выполняют задачи, прикладывают доказательства, проходят ревью, получают отчёты и имеют полную трассируемость.

### Ключевые сценарии

**Сценарий 1: Ежедневная работа**
1. Владелец логинится → видит Attention Dashboard
2. Открывает проект → drill-down до задачи
3. Видит heartbeat и progress агента
4. Отвечает на clarification
5. Агент прикрепляет evidence → отправляет на review
6. Владелец смотрит evidence → approve/reject

**Сценарий 2: Agent-assisted review**
1. Агент-исполнитель завершает задачу → submit review
2. Назначается agent reviewer
3. Agent reviewer проверяет DoD, evidence, git → verdict
4. Человек принимает финальное решение

**Сценарий 3: Multi-project control**
1. Dashboard показывает проекты с проблемами
2. Stale claims, open clarifications, failed gates
3. Drill-down: Portfolio → Project → Component → Module → Feature → Task
4. На каждом уровне: evidence, review, audit, git links

## 4. Milestones

### M7: Identity, Access & Agent Foundation
**Цель**: Полноценные пользователи, организации, RBAC, агенты, токены.
**Срок**: Phase 1
**Критичность**: Critical

### M8: Runtime Foundation
**Цель**: Redis, secrets, rate limiting, observability.
**Срок**: Phase 1 (параллельно с M7)
**Критичность**: Critical/High

### M9: Agent Workflow MVP
**Цель**: Агент может полноценно работать с задачей от claim до review.
**Срок**: Phase 2
**Критичность**: High

### M10: Evidence & Review Engine
**Цель**: Done требует evidence, DoD coverage и review.
**Срок**: Phase 2
**Критичность**: High

### M11: Human Control UX, Project Drill-down & Portfolio Insights
**Цель**: Удобный командный центр с полным drill-down.
**Срок**: Phase 3
**Критичность**: Medium

## 5. Component Map

```
┌─────────────────────────────────────────────────────────────┐
│                    UPCP v2 Component Map                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │ identity-access  │  │ agent-management│   M7             │
│  │ 6 modules       │  │ 6 modules       │                  │
│  └─────────────────┘  └─────────────────┘                  │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────┐ │
│  │ runtime-platform│  │  observability  │  │secrets-cfg │  │ M8
│  │ 6 modules       │  │ 6 modules       │  │5 modules   │  │
│  └─────────────────┘  └─────────────────┘  └────────────┘ │
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │ agent-workflow  │  │delivery-manage  │   M9             │
│  │ 7 modules       │  │ 7 modules       │                  │
│  └─────────────────┘  └─────────────────┘                  │
│                                                             │
│  ┌─────────────────┐                                        │
│  │quality-evidence │   M10                                  │
│  │ 7 modules       │                                        │
│  └─────────────────┘                                        │
│                                                             │
│  ┌──────────┐ ┌────────────┐ ┌──────────┐ ┌──────────────┐│
│  │frontend- │ │reporting-  │ │   git-   │ │notifications ││ M11
│  │ui        │ │insights    │ │integr.   │ │              ││
│  │11 modules│ │6 modules   │ │4 modules │ │4 modules    ││
│  └──────────┘ └────────────┘ └──────────┘ └──────────────┘│
│                                                             │
│  ┌─────────────────┐                                        │
│  │   mcp-api-cli   │   All milestones                      │
│  │ 6 modules       │                                        │
│  └─────────────────┘                                        │
└─────────────────────────────────────────────────────────────┘
```

## 6. Domain Model

### Target Entities

```text
Organization (id, name, slug, is_default)
├── User (id, email, password_hash, display_name, is_active, is_superuser)
│   └── Membership (user_id, org_id, role)
│       └── Session (id, user_id, refresh_token_hash, expires_at)
├── Role (id, name, scope: global|org|project)
│   └── Permission (id, action, resource)
│       └── RoleBinding (user_id, role_id, org_id?, project_id?)
├── Agent (id, name, description, is_active, created_by)
│   ├── AgentToken (id, agent_id, token_hash, name, scopes, expires_at, revoked_at, last_used_at)
│   ├── AgentScope (agent_id, permission)
│   └── AgentProjectAssignment (agent_id, project_id, role)
├── Project (id, name, slug, description, status, settings)
│   ├── Component (id, project_id, name, slug, status)
│   │   └── Module (id, component_id, name, slug, status)
│   ├── Feature (id, project_id, name, slug, status, component_id?)
│   │   └── Task (id, feature_id, title, description, status, priority, review_state,
│   │   │              assignee_type, assignee_id, component_id?, module_id?)
│   │   │   ├── TaskClaim (id, task_id, agent_id, state, claimed_at, released_at,
│   │   │   │                 expires_at, last_heartbeat_at, context_snapshot_id)
│   │   │   │   └── Heartbeat (claim_id, progress_percent, current_step, next_step, blockers, eta)
│   │   │   ├── Subtask (id, task_id, title, status)
│   │   │   ├── AcceptanceCriterion (id, task_id, description, status)
│   │   │   ├── DoDItem (id, task_id, description, required_evidence_type?, status)
│   │   │   ├── Evidence (id, task_id, dod_item_id?, type, title, url, content_snippet,
│   │   │   │                 created_by_type, created_by_id, verification_state, verified_by_type, verified_by_id)
│   │   │   ├── ClarificationRequest (id, task_id, author_type, author_id, question,
│   │   │   │                              blocking, state, answer, answered_by, answered_at)
│   │   │   ├── ReviewRound (id, task_id, requested_by_type, requested_by_id,
│   │   │   │                     reviewer_type, reviewer_id, state, verdict, confidence, summary)
│   │   │   │   └── ReviewFinding (id, review_round_id, severity, category, message, evidence_id?)
│   │   │   └── ContextSnapshot (id, task_id, tier, generated_for_agent_id, content_hash, token_estimate)
│   │   └── GitLink (id, task_id, git_type, git_id, url)
│   ├── GitProvider (id, project_id, type, url, auth_type)
│   │   ├── GitBranch (id, provider_id, name)
│   │   └── GitCommit (id, provider_id, sha, message, author, date)
│   ├── AuditEvent (id, project_id, actor_type, actor_id, action, entity_type, entity_id, changes)
│   └── Report (id, project_id, type, content, generated_at)
└── Notification (id, user_id, type, title, message, entity_type, entity_id, is_read, created_at)
```

### Key Relationships

- Organization 1:N User (via Membership)
- Organization 1:N Project
- Project 1:N Component 1:N Module
- Project 1:N Feature 1:N Task
- Task 1:1 TaskClaim
- Task 1:N Evidence
- Task 1:N ClarificationRequest
- Task 1:N ReviewRound 1:N ReviewFinding
- Agent 1:N AgentToken
- Agent N:M Project (via AgentProjectAssignment)

### Indexes

- User: email (unique), org_id
- AgentToken: token_hash (unique), agent_id
- TaskClaim: task_id (unique active), agent_id, state
- Evidence: task_id, verification_state
- ReviewRound: task_id, state
- AuditEvent: project_id, created_at, actor_type, entity_type
- Notification: user_id, is_read, created_at

## 7. State Machines

### Task Status

```
backlog ──→ ready ──→ claimed ──→ in_progress ──→ done
                │         │            │
                │         │            ├──→ blocked ──→ in_progress
                │         │            │
                │         │            ├──→ needs_clarification ──→ in_progress
                │         │            │
                │         │            └──→ ready_for_review ──→ done
                │         │                         │
                │         │                         └──→ changes_requested ──→ in_progress
                │         │
                │         └──→ backlog (claim expired/released)
                │
                └──→ cancelled
```

### Task Review State

```
none ──→ pending_review ──→ approved
              │
              └──→ rejected
              │
              └──→ changes_requested ──→ pending_review
```

### TaskClaim State

```
active ──→ released
    │
    ├──→ expired
    │
    └──→ completed
```

### ClarificationRequest State

```
open ──→ answered ──→ resolved
  │
  └──→ cancelled
```

### ReviewRound State

```
pending ──→ in_progress ──→ completed (with verdict)
    │
    └──→ cancelled
```

### Evidence Verification State

```
unverified ──→ agent_verified ──→ human_accepted
    │
    └──→ rejected
    │
    └──→ stale (source changed)
```

### AgentToken State

```
active ──→ revoked
    │
    └──→ expired (auto by expires_at)
```

## 8. API Contracts

### Auth API

```yaml
POST /auth/setup
  # First-run only. Creates owner + default org.
  Request: { email, password, display_name }
  Response: { user, access_token, refresh_token, organization }
  Errors: SETUP_ALREADY_COMPLETED

POST /auth/login
  Request: { email, password }
  Response: { user, access_token, refresh_token }
  Errors: INVALID_CREDENTIALS, ACCOUNT_DISABLED
  Rate: 5/min/IP

POST /auth/logout
  Headers: Authorization: Bearer <token>
  Response: { ok: true }
  Invalidates: refresh token

POST /auth/refresh
  Request: { refresh_token }
  Response: { access_token, refresh_token }
  Errors: TOKEN_EXPIRED, TOKEN_REVOKED

GET /auth/me
  Response: { user, organization, memberships, roles }

POST /auth/password/change
  Request: { current_password, new_password }
  Response: { ok: true }
  Errors: INVALID_CURRENT_PASSWORD
```

### Agent API

```yaml
GET /agents
  Response: { items: [Agent], total, offset, limit }
  Permission: admin+

POST /agents
  Request: { name, description }
  Response: Agent
  Permission: admin+

GET /agents/{id}
  Response: Agent (with tokens, scopes, assignments)

POST /agents/{id}/tokens
  Request: { name, scopes, expires_at }
  Response: { ...AgentToken, token: "plaintext-shown-once" }
  Permission: admin+

POST /agent-tokens/{id}/revoke
  Response: { ok: true }

GET /agent/me
  # Agent self-service. Auth via X-Agent-Token.
  Response: { agent, scopes, assignments, inbox_count }

GET /agent/inbox?since=<ISO timestamp>
  Response: { events: [AgentEvent] }

GET /agent/playbook
  Response: markdown (agent playbook content)
```

### Task Workflow API

```yaml
POST /tasks/{id}/claim
  Request: { context_snapshot? }
  Response: TaskClaim
  Errors: TASK_ALREADY_CLAIMED, TASK_NOT_READY, FORBIDDEN

POST /tasks/{id}/release
  Response: { ok: true }
  Errors: TASK_NOT_CLAIMED_BY_YOU

POST /tasks/{id}/heartbeat
  Request: { progress_percent, current_step, next_step, blockers?, eta? }
  Response: { ok: true }

POST /tasks/{id}/progress
  Request: { progress_percent, message? }
  Response: { ok: true }

POST /tasks/{id}/clarifications
  Request: { question, context?, blocking: bool }
  Response: ClarificationRequest

POST /clarifications/{id}/answer
  Request: { answer }
  Response: ClarificationRequest

POST /clarifications/{id}/resolve
  Response: ClarificationRequest

POST /tasks/{id}/submit-review
  Request: { reviewer_agent_id? }
  Response: ReviewRound
  Errors: EVIDENCE_REQUIRED, DOD_NOT_SATISFIED, CLARIFICATION_BLOCKING

POST /tasks/{id}/approve
  Request: { comment? }
  Response: Task
  Permission: human or agent (if auto-close allowed)

POST /tasks/{id}/reject
  Request: { reason }
  Response: Task
```

### Evidence API

```yaml
GET /tasks/{id}/evidence
  Response: { items: [Evidence] }

POST /tasks/{id}/evidence
  Request: { type, title, description?, url?, content_snippet?, artifact_ref?, dod_item_id? }
  Response: Evidence

POST /evidence/{id}/agent-verify
  Request: { notes? }
  Response: Evidence

POST /evidence/{id}/human-accept
  Response: Evidence

POST /evidence/{id}/reject
  Request: { reason }
  Response: Evidence
```

### Review API

```yaml
GET /tasks/{id}/review-rounds
  Response: { items: [ReviewRound] }

POST /tasks/{id}/review-rounds
  Request: { reviewer_type, reviewer_id }
  Response: ReviewRound

POST /review-rounds/{id}/start
  Response: ReviewRound

POST /review-rounds/{id}/findings
  Request: { severity, category, message, evidence_id?, dod_item_id?, suggestion? }
  Response: ReviewFinding

POST /review-rounds/{id}/verdict
  Request: { verdict: approve|reject|needs_changes, confidence: 0-100, summary }
  Response: ReviewRound
```

### Error Response Format

```json
{
  "error_code": "TASK_NOT_CLAIMABLE",
  "message": "Task cannot be claimed because it is already claimed by another agent.",
  "hint": "Release the current claim or choose another task.",
  "entity": "task",
  "entity_id": "TASK-0062",
  "details": {}
}
```

### Rate Limit Headers

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1690000000
Retry-After: 60  (only on 429)
```

## 9. MCP Tools

### Read Tools

| Tool | Description | Input | Output |
|------|-------------|-------|--------|
| `whoami` | Current agent identity | - | { agent, scopes, assignments } |
| `get_capabilities` | Available tools and permissions | - | { tools, permissions } |
| `get_agent_playbook` | Agent operating guide | - | { content: markdown } |
| `list_projects` | List accessible projects | { offset?, limit? } | { items, total } |
| `get_project` | Project detail | { project_id } | Project |
| `list_components` | Components in project | { project_id } | { items } |
| `list_modules` | Modules in component | { component_id } | { items } |
| `list_features` | Features in project | { project_id, status? } | { items } |
| `list_tasks` | Tasks with filters | { feature_id?, status?, priority? } | { items } |
| `get_task` | Full task detail | { task_id } | Task (with claims, evidence, reviews) |
| `get_context_pack` | Context for task | { task_id, tier? } | ContextSnapshot |
| `get_agent_inbox` | Agent events | { since? } | { events } |
| `list_evidence` | Evidence for task | { task_id } | { items } |
| `list_review_rounds` | Review rounds for task | { task_id } | { items } |

### Write Tools

| Tool | Description | Permissions |
|------|-------------|-------------|
| `create_component` | Create component | contributor+ |
| `update_component` | Update component | contributor+ |
| `create_module` | Create module | contributor+ |
| `update_module` | Update module | contributor+ |
| `create_feature` | Create feature | contributor+ |
| `update_feature` | Update feature | contributor+ |
| `create_task` | Create task | contributor+ |
| `update_task` | Update task | contributor+ |
| `create_subtask` | Create subtask | contributor+ |
| `claim_task` | Claim task for agent | agent authenticated |
| `release_task` | Release claim | claimant only |
| `heartbeat_task` | Send heartbeat | claimant only |
| `add_task_note` | Add note/comment | contributor+ |
| `request_clarification` | Ask question | contributor+ |
| `answer_clarification` | Answer question | project member+ |
| `attach_evidence` | Attach evidence | contributor+ |
| `submit_task_for_review` | Submit for review | claimant+ |
| `request_agent_review` | Assign agent reviewer | admin+ |
| `submit_review_verdict` | Submit review verdict | reviewer only |

### Admin Tools (not available to agents by default)

| Tool | Description |
|------|-------------|
| `create_agent` | Create agent profile |
| `revoke_agent_token` | Revoke agent token |
| `manage_roles` | Manage roles/permissions |
| `manage_project_members` | Manage project membership |
| `manage_settings` | Manage org/project settings |

### Idempotency

All write MCP tools support `idempotency_key` parameter. Server stores keys in Redis with 24h TTL. Duplicate requests return cached response.

## 10. UX Flows

### First-Run Setup

```
1. User opens UPCP in browser
2. No users exist → redirect to /setup
3. Form: email, password, display name
4. Submit → POST /auth/setup
5. Creates owner + default org
6. Redirect to dashboard
```

### Agent Token Creation

```
1. Admin navigates to Agents page
2. Clicks "Create Agent"
3. Form: name, description
4. Agent created → detail page
5. Clicks "Create Token"
6. Form: token name, scopes (checkboxes), expiration
7. Token created → MODAL shows plaintext token ONCE
8. User copies token → closes modal → token never shown again
```

### Task Claim by Agent

```
1. Agent authenticates via X-Agent-Token
2. Calls claim_task MCP tool
3. System checks: task ready? not claimed? agent has permission?
4. Creates TaskClaim (active), updates task status to claimed
5. Returns claim with context snapshot
6. Agent begins work, sends heartbeats every 30-60s
```

### Clarification Flow

```
1. Agent encounters ambiguity → calls request_clarification
2. Task status → needs_clarification (if blocking)
3. Notification sent to owner
4. Owner opens task → Clarifications tab
5. Reads question → types answer
6. Calls answer_clarification
7. Agent receives notification in inbox
8. Agent reads answer → continues work
```

### Evidence Attach and Review

```
1. Agent completes work
2. Attaches evidence (commit, test output, screenshot, etc.)
3. Quality gate checks: all required DoD met? evidence attached?
4. Agent calls submit_task_for_review
5. Task status → ready_for_review
6. Review round created (agent_review_then_human)
7. Agent reviewer checks evidence, creates findings, submits verdict
8. Owner sees task in "Needs your review" on Attention Dashboard
9. Reviews verdict and findings
10. Approves or rejects
```

### Attention Dashboard Drill-Down

```
Dashboard shows:
  "Needs your review (3)" → click → list of tasks in review
    → click task → task detail → Reviews tab → see verdict + findings
    → approve/reject

  "Open agent questions (2)" → click → list of open clarifications
    → click → task detail → Clarifications tab → answer

  "Stale claims (1)" → click → agent center with stale highlight
    → click claim → release or extend
```

## 11. Security Model

### Authentication

- JWT access tokens (15min, stateless)
- Rotating refresh tokens (7d, DB-stored)
- Agent tokens (long-lived, hashed, manual revocation)
- First-run setup creates owner
- Public registration disabled by default

### Authorization (RBAC)

| Scope | Roles | Description |
|-------|-------|-------------|
| Global | Owner | Full system control |
| Organization | Admin, Member, Viewer | Org-level access |
| Project | Project Admin, Contributor, Viewer | Project-level |

| Agent Role | Can | Cannot |
|-----------|-----|--------|
| Agent Reader | Read all | Write anything |
| Agent Contributor | Read + write tasks | Delete, manage |
| Agent Builder | Read + write + claim | Delete projects, manage users |
| Agent Reviewer | Review + verdict | Approve (unless auto-close) |

### Secrets

- SecretProvider abstraction (env/file/docker/vault future)
- Encrypted fields in DB (integration secrets)
- Never returned via API (masked `***`)
- Never logged (redaction filter)
- Audit secret changes without values

### Security Hardening

- CORS: explicit origins only
- Security headers: CSP, X-Frame-Options, Referrer-Policy, Permissions-Policy
- Sort whitelist per entity (prevents SQL injection)
- Git adapter: shlex.quote, pattern validation (prevents command injection)
- Rate limiting: per IP/user/agent/token/route class
- Input validation: Pydantic v2 on all inputs

## 12. Observability Model

### Stack

```
Application → OpenTelemetry Collector → Prometheus (metrics)
                                      → Loki (logs)
                                      → Tempo (traces)
                                      → Grafana (dashboards)
```

### Structured Logs

```json
{
  "timestamp": "2026-07-27T10:00:00Z",
  "level": "info",
  "logger": "upcp.api",
  "message": "Task claimed",
  "request_id": "req-abc123",
  "trace_id": "trace-xyz789",
  "org_id": "org-001",
  "agent_id": "agent-001",
  "project_id": "proj-001",
  "task_id": "task-0062",
  "entity_type": "task",
  "action": "claim"
}
```

### Key Metrics

| Metric | Type | Labels |
|--------|------|--------|
| `http_requests_total` | counter | method, path, status |
| `http_request_duration_seconds` | histogram | method, path |
| `db_query_duration_seconds` | histogram | query_type |
| `redis_command_duration_seconds` | histogram | command |
| `upcp_tasks_claimed_total` | counter | project_id |
| `upcp_tasks_completed_total` | counter | project_id |
| `upcp_evidence_attached_total` | counter | type |
| `upcp_review_rounds_total` | counter | verdict |
| `upcp_clarifications_open` | gauge | project_id |
| `upcp_agent_heartbeat_age_seconds` | gauge | agent_id, task_id |

### Dashboards

1. **Service Health**: Request rate, latency p50/p95/p99, error rate, active requests, DB pool, Redis
2. **Auth & Security**: Login attempts, failed logins, rate limit hits, token creation/revocation
3. **Agent Activity**: Active claims, heartbeat age, stale claims, clarifications, evidence attached
4. **Delivery & Quality**: Tasks by status, completion rate, evidence completeness, review turnaround

## 13. Evidence and Review Model

### Evidence Types

| Type | MVP | Description |
|------|-----|-------------|
| commit | Yes | Git commit SHA with URL |
| test_output | Yes | Test run output/logs |
| manual_verification | Yes | Human verified manually |
| screenshot | Yes | Image reference |
| doc_update | Yes | Documentation change |
| note | Yes | Free-form text note |
| review_note | Yes | Reviewer's notes |
| branch | No | Git branch reference |
| pull_request | No | PR link |
| pipeline | No | CI pipeline run |
| coverage_report | No | Coverage output |
| log_snippet | No | Log excerpt |
| security_scan | No | Security scan result |
| performance_note | No | Performance observation |

### Verification States

```
unverified → agent_verified → human_accepted
           → rejected
           → stale (when source evidence changes)
```

### Quality Gate Rules

Task can be done ONLY when:
1. All required DoD items are completed
2. All required evidence types are attached
3. No unresolved blocking clarifications
4. Review policy is satisfied
5. Human approval exists (or agent auto-close is allowed)

### Review Policies

| Policy | Behavior |
|--------|----------|
| `human_only` | Only humans can review and approve |
| `agent_review_then_human` | Agent reviews first, human makes final decision |
| `agent_auto_close_if_allowed` | Agent can close if all conditions met |

### Auto-Close Conditions

```
project.settings.allow_agent_auto_close = true
AND review_policy = agent_auto_close_if_allowed
AND all required DoD satisfied
AND all required evidence attached
AND no unresolved blocking clarifications
AND executor != reviewer (or self_review explicitly allowed)
```

## 14. Migration Plan

### Phase 1: Database Migrations

1. Add User, Organization, Membership, Session models
2. Add Role, Permission, RoleBinding models
3. Add Agent, AgentToken, AgentScope models
4. Add TaskClaim, Heartbeat models
5. Add ClarificationRequest model
6. Add Evidence model
7. Add ReviewRound, ReviewFinding models
8. Add ContextSnapshot model
9. Add Notification model
10. Extend Task model (review_state, claim fields)
11. Seed default roles and permissions
12. Create default organization
13. Backfill existing tasks with default review_state = 'none'

### Phase 2: Feature Flags

```python
FEATURES = {
    "public_registration": False,
    "email_verification": False,
    "oidc_auth": False,
    "agent_auto_close": False,
    "multi_org": False,
    "webhooks": False,
}
```

### Phase 3: Rollout Stages

1. **Stage 1**: Auth + RBAC (existing endpoints get auth, no behavior change for existing)
2. **Stage 2**: Agent management (create agents, tokens)
3. **Stage 3**: Agent workflow (claims, heartbeats, clarifications)
4. **Stage 4**: Evidence + review (new functionality, optional initially)
5. **Stage 5**: UX updates (attention dashboard, drill-down, notifications)

### Backward Compatibility

- All existing API endpoints continue to work with auth header
- First setup: first user gets owner role automatically
- Existing data preserved: tasks, features, components, audit events
- TASK-0062 Notifications integrated into new notifications component
- Frontend gracefully handles missing auth (redirect to setup or login)

## 15. Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Auth breaks existing integrations | High | Feature flag, graceful fallback |
| Redis dependency increases ops complexity | Medium | Docker compose, clear docs |
| Agent workflow complexity | Medium | MVP scope, iterate |
| Migration data loss | High | Test migrations, backup before |
| Performance regression from auth middleware | Low | JWT is stateless, minimal overhead |
| Agent token compromise | Medium | Revocation, audit, scope limits |
| Review engine too complex | Medium | Start with simple policy, iterate |

## 16. Open Questions

1. Should agent auto-close be opt-in per project or per organization?
2. Maximum concurrent agent claims per project?
3. Evidence: file upload or references/snippets only?
4. Token rotation for compromised tokens vs simple revocation?
5. Context pack caching in Redis vs regeneration?
6. Audit/heartbeat retention policy?
7. Real-time notifications: WebSocket or polling?

**Defaults chosen**:
1. Per-project opt-in (more granular control)
2. One active claim per agent per project (prevent hoarding)
3. References/snippets only in v2 (file upload is future)
4. Simple revocation (no rotation for compromised tokens)
5. Regenerate each time in v2 (cache in future)
6. 90-day retention for heartbeats, indefinite for audit
7. Polling in v2, WebSocket in future

## 17. UPCP Population Summary

| Entity | Count |
|--------|-------|
| Projects | 1 (UPCP v2) |
| Components | 13 |
| Modules | 81 |
| Features | 26 |
| Tasks | ~50 |
| Milestones (encoded) | 5 (M7–M11 in task metadata) |

### Components Created

| Component | Modules | Features |
|-----------|---------|----------|
| identity-access | 6 | 2 |
| agent-management | 6 | 2 |
| agent-workflow | 7 | 4 |
| delivery-management | 7 | 1 |
| quality-evidence | 7 | 4 |
| runtime-platform | 6 | 2 |
| observability | 6 | 2 |
| secrets-config | 5 | 1 |
| mcp-api-cli | 6 | 1 |
| frontend-ui | 11 | 4 |
| reporting-insights | 6 | 1 |
| git-integration | 4 | 0 |
| notifications | 4 | 2 |

### Existing Tasks Preserved

TASK-0062 Notifications integrated into new `notifications` component as feature "Notifications system".

## 18. Next Implementation Tasks

Рекомендуемый порядок реализации (первые 20 задач):

| # | Task | Milestone | Priority | Size |
|---|------|-----------|----------|------|
| 1 | Add User model and migration | M7 | Critical | M |
| 2 | Add Organization model and migration | M7 | Critical | M |
| 3 | Add Membership model and migration | M7 | Critical | M |
| 4 | Add Redis to docker-compose and backend | M8 | Critical | M |
| 5 | Implement SecretProvider abstraction | M8 | Critical | M |
| 6 | Implement JWT token service | M7 | Critical | L |
| 7 | Implement auth middleware | M7 | Critical | M |
| 8 | Create POST /auth/setup endpoint | M7 | Critical | M |
| 9 | Create POST /auth/login endpoint | M7 | Critical | M |
| 10 | Add Role and Permission models | M7 | Critical | M |
| 11 | Add RoleBinding model | M7 | Critical | M |
| 12 | Implement permission check service | M7 | Critical | M |
| 13 | Add auth to all existing endpoints | M7 | Critical | L |
| 14 | Add Agent model and migration | M7 | High | M |
| 15 | Add AgentToken model and migration | M7 | High | M |
| 16 | Implement agent token authentication | M7 | High | M |
| 17 | Configure CORS properly | M8 | High | S |
| 18 | Harden Git adapter against command injection | M8 | Critical | M |
| 19 | Implement sliding window rate limiter | M8 | High | L |
| 20 | Implement structured JSON logging | M8 | High | M |

### Критический путь

```
User/Org/Membership models
  → JWT service
  → Auth middleware
  → Auth endpoints (setup/login)
  → RBAC models + seed
  → Permission check service
  → Apply auth to all endpoints
  → Agent model + tokens
  → Agent authentication
  → Redis integration
  → Rate limiting
  → Security hardening
```

После этого — M9 Agent Workflow, M10 Evidence & Review, M11 UX.

---

## Documentation Index

| Category | Files | Path |
|----------|-------|------|
| Kickoff | 1 | `docs/planning/upcp-v2-kickoff.md` |
| PRD | 4 | `docs/prd/` |
| Architecture | 11 | `docs/architecture/` |
| ADRs | 12 new | `docs/decisions.md` |
| Security | 7 | `docs/security/` |
| Agent | 7 | `docs/agent/` |
| UX | 8 | `docs/ux/` |
| Ops | 7 | `docs/ops/` |
| Testing | 4 | `docs/testing/` |
| **Total** | **~61** | |
