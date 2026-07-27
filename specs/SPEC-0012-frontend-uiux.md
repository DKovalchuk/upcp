# SPEC-0012: Frontend UI/UX Architecture

**Status**: Draft
**Date**: 2026-07-24
**Scope**: Full frontend UI/UX architecture for UPCP
**Stack**: React 19 + Vite + TypeScript + Tailwind CSS v4 + shadcn/ui (base-nova) + TanStack Query + TanStack Router + Lucide React icons

---

## 1. Information Architecture

### 1.1 Route Tree

```text
/                                    Dashboard (home)
/projects                            Project list
/projects/:projectId                 Project detail (tabbed)
/projects/:projectId/structure       Components + Modules
/projects/:projectId/delivery        Features + Tasks
/projects/:projectId/quality         Quality gates
/projects/:projectId/audit           Audit log
/projects/:projectId/settings        Project settings
/reports                             Global reports list
/reports/:reportId                   Report detail
/health                              System health
```

### 1.2 Navigation Hierarchy

```text
TOP BAR: [Logo/Brand] [Global Search] [Notifications] [User Menu]
SIDEBAR:
  Dashboard (/)
  Projects (/projects)
  ──────────────────────────
  When a project is selected:
    Project Overview (/projects/:id)
    Structure (/projects/:id/structure)
    Delivery (/projects/:id/delivery)
    Quality (/projects/:id/quality)
    Audit (/projects/:id/audit)
    Settings (/projects/:id/settings)
  ──────────────────────────
  Reports (/reports)
  Health (/health)
  ──────────────────────────
  [Collapse sidebar]
```

### 1.3 Breadcrumb Pattern

```text
Dashboard > Projects > My Project > Delivery > TASK-0042
```

---

## 2. Design System

### 2.1 Color Tokens

| Token | Role | Light | Dark |
|---|---|---|---|
| `--color-primary` | CTAs, active nav, links | `#2563eb` | `#3b82f6` |
| `--color-secondary` | Secondary buttons, badges | `#64748b` | `#94a3b8` |
| `--color-accent` | Highlights, warnings | `#f59e0b` | `#fbbf24` |
| `--color-bg` | Page background | `#ffffff` | `#0f172a` |
| `--color-surface` | Cards, panels | `#f8fafc` | `#1e293b` |
| `--color-text` | Primary text (4.5:1+) | `#1e293b` | `#f1f5f9` |
| `--color-text-muted` | Secondary text | `#64748b` | `#94a3b8` |

### 2.2 Status Colors

| Status | Background | Text |
|---|---|---|
| `active` / `passed` | `bg-emerald-500/10` | `text-emerald-700 dark:text-emerald-400` |
| `backlog` / `pending` | `bg-slate-500/10` | `text-slate-700 dark:text-slate-400` |
| `in-progress` | `bg-blue-500/10` | `text-blue-700 dark:text-blue-400` |
| `paused` | `bg-amber-500/10` | `text-amber-700 dark:text-amber-400` |
| `archived` / `failed` | `bg-red-500/10` | `text-red-700 dark:text-red-400` |
| `done` / `completed` | `bg-violet-500/10` | `text-violet-700 dark:text-violet-400` |

### 2.3 Priority Colors

| Priority | Indicator |
|---|---|
| P0 (critical) | `bg-red-500` solid dot |
| P1 (high) | `bg-orange-500` solid dot |
| P2 (medium) | `bg-blue-500` solid dot |
| P3 (low) | `bg-slate-400` solid dot |

### 2.4 Typography Scale

| Element | Class | Size | Weight |
|---|---|---|---|
| Page title | `text-2xl font-bold tracking-tight` | 24px | 700 |
| Section heading | `text-lg font-semibold` | 18px | 600 |
| Card title | `text-base font-medium` | 16px | 500 |
| Body | `text-sm` | 14px | 400 |
| Caption / label | `text-xs text-muted-foreground` | 12px | 400 |
| Code / slug | `font-mono text-xs` | 12px | 400 |

### 2.5 Spacing Scale

| Token | Value | Usage |
|---|---|---|
| `--spacing-xs` | 4px | Inline element gaps |
| `--spacing-sm` | 8px | Component internal padding |
| `--spacing-md` | 16px | Card padding, form gaps |
| `--spacing-lg` | 24px | Section gaps inside cards |
| `--spacing-xl` | 32px | Section spacing |
| `--spacing-2xl` | 48px | Page section separation |
| `--spacing-3xl` | 64px | Top-level page padding |

---

## 3. Layout Architecture

### 3.1 App Shell

```text
+--------------------------------------------------------------+
| TopBar (h-14)                                                |
| [Logo] [GlobalSearch ................] [Bell] [Avatar/Menu]  |
+----------+---------------------------------------------------+
|          |                                                   |
| Sidebar  | MainContent (Outlet)                              |
| (w-60)   |                                                   |
|          | +-- Breadcrumb bar (h-10) -----------------+     |
| [Nav]    | | Dashboard > Projects > MyProject          |     |
|          | +------------------------------------------+     |
| [Groups] |                                                   |
|          | +-- PageContent ---------------------------+     |
| [Nav]    | |                                          |     |
|          | | (children)                               |     |
| [Footer] | |                                          |     |
|          | +------------------------------------------+     |
+----------+---------------------------------------------------+
```

### 3.2 Sidebar

- Width: 240px expanded, 64px collapsed (icons only)
- Persistent across routes, collapse state in localStorage
- Nav groups: Main, Project (contextual), System

**Icons** (Lucide React):

| Nav Item | Icon |
|---|---|
| Dashboard | `LayoutDashboard` |
| Projects | `FolderKanban` |
| Overview | `Info` |
| Structure | `Boxes` |
| Delivery | `GitBranch` |
| Quality | `ShieldCheck` |
| Audit | `ScrollText` |
| Settings | `Settings` |
| Reports | `BarChart3` |
| Health | `Activity` |

### 3.3 Responsive Behavior

| Breakpoint | Sidebar | Content padding |
|---|---|---|
| `< 768px` (mobile) | Hidden, overlay | `px-4` |
| `768px - 1023px` (tablet) | Collapsed (64px) | `px-6` |
| `>= 1024px` (desktop) | Expanded (240px) | `px-8`, max-width 1400px |

---

## 4. Page Specifications

### 4.1 Dashboard (`/`)

Stats row (4 cards) + two-column: Recent Projects (col-span-2) + Activity Feed (col-span-1).

### 4.2 Project List (`/projects`)

Table with search, status filter, sort. Columns: Name, Status, Components, Tasks, Updated, Actions.

### 4.3 Project Detail (`/projects/:projectId`)

Tabbed layout: Overview | Structure | Delivery | Quality | Audit | Settings.

### 4.4 Structure (`/projects/:projectId/structure`)

Card grid for components. Click expands to show modules table.

### 4.5 Delivery (`/projects/:projectId/delivery`)

Feature groups with task tables. Toolbar: View toggle (List/Board), Filter, Search, + Feature.

### 4.6 Task Detail (slide-over panel)

Status, Priority, Component, Module, Assignee. Tabs: Details | AC | DoD.

### 4.7 Quality (`/projects/:projectId/quality`)

Stats row + task quality table (AC count, DoD items, pass rate).

### 4.8 Audit (`/projects/:projectId/audit`)

Timeline with filters (entity type, event type, date range).

### 4.9 Reports (`/reports`)

Table list + detail page rendering markdown.

### 4.10 Health (`/health`)

Cards: backend status, DB connectivity, API response times.

---

## 5. Component Inventory

### 5.1 shadcn/ui Components

**Phase 1**: Input, Badge, DropdownMenu, Dialog, Tabs, Skeleton, Avatar, Select, Tooltip, Separator
**Phase 2**: Sheet, Popover, Command, Breadcrumb, Pagination, Alert, Toast/Sonner, Progress, Sidebar
**Phase 3**: Accordion, Checkbox, Textarea, Switch, ScrollArea, ResizablePanel

### 5.2 Custom Shared Components

`StatusBadge`, `PriorityDot`, `EmptyState`, `ErrorState`, `PageHeader`, `SearchInput`, `ConfirmDialog`, `TimelineItem`

### 5.3 Layout Components

`AppShell`, `AppSidebar`, `TopBar`, `BreadcrumbBar`

---

## 6. UX Patterns

- **Loading**: Skeleton screens (not spinners) matching final layout
- **Errors**: Icon + message + Retry button
- **Empty**: Icon + message + CTA button
- **Confirmations**: Dialog for destructive actions
- **Toasts**: sonner library, bottom-right, success/error
- **Forms**: Dialog (create/edit) or Sheet (slide-over), inline validation
- **Optimistic updates**: TanStack Query for status changes

---

## 7. Accessibility (WCAG 2.1 AA)

- Semantic HTML: `<nav>`, `<main>`, `<header>`, `<aside>`, `<section>`, `<article>`
- Keyboard: Tab navigation, focus rings, focus traps in dialogs
- ARIA: labels, expanded states, live regions, sort indicators
- Color: 4.5:1 contrast, status conveyed by color + text
- Screen reader: page titles, skip-to-content link

---

## 8. Implementation Order

### Phase 1: Foundation (TASK-0024 to TASK-0026)

- **TASK-0024**: App Shell + Sidebar + TopBar
- **TASK-0025**: Design System Components (StatusBadge, EmptyState, etc.)
- **TASK-0026**: Type Definitions + API Client Expansion + TanStack Query hooks

### Phase 2: Core Pages (TASK-0027 to TASK-0031)

- **TASK-0027**: Dashboard Page
- **TASK-0028**: Project List (enhance) + Detail + Form Dialog
- **TASK-0029**: Structure Page (Components + Modules)
- **TASK-0030**: Delivery Page (Features + Tasks list)
- **TASK-0031**: Task Detail Panel + Quality Page

### Phase 3: Extended Pages (TASK-0032 to TASK-0034)

- **TASK-0032**: Audit Timeline Page
- **TASK-0033**: Reports Pages (list + detail)
- **TASK-0034**: Health Page

### Phase 4: Polish (TASK-0035 to TASK-0037)

- **TASK-0035**: Board View (Kanban) for Delivery
- **TASK-0036**: Command Palette (Cmd+K)
- **TASK-0037**: Dark mode toggle + theme persistence

---

## 9. Key Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Navigation | Sidebar | Multi-level nav scales better than top nav for 10+ items |
| Icons | Lucide React | Already installed, tree-shakeable |
| State management | TanStack Query + URL params | Server state via Query, UI state via URL |
| Forms | Dialog + Sheet | Dialog for CRUD, Sheet for detail panels |
| Board view | Phase 4 | List view first for faster delivery |
