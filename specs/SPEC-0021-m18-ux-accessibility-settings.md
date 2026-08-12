# SPEC-0021 — M18: UX Polish, Accessibility & Settings

**Milestone:** M18
**Version:** 0.20.0
**Status:** PLANNED
**Created:** 2026-08-12
**Source:** M16 Audit findings U7-U9, U14-U19, U23

## 1. Problem

The UI has strong foundations but several accessibility gaps, a minimal settings page, and incomplete notification UX that prevent production readiness.

## 2. Scope

### S20.1: Accessibility (TASK-0108, 8pts)

| Finding | Fix |
|---------|-----|
| BoardView has no keyboard DnD | Add `KeyboardSensor` from @dnd-kit |
| Accordion sections lack ARIA | Add `aria-expanded`, `role="button"`, keyboard handlers to FeatureSection/ComponentCard |
| BreadcrumbBar skips UUIDs | Resolve project name from project ID, show in breadcrumb |
| BoardView task cards not focusable | Add `tabIndex={0}` and keyboard Enter handler |
| SavedViewsDropdown inner button | Remove nested button, use DropdownMenuItem onSelect |

### S20.2: Settings Redesign (TASK-0109, 8pts)

Current settings: theme toggle, API info, version. Target:

```
/settings
├── Profile        — user name, email, password change
├── Notifications  — per-event-type toggle, channel selection
├── Channels       — email/webhook CRUD, test connection (from M16)
├── Appearance     — theme toggle (existing)
└── About          — version, API info, health status (existing)
```

### S20.3: Notification UX (TASK-0110, 5pts)

| Finding | Fix |
|---------|-----|
| Notification click does not navigate | Add entity navigation on click |
| No notification full page | Create `/notifications` page with filters |
| Notification mark-read has no error handling | Add `.catch()` with toast error |
| No notification type filtering | Add type filter dropdown |

### S20.4: Project Dashboard Enhancement (TASK-0111, 5pts)

| Enhancement | Detail |
|-------------|--------|
| Health score card | Show project health with trend indicator |
| Task completion donut | Chart showing done/in-progress/backlog distribution |
| Velocity sparkline | Tasks completed per week (last 8 weeks) |
| Recent activity | Last 10 audit events for this project |

## 3. Exit Criteria

- BoardView fully keyboard-accessible (Tab, Enter, Space, Arrow keys)
- All interactive elements have ARIA attributes
- Settings page has 5 tabs
- `/notifications` page exists with filters and grouping
- Notification click navigates to entity
- Breadcrumbs show resolved names
- Project overview has health + charts
- All existing tests pass + 15 new tests
