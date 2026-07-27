# TASK-0026: Type Definitions + API Client Expansion + TanStack Query Hooks

Spec: SPEC-0012 (Frontend UI/UX Architecture)
Status: done
Priority: 10
Model: routine
Milestone: M5

## Goal

Define all TypeScript types matching backend models. Expand API client with functions for every entity. Create TanStack Query hooks for data fetching and mutations.

## Non-goals

- No UI components (handled by other tasks).
- No route definitions (handled by page tasks).

## Backend API endpoints

```text
Projects:    GET/POST /projects, GET/PATCH/DELETE /projects/:id
Components:  GET/POST /projects/:id/components, GET/PATCH/DELETE /components/:id
Modules:     GET/POST /components/:id/modules, GET/PATCH/DELETE /modules/:id
Features:    GET/POST /projects/:id/features, GET/PATCH/DELETE /features/:id
Tasks:       GET/POST /features/:id/tasks, GET/PATCH/DELETE /tasks/:id
Subtasks:    GET/POST /tasks/:id/subtasks, GET/PATCH/DELETE /subtasks/:id
AC:          GET/POST /tasks/:id/acceptance-criteria, GET/PATCH/DELETE /acceptance-criteria/:id
DoD:         GET/POST /tasks/:id/dod-items, GET/PATCH/DELETE /dod-items/:id
Audit:       GET /audit-events (with filters)
Reports:     GET/POST /projects/:id/reports, GET /reports/:id
Health:      GET /health
```

## Files involved

```text
frontend/src/types/project.ts               (extend existing)
frontend/src/types/component.ts             (new)
frontend/src/types/module.ts                (new)
frontend/src/types/feature.ts               (new)
frontend/src/types/task.ts                  (new)
frontend/src/types/subtask.ts               (new)
frontend/src/types/quality.ts               (new — AC + DoD)
frontend/src/types/audit.ts                 (new)
frontend/src/types/report.ts                (new)
frontend/src/types/api.ts                   (new — PaginatedResponse, etc.)
frontend/src/lib/api.ts                     (expand)
frontend/src/hooks/use-projects.ts          (new)
frontend/src/hooks/use-components.ts        (new)
frontend/src/hooks/use-modules.ts           (new)
frontend/src/hooks/use-features.ts          (new)
frontend/src/hooks/use-tasks.ts             (new)
frontend/src/hooks/use-subtasks.ts          (new)
frontend/src/hooks/use-quality.ts           (new)
frontend/src/hooks/use-audit.ts             (new)
frontend/src/hooks/use-reports.ts           (new)
frontend/src/hooks/use-health.ts            (new)
```

## TDD Steps

1. Read backend schemas (Pydantic models) to understand exact field names and types.
2. Create type definitions for all entities.
3. Create `PaginatedResponse<T>` generic type.
4. Expand `api.ts` with typed functions for all endpoints.
5. Create TanStack Query hooks for each entity (useQuery + useMutation).
6. Test that types compile without errors.
7. Test that API functions return correct types.
8. Verify `npm run build` passes.

## Acceptance Criteria

- TypeScript types exist for: Project, Component, Module, Feature, Task, Subtask, AcceptanceCriterion, DoDItem, AuditEvent, Report.
- Types match backend Pydantic schemas (field names, types, optionality).
- `api.ts` has functions for all 61 backend endpoints.
- Each API function has proper TypeScript typing (params, return type).
- TanStack Query hooks exist for each entity.
- Hooks use proper cache invalidation (onSuccess invalidates related queries).
- `PaginatedResponse<T>` generic type is used for list endpoints.
- No `any` types in new code.
- `npm run build` succeeds with no TypeScript errors.

## Expected test

```tsx
// frontend/src/hooks/use-projects.test.tsx
import { renderHook, waitFor } from '@testing-library/react';
import { useProjects } from './use-projects';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

test('useProjects returns project list', async () => {
  const queryClient = new QueryClient();
  const wrapper = ({ children }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
  const { result } = renderHook(() => useProjects(), { wrapper });
  await waitFor(() => result.current.isSuccess);
  expect(result.current.data).toBeDefined();
});
```

## DoD

- all type definitions created;
- API client expanded for all endpoints;
- TanStack Query hooks created;
- types match backend schemas;
- no TypeScript errors;
- build passes;
- task file status updated;
- `PROJECT_STATUS.md` updated.
