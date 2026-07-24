# TASK-0025: Design System Components

Spec: SPEC-0012 (Frontend UI/UX Architecture)
Status: done
Priority: 10
Model: routine
Milestone: M5

## Goal

Build shared UI primitives that every page needs: StatusBadge, PriorityDot, EmptyState, ErrorState, PageHeader, SearchInput, ConfirmDialog. Install additional shadcn/ui components. Create constants file with status color mappings.

## Non-goals

- No page-level components (each page is a separate task).
- No API integration (TASK-0026 handles that).
- No form dialogs for specific entities (handled in page tasks).

## Files involved

```text
frontend/src/components/ui/StatusBadge.tsx     (new)
frontend/src/components/ui/PriorityDot.tsx     (new)
frontend/src/components/ui/EmptyState.tsx      (new)
frontend/src/components/ui/ErrorState.tsx      (new)
frontend/src/components/ui/PageHeader.tsx      (new)
frontend/src/components/ui/SearchInput.tsx     (new)
frontend/src/components/ui/ConfirmDialog.tsx   (new)
frontend/src/lib/constants.ts                  (new — status colors, priority labels)
```

## TDD Steps

1. Install shadcn: Badge, Input, Dialog, Select, Skeleton, Tooltip, Sonner.
2. Create `constants.ts` with STATUS_COLORS, PRIORITY_LABELS, NAV_ITEMS.
3. Create `StatusBadge.tsx` — takes status string, returns colored badge pill.
4. Create `PriorityDot.tsx` — takes priority level, returns colored dot.
5. Create `EmptyState.tsx` — icon + message + optional CTA button.
6. Create `ErrorState.tsx` — icon + message + retry button.
7. Create `PageHeader.tsx` — title + description + optional action buttons.
8. Create `SearchInput.tsx` — input with debounce and clear button.
9. Create `ConfirmDialog.tsx` — dialog with title, message, cancel/confirm buttons.
10. Test each component renders correctly.
11. Verify `npm run build` passes.

## Acceptance Criteria

- `StatusBadge` renders correct color for each status (active, backlog, in-progress, paused, archived, done).
- `PriorityDot` renders correct color for P0-P3.
- `EmptyState` shows icon, message, and optional CTA.
- `ErrorState` shows error icon, message, retry button.
- `PageHeader` shows title, description, and action slot.
- `SearchInput` debounces input (300ms default).
- `ConfirmDialog` opens, confirms, and cancels correctly.
- All components have TypeScript prop interfaces.
- All components under 100 lines.
- `npm run build` succeeds with no TypeScript errors.

## Expected test

```tsx
// frontend/src/components/ui/StatusBadge.test.tsx
import { render, screen } from '@testing-library/react';
import { StatusBadge } from './StatusBadge';

test('renders active status with correct styling', () => {
  render(<StatusBadge status="active" />);
  const badge = screen.getByText('active');
  expect(badge).toBeInTheDocument();
  expect(badge).toHaveClass('bg-emerald-500/10');
});

test('renders backlog status with correct styling', () => {
  render(<StatusBadge status="backlog" />);
  const badge = screen.getByText('backlog');
  expect(badge).toHaveClass('bg-slate-500/10');
});
```

## DoD

- all shared UI components created;
- constants.ts with color mappings;
- shadcn components installed;
- tests pass;
- build passes;
- task file status updated;
- `PROJECT_STATUS.md` updated.
