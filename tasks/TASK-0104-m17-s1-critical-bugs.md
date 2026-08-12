# TASK-0104 — M17 Sprint 1: Critical Bug Fixes

**Spec:** SPEC-0020
**Milestone:** M17
**Sprint:** S19.1
**Status:** PENDING
**Size:** M (5 points)

## Objective

Fix 5 critical/high bugs found in M16 audit that affect core functionality and user experience.

## Context

These bugs were identified during the M16 comprehensive audit (AUDIT_M16_COMPREHENSIVE.md). Each bug is a concrete, reproducible issue with a clear fix path. No architectural changes required — these are targeted fixes.

---

## Bug 1: Query String Construction in fetchProjectTasks

**Severity:** Critical
**File:** `frontend/src/lib/api/tasks.ts`
**Function:** `fetchProjectTasks`

### Problem

The `sep` logic is broken when both query filters and pagination are present. `paginationParams()` returns strings prefixed with `?` (e.g., `"?offset=0&limit=20"`), but `sep` is set to `&` when both `qs` and `pag` are non-empty. The resulting URL is `/tasks&status=foo?offset=0&limit=20` — malformed.

### Current Code (broken)

```typescript
const sep = qs && pag ? '&' : qs ? '?' : '';
const url = `/api/v1/projects/${projectId}/tasks${qs}${sep}${pag}`;
```

### Fix

```typescript
const params = [qs, pag].filter(Boolean);
const url = `/api/v1/projects/${projectId}/tasks${params.length ? '?' + params.join('&') : ''}`;
```

Or simpler: build the URL with `URLSearchParams`.

### Acceptance Criteria

- [ ] URL is correctly formed when only pagination is present: `/tasks?offset=0&limit=20`
- [ ] URL is correctly formed when only filters are present: `/tasks?status=backlog`
- [ ] URL is correctly formed when both are present: `/tasks?status=backlog&offset=0&limit=20`
- [ ] URL is correctly formed when neither is present: `/tasks`

### Acceptance Tests

```typescript
describe('fetchProjectTasks URL construction', () => {
  it('builds URL with pagination only', () => {
    // Given: no filters, offset=0, limit=20
    // When: fetchProjectTasks called
    // Then: URL is /api/v1/projects/{id}/tasks?offset=0&limit=20
  });

  it('builds URL with filters only', () => {
    // Given: status=backlog, no pagination
    // When: fetchProjectTasks called
    // Then: URL is /api/v1/projects/{id}/tasks?status=backlog
  });

  it('builds URL with filters and pagination', () => {
    // Given: status=backlog, offset=10, limit=20
    // When: fetchProjectTasks called
    // Then: URL is /api/v1/projects/{id}/tasks?status=backlog&offset=10&limit=20
  });

  it('builds URL with no params', () => {
    // Given: no filters, no pagination
    // When: fetchProjectTasks called
    // Then: URL is /api/v1/projects/{id}/tasks
  });
});
```

---

## Bug 2: Project Settings Route Broken

**Severity:** High
**File:** `frontend/src/components/project/ProjectDetail.tsx`
**Lines:** TAB_ROUTES map (line ~37)

### Problem

The sidebar's `PROJECT_NAV_GROUP` has a "Settings" item pointing to `/projects/$projectId/settings`. The router defines `projectSettingsRoute`. However, `ProjectDetail`'s `TAB_ROUTES` map does NOT include `'settings'`, so `activeTab` defaults to `'overview'`. The user sees the Overview tab instead of a Settings tab.

### Current Code (broken)

```typescript
const TAB_ROUTES: Record<string, string> = {
  structure: 'structure',
  delivery: 'delivery',
  quality: 'quality',
  audit: 'audit',
  git: 'git',
  reports: 'reports',
  // 'settings' is MISSING
};
```

### Fix

1. Add `'settings': 'settings'` to `TAB_ROUTES`
2. Add a `<TabsTrigger value="settings">Settings</TabsTrigger>` to the tabs list
3. Add a `<TabsContent value="settings">` that renders a ProjectSettings component (or a placeholder with project-level settings)

### Project Settings Content (minimal viable)

The project settings tab should show:
- Project name (editable)
- Project slug (read-only)
- Project description (editable)
- Project status (editable: active/paused/archived)
- Delete project button
- Project health score (read-only)

This reuses the existing edit dialog but embedded as a tab.

### Acceptance Criteria

- [ ] Clicking "Settings" in sidebar navigates to `/projects/{id}/settings`
- [ ] Settings tab is active when URL is `/projects/{id}/settings`
- [ ] Settings tab shows project edit form
- [ ] Other tabs still work correctly
- [ ] URL updates when switching tabs

### Acceptance Tests

```typescript
describe('Project Settings route', () => {
  it('shows Settings tab when navigating to /projects/:id/settings', () => {
    // Given: user is on project detail page
    // When: navigates to /projects/:id/settings
    // Then: Settings tab is active, shows project edit form
  });

  it('updates URL when clicking Settings tab', () => {
    // Given: user is on Overview tab
    // When: clicks Settings tab trigger
    // Then: URL changes to /projects/:id/settings
  });
});
```

---

## Bug 3: TopBar Profile/Settings No-Ops

**Severity:** High
**File:** `frontend/src/components/layouts/TopBar.tsx`
**Lines:** 91-92

### Problem

The TopBar dropdown menu has "Profile" and "Settings" items with `onClick={() => {}}` — clickable items that do nothing. Users click them expecting navigation.

### Fix

Wire both items to navigate:
```typescript
<DropdownMenuItem onClick={() => navigate({ to: '/settings' })}>
  Profile
</DropdownMenuItem>
<DropdownMenuItem onClick={() => navigate({ to: '/settings' })}>
  Settings
</DropdownMenuItem>
```

When the Settings page has tabs (M18), Profile can navigate to `/settings?tab=profile`.

### Acceptance Criteria

- [ ] Clicking "Profile" navigates to `/settings`
- [ ] Clicking "Settings" navigates to `/settings`
- [ ] Dropdown closes after navigation

### Acceptance Tests

```typescript
describe('TopBar dropdown navigation', () => {
  it('navigates to /settings when Profile is clicked', () => {
    // Given: TopBar dropdown is open
    // When: user clicks Profile
    // Then: navigates to /settings
  });

  it('navigates to /settings when Settings is clicked', () => {
    // Given: TopBar dropdown is open
    // When: user clicks Settings
    // Then: navigates to /settings
  });
});
```

---

## Bug 4: Settings Version Hardcoded

**Severity:** Medium
**File:** `frontend/src/components/SettingsPage.tsx`
**Line:** 8

### Problem

`const APP_VERSION = '0.14.0'` is hardcoded. Current version is 0.17.0 (4 milestones stale).

### Fix

Option A (simple): Update to `'0.17.0'` — requires manual update each release.
Option B (better): Read from `import.meta.env.VITE_APP_VERSION` set by Vite from `package.json`.
Option C (best): Add `app_version` to the `/health` response and read from there.

**Recommended:** Option B — add to `vite.config.ts`:
```typescript
define: {
  'import.meta.env.VITE_APP_VERSION': JSON.stringify(process.env.npm_package_version),
}
```

Then in SettingsPage:
```typescript
const APP_VERSION = import.meta.env.VITE_APP_VERSION || 'unknown';
```

### Acceptance Criteria

- [ ] Settings page shows correct version (matching `package.json`)
- [ ] Version updates automatically when `package.json` changes
- [ ] Fallback to 'unknown' if env var not set

### Acceptance Tests

```typescript
describe('SettingsPage version', () => {
  it('displays version from environment', () => {
    // Given: VITE_APP_VERSION is set to '0.17.0'
    // When: SettingsPage renders
    // Then: version displays '0.17.0'
  });
});
```

---

## Bug 5: Dashboard "New Project" No-Op

**Severity:** Low
**File:** `frontend/src/components/Dashboard.tsx`
**Line:** 102

### Problem

Empty state has `action={{ label: 'New Project', onClick: () => {} }}` — button does nothing.

### Fix

Navigate to projects page and programmatically open the create dialog. Since the create dialog is in ProjectList, the simplest fix is to navigate to `/projects` with a search param:

```typescript
action={{
  label: 'New Project',
  onClick: () => navigate({ to: '/projects', search: { create: true } }),
}}
```

Then in ProjectList, check for `create` search param and open the dialog.

Alternatively, just navigate to `/projects` — the user can click "New Project" there.

### Acceptance Criteria

- [ ] Clicking "New Project" in empty state navigates to `/projects`
- [ ] (Optional) Create dialog opens automatically

### Acceptance Tests

```typescript
describe('Dashboard empty state', () => {
  it('navigates to /projects when New Project is clicked', () => {
    // Given: Dashboard shows empty state (0 projects)
    // When: user clicks "New Project"
    // Then: navigates to /projects
  });
});
```

---

## Files to Modify

| File | Action | Bug |
|------|--------|-----|
| `frontend/src/lib/api/tasks.ts` | MODIFY | #1 |
| `frontend/src/components/project/ProjectDetail.tsx` | MODIFY | #2 |
| `frontend/src/components/layouts/TopBar.tsx` | MODIFY | #3 |
| `frontend/src/components/SettingsPage.tsx` | MODIFY | #4 |
| `frontend/src/components/Dashboard.tsx` | MODIFY | #5 |
| `frontend/vite.config.ts` | MODIFY | #4 |
| `frontend/src/components/project/ProjectDetail.test.tsx` | CREATE | #2 |
| `frontend/src/components/Dashboard.test.tsx` | MODIFY | #5 |

## Dependencies

None — this sprint can start immediately.

## Definition of Done

- [ ] All 5 bugs fixed
- [ ] 5 new frontend tests pass
- [ ] All 260+ existing frontend tests pass
- [ ] TypeScript: 0 errors
- [ ] Manual smoke test: navigate all routes, verify fixes
