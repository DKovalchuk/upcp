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
