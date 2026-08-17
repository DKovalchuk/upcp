# UPCP v2 — Product Requirements Document

> Version: 2.0 | Status: Implemented (M7–M14 complete) | Updated: 2026-08-08
> **Source of truth**: `PROJECT_STATUS.md` for current state, `backend/app/*/models.py` for actual data model

## 1. Product Vision

UPCP (Universal Project Control Plane) is a self-contained, local-first platform for collaborative work between humans and AI agents. The platform provides full control over the development process: from task assignment to evidence-based acceptance.

**Key principle:** every result is verifiable, every agent is accountable, every human is in control.

## 2. Target Audience

| Segment | Description |
|---------|-------------|
| Tech Lead | Manage development teams, control quality, distribute tasks |
| Solo Developer + AI | Single developer using multiple AI agents in parallel |
| DevOps Engineer | Observability, deployment, system health monitoring |
| AI Agent | Autonomous task executor via MCP/CLI/REST interfaces |

## 3. Key Capabilities

### 3.1 Identity

- Organizations → Projects → Tasks (hierarchy)
- Roles: `owner`, `admin`, `member`, `viewer`, `agent`
- API keys for agents (scoped, rotatable)
- JWT for users (access + refresh)
- RBAC matrix with enforcement at every endpoint

### 3.2 Agent Workflow

- Task lifecycle: `open → claimed → in_progress → in_review → done`
- Heartbeat every 30–60 seconds, stale detection after 7 minutes
- Agent inbox: incoming messages from humans and agents
- Clarification flow: agent requests clarification, task enters `blocked` status
- Playbook: working instructions for each project

### 3.3 Evidence

- Types: `test_result`, `log`, `screenshot`, `diff`, `metric`, `custom`
- Every piece of evidence is linked to a task and a DoD step
- DoD (Definition of Done): a set of requirements that must be fulfilled
- Evidence completeness: percentage of fulfilled DoD requirements

### 3.4 Review

- Automated quality gates (linters, tests, type checks)
- Agent or human reviewer
- Review rounds: multiple iterations until approval
- Findings: specific remarks linked to files/lines
- Auto-close: task is automatically closed upon full approval

### 3.5 Observability

- OpenTelemetry: traces, metrics, logs
- Prometheus + Grafana: dashboards and alerts
- Audit log: all actions recorded with timestamp, actor, target
- Attention dashboard: what requires your attention right now

### 3.6 Human Control UX

- Portfolio overview: all projects on a single screen
- Project drill-down: tasks, agents, health
- Agent center: active agents, their current tasks, metrics
- Notifications: real-time via WebSocket
- Command palette (Ctrl+K): quick access to actions

## 4. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Time to first task | < 5 min from launch | from `docker compose up` to first created task |
| Agent task cycle time | < 30 min (typical task) | from claim to done |
| Evidence completeness | > 90% of tasks with full evidence | % of tasks with completed DoD |
| Review turnaround | < 15 min (auto) / < 2 h (human) | time from in_review to done |
| System uptime | 99.5% for self-hosted | health check success rate |
| Stale task rate | < 5% of tasks | % of tasks without heartbeat > 7 min |

## 5. Milestones

### M7 — Foundation (current)
- Docker Compose configuration
- Database schema (Alembic migrations)
- Auth: registration, login, JWT, API keys
- Health check endpoint

### M8 — Identity & Projects
- CRUD for organizations, projects
- RBAC matrix
- Project members with roles
- Audit log (append-only)

### M9 — Agent Workflow
- Tasks: creation, assignment, lifecycle
- Agent claim/release/heartbeat
- Stale detection + auto-release
- Agent inbox + clarification
- Playbook per project

### M10 — Evidence & Review
- Evidence: upload, linking to tasks
- DoD templates
- Quality gates (lint, test, type check)
- Review workflow: round-based review
- Findings + resolution

### M11 — Observability & UX
- Attention dashboard
- Portfolio insights
- Agent center
- Notifications (WebSocket)
- Grafana dashboards
- Command palette

## 6. Scope and Non-Goals

### In Scope (v2)
- Self-hosted deployment via Docker Compose
- Local-first: works without internet
- Python/FastAPI backend, React frontend
- PostgreSQL + Redis
- MCP server for AI agent integration
- REST API for all operations
- CLI basic commands

### Out of Scope (v2)
- Cloud/SaaS version
- Multi-tenant isolation at the database level
- Real-time collaborative editing
- Built-in LLM (integration via API only)
- Mobile application
- Visual workflow builder
- Billing / invoicing
- SSO / SAML / OIDC

## 7. Technical Constraints

- Python 3.12+, FastAPI, SQLAlchemy 2
- PostgreSQL 16, Redis 7
- React 19, Vite, Tailwind CSS
- Docker Compose (single-node)
- Semantic Versioning (SemVer)
- OpenAPI 3.1 for all endpoints

## 8. References

- [Agent Workflow Spec](./agent-workflow.md)
- [Evidence & Review Spec](./evidence-and-review.md)
- [Human Control UX Spec](./human-control-ux.md)
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [PROJECT_STATUS.md](../../PROJECT_STATUS.md)
