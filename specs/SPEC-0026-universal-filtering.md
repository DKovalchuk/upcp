# SPEC-0026 — Universal Filtering System

**Status:** DRAFT
**Created:** 2026-09-05

## 1. Problem

No server-side filtering on most list pages. Frontend ignores backend filter capabilities.

| Entity | Backend filters | Frontend UI |
|--------|----------------|-------------|
| Tasks | status, feature_id, assignee_type | client-side text only |
| Features | NONE | NONE |
| Components | NONE | NONE |
| Modules | NONE | NONE |
| Projects | status, search, sort | NONE (pagination only) |
| Agents | search, status (dead code) | search only |

## 2. Goals

1. Shared filter components: status dropdown, priority dropdown, search input
2. URL-synced filter state (bookmarkable, shareable)
3. Server-side filtering on all list endpoints
4. SavedViews extended to store full filter state
5. Consistent UX across all list pages

## 3. Scope

### S26.1: Backend — Add filters to delivery endpoints (TASK-0129)

**Features list** (`GET /projects/{id}/features`):
- `status` (string, optional) — backlog, in_progress, review, done
- `search` (string, optional) — ILIKE on name
- `sort_by` (string) — name, status, created_at
- `sort_dir` (string) — asc, desc

**Tasks by feature** (`GET /features/{id}/tasks`):
- `status` (string, optional)
- `priority` (int, optional) — min priority threshold
- `search` (string, optional) — ILIKE on title

### S26.2: Backend — Add filters to structure endpoints (TASK-0130)

**Components list** (`GET /projects/{id}/components`):
- `status` (string, optional)
- `search` (string, optional) — ILIKE on name

**Modules list** (`GET /components/{id}/modules`):
- `status` (string, optional)
- `search` (string, optional) — ILIKE on name

### S26.3: Frontend — Shared filter components (TASK-0131)

Create reusable components:
- `StatusFilter` — dropdown with status options, multi-select
- `PriorityFilter` — dropdown with priority levels
- `SearchFilter` — debounced text input
- `FilterBar` — container that composes filters + clear button
- `useFilters` hook — syncs filter state with URL params

### S26.4: Frontend — Wire filters to DeliveryPage (TASK-0132)

- Replace client-side search with server-side `search` param
- Add StatusFilter for task statuses
- Wire filters to `fetchProjectTasks(projectId, { status, search })`
- Update BoardView to use same filters
- Update SavedViews to store full filter state

### S26.5: Frontend — Wire filters to ProjectList (TASK-0133)

- Add SearchFilter
- Add StatusFilter (active/paused/archived)
- Wire to `fetchProjects({ status, search, sort_by, sort_dir })`

### S26.6: Frontend — Wire filters to StructurePage (TASK-0134)

- Add SearchFilter for components
- Wire to backend component/module filters

### S26.7: Fix AgentCenterPage status filter (TASK-0135)

- Fix dead code: apply `statusFilter` to filtered array
- Wire to backend if agent list endpoint supports it

## 4. API Changes

### Modified Endpoints

`GET /projects/{id}/features` — add query params:
```
?status=in_progress&search=auth&sort_by=name&sort_dir=asc
```

`GET /features/{id}/tasks` — add query params:
```
?status=backlog&priority=5&search=login
```

`GET /projects/{id}/components` — add query params:
```
?status=active&search=backend
```

`GET /components/{id}/modules` — add query params:
```
?status=active&search=auth
```

### URL Filter State

All filters synced to URL search params:
```
/projects/xxx/delivery?status=in_progress&search=login&priority=7
/projects?status=active&search=upcp&sort_by=name
/projects/xxx/structure?search=backend
```

## 5. Implementation Order

```
S26.1 (backend delivery filters) ──→ S26.3 (shared components) ──→ S26.4 (DeliveryPage)
                                 ──→ S26.2 (backend structure) ──→ S26.6 (StructurePage)
                                 ──→ S26.5 (ProjectList)
                                 ──→ S26.7 (AgentCenter fix)
```
