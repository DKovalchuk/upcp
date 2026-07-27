# Information Architecture

Navigation structure and pages of UPCP.

---

## 1. Navigation Structure

### Top Bar

```
[Logo] [Global Search (Cmd+K)] [Notifications Bell] [User Menu]
```

### Sidebar

```
MAIN
  Dashboard (/)
  Projects (/projects)
  ─────────────────────
PROJECT (contextual, when project selected)
  Overview (/projects/:id)
  Structure (/projects/:id/structure)
  Delivery (/projects/:id/delivery)
  Quality (/projects/:id/quality)
  Agents (/projects/:id/agents)
  Evidence & Reviews (/projects/:id/evidence)
  Git (/projects/:id/git)
  Audit (/projects/:id/audit)
  Settings (/projects/:id/settings)
  ─────────────────────
SYSTEM
  Agent Center (/agents)
  Reports (/reports)
  Health (/health)
  ─────────────────────
  [Collapse sidebar]
```

**Icons (Lucide):**

| Element | Icon |
|---------|--------|
| Dashboard | `LayoutDashboard` |
| Projects | `FolderKanban` |
| Overview | `Info` |
| Structure | `Boxes` |
| Delivery | `GitBranch` |
| Quality | `ShieldCheck` |
| Agents | `Bot` |
| Evidence | `FileCheck` |
| Git | `GitFork` |
| Audit | `ScrollText` |
| Settings | `Settings` |
| Agent Center | `BrainCircuit` |
| Reports | `BarChart3` |
| Health | `Activity` |
| Notifications | `Bell` |

---

## 2. Pages

### Dashboard (`/`)

**View:** Attention Dashboard — focused on what requires attention.

**Sections:**
- Needs your review
- Open agent questions
- Blocked tasks
- Stale agent claims
- Failed quality gates
- Recent agent activity

See [attention-dashboard.md](./attention-dashboard.md).

---

### Portfolio / Project List (`/projects`)

Project table with search, status filter, and sorting.

**Columns:** Name, Status, Components, Tasks, Last Activity.

---

### Project Detail (`/projects/:projectId`)

**Layout:** Tabbed layout with URL-synced tabs.

| Tab | Route | Content |
|-----|-------|---------|
| Overview | `/projects/:id` | Status, description, statistics |
| Structure | `/projects/:id/structure` | Components → Modules |
| Delivery | `/projects/:id/delivery` | Features → Tasks (list/board) |
| Quality | `/projects/:id/quality` | AC/DoD statistics, quality gates |
| Agents | `/projects/:id/agents` | Assigned agents, claims |
| Evidence & Reviews | `/projects/:id/evidence` | Evidence list, review rounds |
| Git | `/projects/:id/git` | Providers, branches, commits, links |
| Audit | `/projects/:id/audit` | Timeline with filters |
| Settings | `/projects/:id/settings` | Project settings |

---

### Component Detail

Inside the Structure tab. Accordion/card expands to view modules.

---

### Module Detail

Inside Component expand. Module table with columns: Name, Status, Features.

---

### Feature Detail

Inside the Delivery tab. Feature as a group of tasks with a collapsible header.

---

### Task Detail

**Layout:** Sheet (slide-over) by default. Full page via deep link.

**Tabs:** Details, Execution, Clarifications, Evidence, DoD, Subtasks, Reviews, Git, Audit.

See [task-detail.md](./task-detail.md).

---

### Agent Center (`/agents`)

Agent management. List + details.

See [agent-center.md](./agent-center.md).

---

### Notifications (`/notifications`)

Notification history with filters.

See [notifications.md](./notifications.md).

---

### Reports (`/reports`)

Global report list. daily/weekly generation. Markdown export.

---

### Health (`/health`)

Status: backend, DB, Redis, MCP. Auto-refresh.

---

### Settings (global)

Settings: profile, notifications, theme. `/settings` route.

---

## 3. Breadcrumbs

```
Dashboard > Projects > UPCP v2 > Delivery > TASK-0042
```

Rules:
- Each element is a clickable link.
- The last element is the current page (not a link).
- On mobile: last 3 levels are shown.

---

## 4. Deep Links

| Resource | URL |
|--------|-----|
| Project | `/projects/:id` |
| Project + tab | `/projects/:id?tab=delivery` |
| Component | `/projects/:id/structure?component=:cid` |
| Task (sheet) | `/projects/:id/delivery?task=:tid` |
| Task (page) | `/projects/:id/tasks/:tid` |
| Agent | `/agents/:id` |
| Report | `/reports/:id` |

---

## 5. URL State

UI state is synchronized with the URL:

- `?tab=` — active project tab
- `?task=` — open task detail sheet
- `?component=` — expanded component
- `?view=list|board` — delivery display mode
- `?page=&pageSize=` — pagination
- `?search=` — search query
- `?status=` — status filter

---

## 6. Responsive Behavior

| Breakpoint | Sidebar | Content |
|-----------|---------|---------|
| < 768px | Hidden, overlay | `px-4` |
| 768–1023px | Collapsed (64px, icons) | `px-6` |
| ≥ 1024px | Expanded (240px) | `px-8`, max-width 1400px |
