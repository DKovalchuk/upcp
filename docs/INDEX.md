# Documentation Index

Read only what is needed for the current task.

| Doc | Purpose | Read when |
|---|---|---|
| `00-vision.md` | Product vision | Starting a new feature or milestone |
| `01-principles.md` | Engineering principles | Making trade-offs |
| `02-architecture.md` | System architecture | Creating modules or services |
| `03-domain-model.md` | Entities and relationships | Changing data model |
| `04-spec-flow.md` | Spec workflow | Creating specs/tasks |
| `05-ddd.md` | Domain boundaries | Adding contexts/modules |
| `06-tdd.md` | Testing workflow | Writing code |
| `07-token-economy.md` | Token-saving rules | Prompting agents |
| `08-coding-standards.md` | Code style and limits | Writing or reviewing code |
| `09-testing-standards.md` | Test structure | Writing tests |
| `10-git-conventions.md` | Branches/commits | Committing work |
| `11-docker-and-ports.md` | Docker ports | Running locally |
| `12-bootstrap-plan.md` | Milestones and first tasks | Planning implementation |
| `13-model-routing.md` | Light vs Pro model usage | Choosing model |
| `decisions.md` | Append-only decisions | Recording assumptions |

## UPCP v2 Planning (2026-07-27)

| Doc | Purpose |
|---|---|
| `planning/upcp-v2-kickoff.md` | Current state, target vision, milestones, assumptions |
| `planning/upcp-v2-planning-report.md` | Full planning report with domain model, state machines, API/MCP contracts |

### PRD

| Doc | Purpose |
|---|---|
| `prd/upcp-v2.md` | Full PRD for v2 |
| `prd/agent-workflow.md` | Agent workflow specification |
| `prd/evidence-and-review.md` | Evidence and review specification |
| `prd/human-control-ux.md` | Human control UX specification |

### Architecture

| Doc | Purpose |
|---|---|
| `architecture/system-context.md` | System context and actors |
| `architecture/ddd-contexts.md` | Bounded contexts |
| `architecture/data-model.md` | Target data model |
| `architecture/api-design.md` | API design principles |
| `architecture/mcp-tools.md` | MCP tool catalog |
| `architecture/agent-workflow-state-machine.md` | State machines |
| `architecture/review-engine.md` | Review engine design |
| `architecture/observability.md` | Observability stack |
| `architecture/secrets-management.md` | Secret provider abstraction |
| `architecture/rate-limiting.md` | Rate limiting design |
| `architecture/multi-org-readiness.md` | Multi-org architecture |

### Security

| Doc | Purpose |
|---|---|
| `security/auth-rbac.md` | Auth and RBAC specification |
| `security/agent-permissions.md` | Agent permission model |
| `security/secrets-handling.md` | Secret management rules |
| `security/rate-limiting.md` | Rate limiting specification |
| `security/audit-events.md` | Required audit events |
| `security/threat-model.md` | STRIDE threat model |
| `security/secure-deployment.md` | Deployment security checklist |

### Agent

| Doc | Purpose |
|---|---|
| `agent/agent-playbook.md` | Agent operating guide |
| `agent/agent-onboarding.md` | Agent onboarding |
| `agent/mcp-tools.md` | MCP tools reference |
| `agent/cli-commands.md` | CLI commands reference |
| `agent/error-codes.md` | Error code catalog |
| `agent/context-packs.md` | Context pack tiers |
| `agent/review-agent.md` | Agent reviewer guide |

### UX

| Doc | Purpose |
|---|---|
| `ux/information-architecture.md` | Navigation and IA |
| `ux/attention-dashboard.md` | Attention dashboard spec |
| `ux/project-drilldown.md` | Project drill-down UX |
| `ux/task-detail.md` | Task detail UX |
| `ux/agent-center.md` | Agent center UX |
| `ux/evidence-and-review-ui.md` | Evidence/review UI |
| `ux/notifications.md` | Notifications UX |
| `ux/design-system.md` | Design system reference |

### Ops

| Doc | Purpose |
|---|---|
| `ops/docker-compose.md` | Docker configuration |
| `ops/observability-stack.md` | Observability setup |
| `ops/grafana-dashboards.md` | Dashboard specifications |
| `ops/backup-restore.md` | Backup/restore procedures |
| `ops/troubleshooting.md` | Common issues |
| `ops/runbook-rate-limiting.md` | Rate limiting runbook |
| `ops/runbook-stale-claims.md` | Stale claims runbook |

### Testing

| Doc | Purpose |
|---|---|
| `testing/test-plan.md` | Test plan |
| `testing/permission-matrix-tests.md` | Permission matrix tests |
| `testing/mcp-contract-tests.md` | MCP contract tests |
| `testing/e2e-critical-flows.md` | E2E critical flows |
