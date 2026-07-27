# Decisions

Append-only.
Keep this file under 100 lines.
Archive old decisions when needed.

## Format

```text
YYYY-MM-DD | DEC-xxxx | decision | reason
```

## Decisions

2026-07-24 | DEC-0001 | Use Python FastAPI backend | Best balance for AI tooling, typing, MCP, and team preference
2026-07-24 | DEC-0002 | Use React rich frontend | Product requires rich functional UI
2026-07-24 | DEC-0003 | Use non-standard Docker ports | Standard ports are occupied on host
2026-07-24 | DEC-0004 | Use English machine docs | Better token efficiency and code-model performance
2026-07-24 | DEC-0005 | UPCP runtime is read-only for project Git repos | Safety and owner requirement
2026-07-24 | DEC-0006 | Task detail uses Sheet (slide-over), not a route | Task detail is transient context, not deep-linkable. Keeps user in flow on delivery page.
2026-07-24 | DEC-0007 | Dashboard is the project list, not a stats page | Single-user tool — project list IS the dashboard. Stats cards at top, projects below.
2026-07-24 | DEC-0008 | Project detail is tabbed layout, not nested routes | Tabs keep context visible (project name, status) while switching views. Avoids route explosion.
2026-07-24 | DEC-0009 | All forms use Dialog (create/edit), not separate pages | Faster workflow, no route changes, consistent pattern for all entities.
2026-07-24 | DEC-0010 | No auth in v1 — single-user self-hosted | Auth adds complexity with no value for single-user laptop deployment. Add when multi-user needed.
2026-07-24 | DEC-0011 | Sidebar project nav uses `:projectId` param from URL | Avoids prop drilling. Sidebar reads route params directly via TanStack Router.
2026-07-24 | DEC-0012 | Frontend types must match backend response schema exactly | Audit shows mismatches (feature_id missing, audit fields differ). Types are the API contract.
2026-07-24 | DEC-0013 | Priority is integer (0-3) not string (P0-P3) | Backend stores integer. Frontend maps to display labels/colors. Constants file handles mapping.
2026-07-24 | DEC-0014 | Use TanStack Table for all list views | Consistent sorting, filtering, pagination across all tables. Replaces ad-hoc table markup.
2026-07-27 | DEC-0015 | Redis as required runtime dependency | Rate limiting, idempotency, locks, heartbeats, session cache. Docker service mandatory.
2026-07-27 | DEC-0016 | Multi-org ready architecture | Organization model from day one. Default org for standalone. Feature flags for SaaS features.
2026-07-07 | DEC-0017 | JWT access tokens + rotating refresh tokens | Access: 15min. Refresh: 7d, stored in DB, rotated on use. Stateless validation for access tokens.
2026-07-27 | DEC-0018 | Agent tokens as first-class credentials | Hashed storage, shown once on creation, manual revocation, scope-based. X-Agent-Token header.
2026-07-27 | DEC-0019 | RBAC with global/org/project scopes | Owner > Admin > Member > Viewer for humans. Agent Reader/Contributor/Builder/Reviewer for agents.
2026-07-27 | DEC-0020 | Evidence-based Done | Task cannot be done without required evidence, DoD coverage, no blocking clarifications.
2026-07-27 | DEC-0021 | Agent-assisted review, human final authority by default | Agent can review and recommend. Human approves by default. Agent auto-close only if explicitly allowed.
2026-07-27 | DEC-0022 | OpenTelemetry + Prometheus + Grafana + Loki + Tempo | Standard observability stack. OTel Collector as router. Prometheus for metrics.
2026-07-27 | DEC-0023 | Secret provider abstraction | Env, File, Docker providers. Vault/KMS/cloud as future. Encrypted fields in DB. Never log/return secrets.
2026-07-27 | DEC-0024 | Read-only Git integration remains default | No push, no branch creation, no PR opening. Read-only by design.
2026-07-27 | DEC-0025 | Context pack versioning and tiers | Minimal/standard/deep/debug tiers. Versioned snapshots with content hash and token estimate.
2026-07-27 | DEC-0026 | Full project drill-down UX | Portfolio → Project → Component → Module → Feature → Task. Breadcrumbs, deep links, URL state.
