# TASK-0024: App Shell + Sidebar + TopBar

Spec: SPEC-0012 (Frontend UI/UX Architecture)
Status: done
Priority: 10
Model: routine
Milestone: M5

## Goal

Replace the bare `Layout.tsx` with a full app shell: collapsible sidebar with nav groups, top bar with search/notifications/avatar, and breadcrumb bar. Responsive behavior across mobile/tablet/desktop.

## Non-goals

- No page content beyond shell (each page is a separate task).
- No command palette (Phase 4).
- No dark mode toggle (Phase 4).
- No real authentication/user menu (placeholder only).

## Files involved

```text
frontend/src/components/layouts/AppShell.tsx       (new)
frontend/src/components/layouts/AppSidebar.tsx     (new)
frontend/src/components/layouts/TopBar.tsx         (new)
frontend/src/components/layouts/BreadcrumbBar.tsx  (new)
frontend/src/components/Layout.tsx                 (replace with AppShell)
frontend/src/router.tsx                           (update with nested routes)
frontend/src/lib/constants.ts                     (new — nav items, icons)
```

## TDD Steps

1. Install shadcn: Sidebar, Separator, Tooltip, Avatar, DropdownMenu, Skeleton.
2. Create `constants.ts` with nav item definitions (label, icon, path).
3. Create `AppSidebar.tsx` — collapsible sidebar with nav groups, Lucide icons.
4. Create `TopBar.tsx` — logo, search placeholder, notifications icon, avatar.
5. Create `BreadcrumbBar.tsx` — auto-generated from TanStack Router route context.
6. Create `AppShell.tsx` — compose Sidebar + TopBar + BreadcrumbBar + Outlet.
7. Update `router.tsx` — nested routes under AppShell.
8. Replace `Layout.tsx` with `AppShell`.
9. Test responsive behavior: mobile hamburger, tablet collapsed, desktop expanded.
10. Verify `npm run build` passes.

## Acceptance Criteria

- Sidebar shows nav items with Lucide icons (Dashboard, Projects, Reports, Health).
- Sidebar collapses/expands; state persisted in localStorage.
- TopBar shows "UPCP" logo, search placeholder, bell icon, avatar.
- Breadcrumbs update on route navigation.
- Mobile (< 768px): sidebar hidden, hamburger toggle in TopBar.
- Tablet (768-1023px): sidebar collapsed (icons only, 64px).
- Desktop (>= 1024px): sidebar expanded (240px).
- Keyboard navigation works (Tab through nav items).
- Focus ring visible on interactive elements.
- `npm run build` succeeds with no TypeScript errors.

## Expected test

```tsx
// frontend/src/components/layouts/AppSidebar.test.tsx
import { render, screen } from '@testing-library/react';
import { AppSidebar } from './AppSidebar';

test('renders navigation items', () => {
  render(<AppSidebar />);
  expect(screen.getByText('Dashboard')).toBeInTheDocument();
  expect(screen.getByText('Projects')).toBeInTheDocument();
  expect(screen.getByText('Reports')).toBeInTheDocument();
  expect(screen.getByText('Health')).toBeInTheDocument();
});

test('sidebar collapses on button click', async () => {
  render(<AppSidebar />);
  const collapseBtn = screen.getByRole('button', { name: /collapse/i });
  fireEvent.click(collapseBtn);
  expect(screen.queryByText('Dashboard')).not.toBeVisible();
});
```

## DoD

- sidebar created with nav groups;
- topbar created with search/notifications/avatar;
- breadcrumbs auto-generated from routes;
- responsive behavior verified;
- build passes;
- task file status updated;
- `PROJECT_STATUS.md` updated.
