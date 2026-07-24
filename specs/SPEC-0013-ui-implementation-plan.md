# SPEC-0013: UI Implementation Plan

**Status**: Draft
**Date**: 2026-07-24
**Depends on**: SPEC-0012 (Frontend UI/UX Architecture)
**Supersedes**: SPEC-0012 Phase 2-4 task assignments

---

## 1. Current State Analysis

### 1.1 What Exists (Frontend)

| Component | Status | Quality | Notes |
|---|---|---|---|
| AppShell + Sidebar + TopBar | Done | Good | Structure matches SPEC-0012 |
| BreadcrumbBar | Done | Fair | Shows raw path segments, not entity names |
| Design system components | Done | Good | StatusBadge, PriorityDot, EmptyState, ErrorState, PageHeader, SearchInput, ConfirmDialog |
| Type definitions | Done | Fair | Mismatches with backend (see §1.3) |
| API client (api.ts) | Done | Good | Full CRUD for all entities |
| TanStack Query hooks | Done | Good | All entities covered |
| ProjectList page | Done | Fair | Basic table, no search/filter/sort, spinner not skeleton |
| 404 page | Done | Good | — |
| ErrorBoundary | Done | Good | — |
| Dark mode CSS | Done | Good | CSS vars ready, no toggle UI |

### 1.2 What's Missing (Frontend — All Pages)

| Page | Route | Status | Backend Ready? |
|---|---|---|---|
| Dashboard | `/` | Shows ProjectList instead of dashboard | Yes (`/dashboard/stats`) |
| Project Detail | `/projects/:id` | Not implemented | Yes |
| Structure | `/projects/:id/structure` | Not implemented | Yes |
| Delivery | `/projects/:id/delivery` | Not implemented | Yes |
| Quality | `/projects/:id/quality` | Not implemented | Yes (`/quality/stats`) |
| Audit | `/projects/:id/audit` | Not implemented | Yes (`/audit-events`) |
| Reports | `/reports` | Not implemented | Partial (per-project only) |
| Health | `/health` | Not implemented | Partial (basic only) |
| Project Settings | `/projects/:id/settings` | Not implemented | N/A |

### 1.3 Type Mismatches (Critical)

| Type | Field | Frontend | Backend | Fix |
|---|---|---|---|---|
| Task | `feature_id` | Missing | Returns it | Add field |
| Task | `priority` | `number` | `int` (0-3) | OK, but constants use string keys P0-P3 |
| AuditEvent | `timestamp` | Missing | Returns `timestamp` | Add field |
| AuditEvent | `actor_type` | Missing | Returns `actor_type` | Add field |
| AuditEvent | `actor_id` | `user_id` | `actor_id` | Rename |
| AuditEvent | `details` | `details` | `payload` | Rename |
| AuditEvent | `note` | Missing | Returns `note` | Add field |
| Feature | `project_id` | Missing | Returns it | Add field |
| Subtask | `task_id` | Missing | Returns it | Add field |

### 1.4 Sidebar Issues

| Issue | Details |
|---|---|
| Project nav paths empty | All `PROJECT_NAV_GROUP.items` have `path: ''` except Overview |
| No dynamic projectId | Project nav items don't include `:projectId` in paths |
| Wrong nav items | Has "Tasks", "Features", "Docs" — should be "Structure", "Delivery", "Quality", "Audit", "Settings" per SPEC-0012 |

### 1.5 UX Issues

| Issue | Details |
|---|---|
| Loading spinner | ProjectList uses `<div className="animate-spin">` — should use Skeleton per SPEC |
| No create dialog | "New Project" button has no onClick handler |
| No delete confirmation | No delete flow for any entity |
| No toast notifications | `sonner` installed but never used |
| No pagination UI | Backend returns paginated data, frontend ignores pagination |
| Empty paths in nav | Project sidebar items have empty paths — clicking does nothing |

---

## 2. Implementation Phases

### Phase 0: Foundation Fixes (M6a)
Fix broken foundations before building new pages.

### Phase 1: Core Pages (M6b)
Dashboard + Project Detail + Structure + Delivery pages.

### Phase 2: Quality + Audit + Reports (M6c)
Quality page, Audit timeline, Reports list.

### Phase 3: Polish (M6d)
Dark mode toggle, command palette, board view, global search.

---

## 3. Detailed Task Specifications

---

### TASK-0043: Fix Type Mismatches + Sidebar Navigation

**Goal**: Fix all type mismatches between frontend and backend. Fix sidebar navigation.

**Scope**:
1. Update `frontend/src/types/task.ts` — add `feature_id: string`
2. Update `frontend/src/types/feature.ts` — add `project_id: string`
3. Update `frontend/src/types/subtask.ts` — add `task_id: string`
4. Update `frontend/src/types/audit.ts` — rename `user_id` → `actor_id`, `details` → `payload`, add `timestamp`, `actor_type`, `note`
5. Update `frontend/src/types/api.ts` — add `DashboardStatsResponse`, `QualityStatsResponse`, `AuditEventSummary`, `ProjectSummary`, `TaskCountsByStatus`
6. Update `frontend/src/lib/constants.ts`:
   - Fix `PROJECT_NAV_GROUP` items: Overview, Structure, Delivery, Quality, Audit, Settings
   - Fix paths to use relative segments: `''`, `'structure'`, `'delivery'`, `'quality'`, `'audit'`, `'settings'`
   - Fix icons to match SPEC-0012: Boxes, GitBranch, ShieldCheck, ScrollText, Settings
   - Change priority keys from P0-P3 to 0-3 (integers)
7. Update `frontend/src/components/layouts/AppSidebar.tsx` — use `useParams` to get projectId
8. Update `frontend/src/lib/api.ts` — add `fetchDashboardStats()`, `fetchQualityStats(projectId)`
9. Update `frontend/src/hooks/` — add `use-dashboard.ts`, update `use-audit.ts` for project-scoped endpoint

**Acceptance Criteria**:
- [ ] All types match backend response schemas exactly
- [ ] Sidebar shows correct nav items with working links
- [ ] Priority display works with integer keys
- [ ] API client has functions for dashboard and quality stats
- [ ] `npm run build` passes with no TypeScript errors

**Estimated effort**: 1-2 hours

---

### TASK-0044: Skeleton Loading + Toast System

**Goal**: Replace spinners with skeleton screens. Wire up sonner toast system.

**Scope**:
1. Create `frontend/src/components/ui/PageSkeleton.tsx` — configurable skeleton for any page layout
2. Update `frontend/src/components/ProjectList.tsx` — replace spinner with skeleton
3. Add `<Toaster />` from sonner to `AppShell.tsx`
4. Create toast utility `frontend/src/lib/toast.ts` with helpers: `toast.success()`, `toast.error()`, `toast.created()`, `toast.updated()`, `toast.deleted()`
5. Toast message pattern: `{action} {entity} successfully` e.g. "Project created successfully"

**Acceptance Criteria**:
- [ ] All loading states use skeleton screens matching page layout
- [ ] Toast appears on create/update/delete operations
- [ ] Toast position: bottom-right
- [ ] Toast auto-dismiss: 3 seconds for success, 5 seconds for error
- [ ] `npm run build` passes

**Estimated effort**: 1 hour

---

### TASK-0045: Dashboard Page

**Goal**: Implement the Dashboard page with stats cards and recent projects.

**Scope**:
1. Create `frontend/src/components/Dashboard.tsx`
2. Use `useDashboardStats()` hook to fetch `/api/v1/dashboard/stats`
3. Layout per SPEC-0012 §4.1:
   - Stats row: 4 cards (Total Projects, Tasks by Status breakdown, Recent Activity count, Health indicator)
   - Below: Recent Projects table (name, status, updated_at) + Activity Feed sidebar
4. Stats cards use `Card` component with icon + number + label
5. Recent Projects links to project detail
6. Activity Feed shows last 10 audit events with timestamp + event_type + entity_type
7. Loading: skeleton matching layout
8. Empty: EmptyState with "Create your first project" CTA
9. Error: ErrorState with retry
10. Update router: `/` route renders Dashboard, `/projects` renders ProjectList

**Acceptance Criteria**:
- [ ] Dashboard shows 4 stat cards with real data from API
- [ ] Recent Projects table shows last 5 projects with links
- [ ] Activity feed shows last 10 events
- [ ] Loading/empty/error states handled
- [ ] Click on project name navigates to project detail
- [ ] `npm run build` passes

**Estimated effort**: 2-3 hours

---

### TASK-0046: Project Detail Page (Tabbed Layout)

**Goal**: Create the project detail page with tabbed navigation.

**Scope**:
1. Create `frontend/src/components/ProjectDetail.tsx` — main container
2. Create `frontend/src/components/project/ProjectOverview.tsx` — overview tab
3. Create `frontend/src/components/project/ProjectTabs.tsx` — tab navigation
4. Use shadcn `Tabs` component
5. Route: `/projects/$projectId` with tab as search param `?tab=overview|structure|delivery|quality|audit|settings`
6. Page header: Project name + status badge + description
7. Tabs: Overview, Structure, Delivery, Quality, Audit, Settings
8. Overview tab content:
   - Project info card (name, slug, description, status, created/updated)
   - Quick stats: component count, feature count, task count by status
   - Recent activity (last 5 audit events for this project)
9. Edit project via Dialog (reuse form from create)
10. Delete project with ConfirmDialog → navigate to `/projects`

**Acceptance Criteria**:
- [ ] `/projects/:id` renders project detail with header + tabs
- [ ] Tab navigation works with URL sync
- [ ] Overview shows project info + stats
- [ ] Edit project dialog works
- [ ] Delete project with confirmation → redirects to project list
- [ ] BreadcrumbBar shows: Home > Projects > {project.name}
- [ ] `npm run build` passes

**Estimated effort**: 3-4 hours

---

### TASK-0047: Create/Edit Form Dialogs (All Entities)

**Goal**: Implement reusable form dialogs for creating and editing all entities.

**Scope**:
1. Create `frontend/src/components/forms/ProjectForm.tsx`
2. Create `frontend/src/components/forms/ComponentForm.tsx`
3. Create `frontend/src/components/forms/ModuleForm.tsx`
4. Create `frontend/src/components/forms/FeatureForm.tsx`
5. Create `frontend/src/components/forms/TaskForm.tsx`
6. Create `frontend/src/components/forms/SubtaskForm.tsx`
7. Each form:
   - Uses shadcn `Dialog` component
   - Fields match backend schema
   - Auto-generates slug from name (client-side)
   - Validates required fields
   - Shows loading state on submit
   - Calls mutation hook on success
   - Toast notification on success/error
8. Pattern: parent component controls `open` state, passes `onSuccess` callback

**Acceptance Criteria**:
- [ ] Every entity has a create and edit form dialog
- [ ] Slug auto-generated from name (editable)
- [ ] Required field validation works
- [ ] Submit calls correct API endpoint
- [ ] Toast on success/error
- [ ] Dialog closes on success
- [ ] Parent list/detail refreshes after mutation
- [ ] `npm run build` passes

**Estimated effort**: 4-5 hours

---

### TASK-0048: Structure Page (Components + Modules)

**Goal**: Implement the Structure page showing components with expandable modules.

**Scope**:
1. Create `frontend/src/components/project/StructurePage.tsx`
2. Layout: Card grid for components
3. Each component card:
   - Name, slug, status badge, description
   - Module count
   - Click to expand → shows modules table inline
   - Edit/delete actions via dropdown menu
4. Modules table inside expanded card:
   - Columns: Name, Slug, Status, Actions
   - Create module button
   - Edit/delete module
5. Create component via `ComponentForm` dialog
6. Create module via `ModuleForm` dialog
7. Use `useComponents(projectId)` and `useModules(componentId)` hooks
8. Loading: skeleton cards
9. Empty: EmptyState "No components yet" with create CTA

**Acceptance Criteria**:
- [ ] Components displayed as cards
- [ ] Click card expands to show modules table
- [ ] Create/edit/delete component works
- [ ] Create/edit/delete module works
- [ ] Toast notifications on all mutations
- [ ] Loading/empty states handled
- [ ] `npm run build` passes

**Estimated effort**: 3-4 hours

---

### TASK-0049: Delivery Page (Features + Tasks)

**Goal**: Implement the Delivery page with features and tasks.

**Scope**:
1. Create `frontend/src/components/project/DeliveryPage.tsx`
2. Create `frontend/src/components/project/FeatureSection.tsx`
3. Create `frontend/src/components/project/TaskTable.tsx`
4. Layout: Feature groups, each with task table
5. Toolbar: Search input, status filter dropdown, + Feature button
6. Feature section:
   - Feature name + status badge + task count
   - Expandable task table
   - Edit/delete feature via dropdown
7. Task table columns: Priority dot, Title, Status badge, Assignee, Component, Updated, Actions
8. Task row click → opens Task Detail Sheet (slide-over)
9. Create task inline via TaskForm dialog
10. Subtask list inside Task Detail Sheet

**Acceptance Criteria**:
- [ ] Features listed with expandable task tables
- [ ] Task table shows all columns
- [ ] Click task row opens slide-over detail
- [ ] Create/edit/delete feature works
- [ ] Create/edit/delete task works
- [ ] Search filters tasks by title
- [ ] Status filter works
- [ ] `npm run build` passes

**Estimated effort**: 4-5 hours

---

### TASK-0050: Task Detail Sheet (Slide-Over)

**Goal**: Implement the task detail slide-over panel.

**Scope**:
1. Create `frontend/src/components/project/TaskDetailSheet.tsx`
2. Uses shadcn `Sheet` component (right side)
3. Content:
   - Header: Task title + status badge + priority dot
   - Metadata: Feature, Component, Module, Assignee, Created, Updated
   - Tabs: Details | Acceptance Criteria | DoD | Subtasks
4. Details tab: Description (editable), status dropdown, priority selector
5. AC tab: List of acceptance criteria with checkbox toggle, add new AC
6. DoD tab: List of DoD items with checkbox toggle, add new DoD item
7. Subtasks tab: List of subtasks with status, add new subtask
8. All mutations show toast
9. Delete task from sheet header

**Acceptance Criteria**:
- [ ] Sheet opens on task row click
- [ ] All task metadata displayed
- [ ] Tabs switch between AC, DoD, Subtasks
- [ ] Toggle AC/DoD status works
- [ ] Add/delete AC, DoD, subtask works
- [ ] Edit task fields inline
- [ ] Delete task closes sheet and refreshes list
- [ ] `npm run build` passes

**Estimated effort**: 4-5 hours

---

### TASK-0051: Quality Page

**Goal**: Implement the Quality page with stats and quality metrics.

**Scope**:
1. Create `frontend/src/components/project/QualityPage.tsx`
2. Use `useQualityStats(projectId)` hook
3. Layout per SPEC-0012 §4.7:
   - Stats row: Total Tasks, Tasks with AC, AC Pass Rate, DoD Pass Rate
   - Progress bars for AC and DoD completion
   - Task quality table: Task title, AC count, DoD count, AC status, DoD status
4. Quality table uses TanStack Table
5. Click task → opens Task Detail Sheet (reuse from TASK-0050)
6. Loading/empty/error states

**Acceptance Criteria**:
- [ ] Quality stats cards show real data
- [ ] Progress bars show AC/DoD completion percentages
- [ ] Task quality table lists all tasks with quality metrics
- [ ] Click task opens detail sheet
- [ ] `npm run build` passes

**Estimated effort**: 2-3 hours

---

### TASK-0052: Audit Timeline Page

**Goal**: Implement the Audit page with filterable timeline.

**Scope**:
1. Create `frontend/src/components/project/AuditPage.tsx`
2. Create `frontend/src/components/project/AuditTimelineItem.tsx`
3. Use `useAuditEvents({ project_id, ...filters })` hook
4. Layout per SPEC-0012 §4.8:
   - Filters bar: event_type dropdown, entity_type dropdown, date range picker
   - Timeline: vertical timeline with event nodes
5. Each timeline item:
   - Timestamp (relative: "2 hours ago")
   - Event type badge (created, updated, deleted)
   - Entity type + entity name (link to entity if possible)
   - Actor (user or agent)
   - Expandable payload details
6. Pagination: Load more button
7. Loading/empty states

**Acceptance Criteria**:
- [ ] Timeline shows audit events chronologically
- [ ] Filters work (event_type, entity_type, date range)
- [ ] Each event shows timestamp, type, entity, actor
- [ ] Click entity link navigates to entity
- [ ] Pagination via load more
- [ ] `npm run build` passes

**Estimated effort**: 2-3 hours

---

### TASK-0053: Reports Page

**Goal**: Implement the Reports page.

**Scope**:
1. Create `frontend/src/components/ReportsPage.tsx`
2. Create `frontend/src/components/ReportDetail.tsx`
3. Routes: `/reports` (list) and `/projects/:id/reports` (project-scoped)
4. List view: Table with columns: Type, Summary, Created, Actions
5. Generate daily report button (calls POST endpoint)
6. Report detail: Render report content as formatted cards
7. Export as markdown button (calls export endpoint, triggers download)
8. LLM summarize button (if available)

**Acceptance Criteria**:
- [ ] Reports list shows all reports for project
- [ ] Generate daily report works
- [ ] Report detail renders content
- [ ] Export markdown downloads file
- [ ] `npm run build` passes

**Estimated effort**: 2-3 hours

---

### TASK-0054: Health Page

**Goal**: Implement the Health page.

**Scope**:
1. Create `frontend/src/components/HealthPage.tsx`
2. Use `useHealth()` hook (already exists with 30s polling)
3. Layout: Cards for each service
4. Backend card: status, response time (measured client-side)
5. Auto-refresh every 30 seconds
6. Status indicator: green (ok), red (error), yellow (degraded)

**Acceptance Criteria**:
- [ ] Health page shows backend status
- [ ] Auto-refreshes every 30s
- [ ] Status indicators work
- [ ] `npm run build` passes

**Estimated effort**: 1 hour

---

### TASK-0055: Dark Mode Toggle + Theme Persistence

**Goal**: Add dark mode toggle to TopBar.

**Scope**:
1. Add theme toggle button to TopBar (Sun/Moon icons)
2. Use `next-themes` ThemeProvider (already installed)
3. Wrap app in `<ThemeProvider>` in main.tsx
4. Persist theme choice in localStorage
5. Respect `prefers-color-scheme` as default

**Acceptance Criteria**:
- [ ] Toggle switches between light/dark/system
- [ ] Theme persists across page reloads
- [ ] All components render correctly in both themes
- [ ] `npm run build` passes

**Estimated effort**: 1 hour

---

### TASK-0056: Pagination Component + URL Sync

**Goal**: Implement reusable pagination with URL parameter sync.

**Scope**:
1. Create `frontend/src/components/ui/DataTablePagination.tsx`
2. Use shadcn Pagination component
3. URL sync: `?page=2&pageSize=20` in search params
4. Page size selector: 10, 20, 50
5. Shows: "Showing 1-20 of 142 results"
6. Integrate with all list pages (projects, features, tasks, audit, reports)

**Acceptance Criteria**:
- [ ] Pagination renders with page numbers
- [ ] URL updates on page change
- [ ] Page size selector works
- [ ] Integrated with all list views
- [ ] `npm run build` passes

**Estimated effort**: 2 hours

---

## 4. Implementation Order

```text
Phase 0 (Foundation):
  TASK-0043  Type fixes + Sidebar nav
  TASK-0044  Skeleton loading + Toast system
  TASK-0056  Pagination component

Phase 1 (Core Pages):
  TASK-0045  Dashboard
  TASK-0046  Project Detail (tabbed)
  TASK-0047  Form dialogs (all entities)
  TASK-0048  Structure page
  TASK-0049  Delivery page
  TASK-0050  Task Detail Sheet

Phase 2 (Extended):
  TASK-0051  Quality page
  TASK-0052  Audit timeline
  TASK-0053  Reports page
  TASK-0054  Health page

Phase 3 (Polish):
  TASK-0055  Dark mode toggle
```

---

## 5. Dependencies

```text
TASK-0043 → blocks everything (type fixes)
TASK-0044 → blocks all pages (skeleton + toast)
TASK-0056 → blocks list pages (pagination)
TASK-0047 → blocks TASK-0048, TASK-0049 (form dialogs needed for CRUD)
TASK-0050 → blocks TASK-0051 (task detail reused in quality page)
```

---

## 6. Out of Scope (Future)

| Feature | Reason |
|---|---|
| Board/Kanban view | List view first, board is polish |
| Command palette (Cmd+K) | Nice-to-have, not blocking |
| Global search | Needs backend search endpoint |
| Notifications | Needs backend notification system |
| Auth/RBAC | Single-user v1, add for multi-user |
| Git integration UI | Backend has endpoints but low priority |
| Drag-and-drop | Adds complexity, not critical |
