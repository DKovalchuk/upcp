# TASK-0023 Portfolio View (Project List)

Spec: SPEC-0006 (Frontend spec) — backlog
Status: done
Priority: 10
Model: routine
Milestone: M5

## Goal

Create portfolio view (project list) at route `/`. Fetch projects from API: `GET /api/v1/projects`. Display: name, status, created_at. Responsive layout with Tailwind.

## Non-goals

- No project detail page.
- No CRUD operations.
- No pagination (will be added later).
- No filtering/sorting.

## Files likely involved

```text
frontend/src/routes/index.tsx
frontend/src/components/ProjectList.tsx
frontend/src/components/ProjectTable.tsx
frontend/src/lib/api.ts
frontend/src/types/project.ts
```

## TDD Steps

1. Create project type definition.
2. Create API client function.
3. Create ProjectTable component.
4. Create ProjectList component.
5. Create route at `/`.
6. Test with mock data.
7. Verify responsive layout.

## Acceptance Criteria

- Route `/` renders project list.
- Projects fetched from `/api/v1/projects`.
- Table displays: name, status, created_at.
- Responsive layout (mobile, tablet, desktop).
- Loading state shown while fetching.
- Error state shown on failure.
- Empty state shown when no projects.
- TypeScript strict mode passes.
- `npm run build` succeeds.

## Expected test

```tsx
// frontend/src/components/ProjectTable.test.tsx
import { render, screen } from '@testing-library/react';
import { ProjectTable } from './ProjectTable';

const mockProjects = [
  {
    id: '1',
    name: 'Test Project',
    status: 'active',
    created_at: '2026-07-24T10:00:00Z',
  },
];

test('renders project name', () => {
  render(<ProjectTable projects={mockProjects} />);
  expect(screen.getByText('Test Project')).toBeInTheDocument();
});
```

## DoD

- component created;
- route added;
- build passes;
- responsive layout verified.