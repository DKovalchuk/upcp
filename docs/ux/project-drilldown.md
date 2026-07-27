# Project Drill-Down UX

Hierarchical navigation: Portfolio → Project → Component → Module → Feature → Task.

---

## 1. Hierarchy

```
Portfolio (/projects)
└── Project (/projects/:id)
    └── Component (expand in Structure tab)
        └── Module (expand in Component)
            └── Feature (group header in Delivery tab)
                └── Task (sheet or page)
                    ├── Subtask
                    ├── AcceptanceCriterion
                    ├── DoDItem
                    ├── Evidence
                    ├── ReviewRound → ReviewFinding
                    ├── ClarificationRequest
                    └── Audit trail
```

---

## 2. Navigation Patterns

### 2.1 Breadcrumbs

Always visible in BreadcrumbBar:

```
Dashboard > Projects > UPCP v2 > Delivery > TASK-0042
```

- Each element is clickable.
- The last one is the current page (not a link).
- On mobile: last 3 levels + "..." for the rest.

### 2.2 Deep Links

| Resource | URL | Type |
|--------|-----|-----|
| Project overview | `/projects/:id` | page |
| Project + tab | `/projects/:id?tab=delivery` | page + tab |
| Component | `/projects/:id/structure?component=:cid` | expand |
| Module | `/projects/:id/structure?component=:cid&module=:mid` | expand |
| Feature | `/projects/:id/delivery?feature=:fid` | expand |
| Task (sheet) | `/projects/:id/delivery?task=:tid` | sheet |
| Task (page) | `/projects/:id/tasks/:tid` | page |

### 2.3 URL State Sync

All UI states are synchronized with URL search params:

| Param | Type | Description |
|-------|------|-------------|
| `tab` | string | Active project tab |
| `component` | UUID | Expanded component |
| `module` | UUID | Expanded module |
| `feature` | UUID | Expanded feature |
| `task` | UUID | Open task detail sheet |
| `view` | `list` \| `board` | Delivery mode |
| `page` | int | Page number |
| `pageSize` | int | Page size |
| `search` | string | Search query |
| `status` | string | Status filter |
| `sort` | string | Sorting |

**Behavior:**
- Back/forward navigation restores state.
- Share URL opens the same view.
- Cmd+click opens in a new tab.

---

## 3. Portfolio Level (`/projects`)

### Project Table

**Columns:** Name, Status, Components, Tasks (total), Active Tasks, Last Activity.

**Features:** Search, status filter, sorting, pagination (URL-synced), click → project detail.

---

## 4. Project Level (`/projects/:id`)

### Tabs

| Tab | Content |
|-----|---------|
| Overview | Status, description, stats cards |
| Structure | Components → Modules |
| Delivery | Features → Tasks |
| Quality | AC/DoD statistics |
| Agents | Assigned agents |
| Evidence & Reviews | Evidence list, review rounds |
| Git | Providers, branches, commits, links |
| Audit | Timeline |
| Settings | Project settings |

Tab state synced with the `?tab=` URL param.

---

## 5. Component Level (Structure tab)

Card grid for components. Click → expand with module table.

```
┌─────────────────────────────────┐
│ Backend Core                    │
│ Status: active · 5 modules      │
│ ▼                               │
├─────────────────────────────────┤
│ │ Module        │ Status │ Tasks│ │
│ │ User Module   │ active │ 8    │ │
│ │ Auth Module   │ active │ 5    │ │
└─────────────────────────────────┘
```

---

## 6. Module Level (expand inside Component)

Module table: Name, Status, Features count, Tasks count. Click → filters the Delivery tab.

---

## 7. Feature Level (Delivery tab)

Features are collapsible task groups.

```
▼ Auth System (feat_001) — 8 tasks · 3 done · 2 in progress
  ├─ [P1] Add User model              ready      claude-builder
  ├─ [P0] JWT authentication           in_progress claude-builder
  └─ [P2] Password reset flow          backlog     unassigned
```

**View toggle:** List / Board (Kanban).

---

## 8. Task Level

### Sheet (slide-over)

Default. See [task-detail.md](./task-detail.md).

### Full Page (`/projects/:id/tasks/:tid`)

Via deep link. Same content in a full-screen layout.

---

## 9. Saved Views

User saves a combination of filters:

```
Saved View: "My blocked tasks"
  - status: blocked
  - assignee: me
  - project: UPCP v2
```

**Storage:** localStorage + optional server-side. **UI:** "Saved Views" dropdown in the toolbar.

---

## 10. Keyboard Navigation

| Key | Action |
|-----|----------|
| `Cmd+K` | Command palette |
| `[` / `]` | Previous / next tab |
| `Esc` | Close sheet |
| `j` / `k` | Navigate list items |
| `Enter` | Open selected item |
| `Cmd+Click` | Open in new tab |
