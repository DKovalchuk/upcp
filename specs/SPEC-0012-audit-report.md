# SPEC-0012 Audit Report

**Date**: 2026-07-24
**Auditor**: Reviewer Agent
**Status**: Draft — NOT ready for implementation beyond Phase 1

---

## Critical Gaps (must fix before Phase 2)

| ID | Gap | Impact | Recommendation |
|----|-----|--------|----------------|
| C1 | **Audit page has no backend support** | AuditService only has `log_event()`, no `list_events()`. No API route exists. TASK-0032 unimplementable. | Add `GET /api/v1/projects/{id}/audit-events` with filters + pagination. Create backend task first. |
| C2 | **No Quality statistics aggregation endpoint** | Quality page needs project-level stats (total ACs, pass rate). Current endpoints only list per-task. N+1 client-side queries required. | Add `GET /api/v1/projects/{id}/quality/stats` returning aggregated stats. |
| C3 | **No Dashboard statistics or activity feed endpoint** | Dashboard needs project count, task counts by status, recent activity. No single endpoint provides this. | Add `GET /api/v1/dashboard/stats` returning aggregated dashboard data. |
| C4 | **Missing `slug` field in frontend Project type** | Backend `ProjectResponse` always returns `slug`. Frontend type omits it. Runtime mismatch. | Add `slug: string` to Project interface. |
| C5 | **No 404 route defined** | Unknown paths show blank page. | Add `*` catch-all route with NotFoundPage. |

## Missing Features (should add)

| ID | Feature | Details | Recommendation |
|----|---------|---------|----------------|
| M1 | Global Reports route has no backend | API only has per-project reports, no global `GET /reports`. | Either add global endpoint or scope reports under project. |
| M2 | No Subtask UI specification | Backend has full Subtask CRUD (5 endpoints). Spec mentions subtasks nowhere. | Add subtask list in Task Detail panel. |
| M3 | No Git integration pages | Gitread context has 5 models, 8 endpoints. Spec has zero Git-related UI. | Add Git provider config to Project Settings. |
| M4 | No Create/Edit form dialogs defined | Spec mentions dialogs generically but no actual form fields, validation, or behavior. | Add form specs per entity: fields, validation, auto-generation (slug from name). |
| M5 | No Delete confirmation UX defined | No specific delete flows: dialog text, post-delete behavior, restore support. | Define pattern: dialog text, toast + refetch, hard delete only. |
| M6 | No project list counts for Components/Tasks | ProjectResponse has no counts. API needs aggregation. | Add counts to ProjectResponse or separate stats endpoint. |
| M7 | No pagination UI specification | API returns paginated responses but no spec for pagination component, page size, URL sync. | Define per list: shadcn Pagination, default page size, URL param sync. |
| M8 | Task Detail: route vs slide-over unclear | Is it a route or transient UI? Can it be deep-linked? | Define explicitly: Sheet component, URL does not change. |

## UX Improvements

| ID | Improvement | Recommendation |
|----|-------------|----------------|
| U1 | No toast message specifications | Define catalog: action + entity + outcome pattern. |
| U2 | No form validation message mapping | Map backend constraints to frontend rules (pattern, min/max, required). |
| U3 | No loading skeleton shapes defined | Add ASCII wireframe per page skeleton. |
| U4 | No responsive table behavior | Define per table: horizontal scroll + sticky first column, or card layout. |
| U5 | No empty state messaging per page | Define message + CTA for every list view. |
| U6 | No sidebar contextual state spec | Define: project context active when URL matches `/projects/:id/*`. |
| U7 | No animation/transition spec | Add: page fade 200ms, slide-over 250ms ease-out. |

## Technical Debt

| ID | Debt | Recommendation |
|----|------|----------------|
| T1 | No API client abstraction with auth interceptors | Define centralized HTTP client with auth injection, 401 redirect, retry. |
| T2 | No React Error Boundary specification | Add route-level Error Boundaries with fallback UI. |
| T3 | No lazy loading / code splitting | Define route-level code splitting with React.lazy(). |
| T4 | No TanStack Query configuration specification | Define per-entity cache defaults (staleTime, gcTime, retry). |
| T5 | No optimistic update specification | Define per-mutation: optimistic yes/no, rollback strategy, error handling. |
| T6 | No route parameter type safety | Define UUID validation in route beforeLoad, redirect to 404 on invalid. |
| T7 | No global search specification | Define: search scope, API contract, results UI, keyboard shortcuts. |

## Recommended SPEC-0012 Changes

1. **Section 1.1**: Add routes — `/projects/:id/tasks/:taskId`, `/projects/:id/reports/*`, `/*` (404)
2. **Section 4.1**: Define Dashboard stats API contract
3. **Section 4.2**: Add search, filter, sort, pagination sub-sections
4. **Section 4.4**: Expand with CRUD operations (create/edit/delete dialogs)
5. **Section 4.5**: Add Feature/Task/Subtask CRUD, filters, sort
6. **Section 4.7**: Define Quality stats API contract
7. **Section 4.8**: Define Audit events API contract (missing entirely)
8. **Section 5.1**: Move Sonner to Phase 1
9. **Section 6**: Add toast catalog, form validation rules, optimistic update matrix, skeleton wireframes
10. **Section 7**: Add specifics — skip-to-content, focus trap, live regions, aria-sort
11. **Section 9**: Add decisions for auth, API client, search, Git integration
12. **Add Section 10**: Type Definitions Reference (all interfaces matching backend)
13. **Add Section 11**: API Contract Reference (all endpoints, request/response, status codes)

## Verdict

SPEC-0012 is **not ready for Phase 2**. Three blocking issues:

1. Audit page has no backend support (C1)
2. Quality page has no stats endpoint (C2)
3. Dashboard has no stats/activity API (C3)

Before Phase 2: update SPEC-0012 to Rev A with Critical Gaps (C1-C5) and Missing API contracts (M1, M6, M7).
