# Documentation Status Reference

> Updated: 2026-08-08
> Purpose: Track which docs reflect reality vs aspirational plans

## Status Legend

| Status | Meaning |
|--------|---------|
| ✅ Implemented | Feature fully working in code |
| ⚠️ Partial | Some parts implemented, some not |
| 📋 Planned | Designed but not built |
| ❌ Aspirational | Future vision, no implementation |

## PRD Documents

| Doc | Status | Notes |
|-----|--------|-------|
| `prd/upcp-v2.md` | ✅ Implemented (M7–M14) | M15+ sections are planned |
| `prd/agent-workflow.md` | ✅ Implemented | Lifecycle synced to `lifecycle.py` |
| `prd/evidence-and-review.md` | ✅ Implemented | Severity synced to `quality/schemas.py` |
| `prd/human-control-ux.md` | ⚠️ Partial | Attention dashboard done, Agent Center not done |

## Architecture Documents

| Doc | Status | Notes |
|-----|--------|-------|
| `architecture/system-context.md` | ✅ Implemented | C4 diagram matches code |
| `architecture/ddd-contexts.md` | ✅ Implemented | 13 contexts match code |
| `architecture/data-model.md` | ✅ Implemented | Matches migrations |
| `architecture/api-design.md` | ✅ Implemented | Conventions followed |
| `architecture/mcp-tools.md` | ✅ Implemented | 20+ tools working |
| `architecture/agent-workflow-state-machine.md` | ✅ Implemented | States match `lifecycle.py` |
| `architecture/review-engine.md` | ✅ Implemented | Severity synced to 4 levels |
| `architecture/observability.md` | ⚠️ Partial | Logging only, no OTEL/metrics |
| `architecture/secrets-management.md` | ⚠️ Partial | Env/File providers only, no Vault |
| `architecture/rate-limiting.md` | ✅ Implemented | Sliding window working |
| `architecture/multi-org-readiness.md` | 📋 Planned | Single default org only |

## Security Documents

| Doc | Status | Notes |
|-----|--------|-------|
| `security/auth-rbac.md` | ✅ Implemented | JWT HS256 (not RS256 as previously stated) |
| `security/agent-permissions.md` | ⚠️ Partial | Agent tokens work, scopes limited |
| `security/secrets-handling.md` | ⚠️ Partial | Basic secret provider, no encryption at rest |
| `security/rate-limiting.md` | ✅ Implemented | Matches architecture doc |
| `security/audit-events.md` | ✅ Implemented | Audit trail working |
| `security/threat-model.md` | 📋 Planned | Document only |
| `security/secure-deployment.md` | 📋 Planned | Document only |

## Agent Documents

| Doc | Status | Notes |
|-----|--------|-------|
| `agent/agent-playbook.md` | ⚠️ Partial | API exists, playbook storage not implemented |
| `agent/agent-onboarding.md` | ⚠️ Partial | Token creation works, no onboarding flow |
| `agent/mcp-tools.md` | ✅ Implemented | Matches `mcp/tools.py` |
| `agent/cli-commands.md` | ✅ Implemented | Basic CLI working |
| `agent/error-codes.md` | 📋 Planned | Document only |
| `agent/context-packs.md` | ⚠️ Partial | Generator exists, tiers not configurable |
| `agent/review-agent.md` | 📋 Planned | Document only |

## UX Documents

| Doc | Status | Notes |
|-----|--------|-------|
| `ux/information-architecture.md` | ✅ Implemented | Nav matches router |
| `ux/attention-dashboard.md` | ✅ Implemented | 9 sections working |
| `ux/project-drilldown.md` | ✅ Implemented | Full drill-down working |
| `ux/task-detail.md` | ✅ Implemented | Sheet with tabs working |
| `ux/agent-center.md` | ❌ Aspirational | Not implemented |
| `ux/evidence-and-review-ui.md` | ❌ Aspirational | Types exist, no UI pages |
| `ux/notifications.md` | ⚠️ Partial | Bell + dropdown, no WebSocket |
| `ux/design-system.md` | ✅ Implemented | shadcn + custom components |

## Ops Documents

| Doc | Status | Notes |
|-----|--------|-------|
| `ops/docker-compose.md` | ✅ Implemented | Dev + test + stage configs |
| `ops/observability-stack.md` | ❌ Aspirational | Prometheus/Grafana behind profile |
| `ops/grafana-dashboards.md` | ❌ Aspirational | No dashboards defined |
| `ops/backup-restore.md` | ❌ Aspirational | No procedures |
| `ops/troubleshooting.md` | ⚠️ Partial | Basic health checks |
| `ops/runbook-rate-limiting.md` | 📋 Planned | Document only |
| `ops/runbook-stale-claims.md` | 📋 Planned | Document only |

## Testing Documents

| Doc | Status | Notes |
|-----|--------|-------|
| `testing/test-plan.md` | ⚠️ Partial | Unit tests good, E2E minimal |
| `testing/permission-matrix-tests.md` | ❌ Aspirational | Not implemented |
| `testing/mcp-contract-tests.md` | ❌ Aspirational | Not implemented |
| `testing/e2e-critical-flows.md` | ❌ Aspirational | 12 basic Playwright tests only |

## Core Docs

| Doc | Status | Notes |
|-----|--------|-------|
| `00-vision.md` | ✅ Current | Concise, accurate |
| `01-principles.md` | ✅ Current | 10 principles still valid |
| `02-architecture.md` | ✅ Updated | LLM clarification added |
| `03-domain-model.md` | ✅ Updated | Matches actual entities |
| `decisions.md` | ✅ Current | 26 ADRs, all still valid |
