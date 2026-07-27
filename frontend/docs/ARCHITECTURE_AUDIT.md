# UPCP Component Architecture Audit

**Date**: 2026-07-27
**Scope**: Full frontend codebase analysis (React 19, TypeScript 6, Vite 8, TanStack Query/Router, shadcn/ui)
**Files analyzed**: 80+ source files including all components, hooks, utils, tests, and config

---

## Executive Summary

**Architecture quality score: 7.5 / 10**

The UPCP frontend is a well-structured single-page application with a clear component hierarchy, proper separation of concerns, and consistent patterns throughout. The codebase demonstrates strong fundamentals: good use of TanStack Query for server state, proper lazy loading of route components, a clean API abstraction layer, and a reusable UI primitive library based on shadcn/ui. The main areas for improvement center on eliminating hardcoded sample data, reducing repeated boilerplate across hook files, strengthening type safety in a few areas, and expanding test coverage to business-critical page components.

### Top 3 Strengths

1. **Consistent hook + TanStack Query pattern** -- Every entity (projects, tasks, features, components, modules, subtasks, quality items, reports, git, audit) has a dedicated hook file following the identical `useX` / `useCreateX` / `useUpdateX` / `useDeleteX` pattern with proper cache invalidation. This makes the data layer extremely predictable and easy to maintain.

2. **Solid UI primitive library** -- 15+ custom domain-specific primitives (`StatusBadge`, `PriorityDot`, `AgentAvatar`, `AgentStatusBadge`, `ActorBadge`, `ClarificationBanner`, `ReviewVerdictCard`, `EmptyState`, `ErrorState`, `PageSkeleton`, `ConfirmDialog`, `DataTablePagination`, `SearchInput`, `ShortcutsDialog`, `DataTable`) built on top of shadcn/ui. These encapsulate visual logic cleanly and are used consistently across all pages.

3. **Thoughtful developer experience** -- URL-based pagination (`useUrlPagination`), keyboard shortcuts system (`useHotkeys`), command palette (`cmdk`), skip-to-content link, proper `ErrorBoundary` placement, and a design token system in CSS custom properties that enables clean dark mode support.

### Top 5 Issues

1. **Hardcoded sample/mock data in production components** -- `LiveActivityFeed.tsx` and `AgentActivitySummary.tsx` use hardcoded `SAMPLE_EVENTS` and `SAMPLE_AGENTS` arrays directly in production components. `AttentionCards.tsx` also has hardcoded items. These bypass the API layer entirely.

2. **Duplicated projectId extraction pattern** -- The `useMemo` + `location.pathname.match()` pattern for extracting `projectId` is copied verbatim in 7 components (`DeliveryPage`, `StructurePage`, `QualityPage`, `GitIntegrationPage`, `ReportsPage`, `CommandPalette`, `Dashboard`). The `useProjectId` hook exists but is only used in `ProjectDetail` and `AuditPage`.

3. **`api.ts` is a 300+ line monolith** -- The API file contains every endpoint function for every entity (projects, components, modules, features, tasks, subtasks, acceptance criteria, DoD items, reports, audit events, dashboard, quality, health, search, git providers, git branches, git commits, git links). This should be split by domain.

4. **Test coverage gaps for page-level components** -- `ProjectList`, `ProjectTable`, `LoginPage`, `SetupPage`, `ReportsPage`, `TopBar`, `AppShell`, `AppSidebar`, and `BreadcrumbBar` have no tests. The existing tests cover UI primitives and a few key pages well, but business-critical auth and navigation flows are untested.

5. **Inconsistent tab routing in `ProjectDetail`** -- The "Settings" tab renders `<ReportsPage />` (line 146: `<TabsContent value="settings">` maps to `ReportsPage`), and `TAB_ROUTES` maps `settings` to the settings key but the actual settings route renders `NotFoundPage`. This is a bug or a confusing naming mismatch.

---

## Component Architecture Analysis

### `src/main.tsx` (18 lines)
- **Status**: Clean
- Creates `QueryClient` with default options (no customization -- see Performance section)
- Proper provider nesting: `StrictMode > QueryClientProvider > ThemeProvider > RouterProvider`
- **Issue**: `QueryClient` is created at module level outside the component, which is correct, but no `defaultOptions` are configured for stale time or retry behavior

### `src/router.tsx` (166 lines)
- **Status**: Good, with minor issues
- All route components are properly lazy-loaded with `React.lazy`
- `LazyRoute` wrapper provides `ErrorBoundary` + `Suspense` for every route -- good pattern
- **Issue**: Multiple routes (`projectStructureRoute`, `projectDeliveryRoute`, `projectQualityRoute`, `projectAuditRoute`, `projectGitRoute`, `projectSettingsRoute`) all render `<ProjectDetail />` -- the routing is handled internally via tabs rather than via the router. This means the URL changes but the same component remounts or navigates internally, which can cause unnecessary re-renders and makes the tab system do double duty with the router.
- **Issue**: `AuthGuard` uses `window.location.href = '/login'` instead of TanStack Router's `navigate`. This causes a full page reload and loses all client state.
- **Issue**: `settingsRoute` renders `NotFoundPage` -- either settings should be implemented or the route should redirect.

### `src/contexts/AuthContext.tsx` (74 lines)
- **Status**: Good
- Proper token refresh flow with fallback to logout
- Uses `safeStorage` abstraction -- good
- **Issue**: `loadUser` catches all errors silently. If `/auth/me` returns a 500 (server error), it will attempt a refresh unnecessarily. Should distinguish 401 from other errors.
- **Issue**: No automatic token refresh on interval or before expiry. The token is only refreshed when `loadUser` fails on mount.

### `src/lib/api.ts` (310 lines)
- **Status**: Needs decomposition
- Core `apiRequest` function is solid with proper auth headers, 401 handling, and error parsing
- **Issue**: File exceeds 300 line limit (AGENTS.md rule). Should be split into `api/projects.ts`, `api/tasks.ts`, `api/quality.ts`, `api/git.ts`, etc.
- **Issue**: `paginationParams` function uses manual string building instead of `URLSearchParams` (which is used correctly in `fetchAuditEvents` nearby -- inconsistency)
- **Issue**: `SearchResult` interface is defined inline in `api.ts` instead of in a types file
- **Issue**: No request deduplication or abort controller support. If a user navigates away mid-request, the request continues.

### `src/lib/auth.ts` (59 lines)
- **Status**: Clean
- `AuthUser` and `AuthTokens` interfaces are well-defined
- Duplicates the `authRequest` pattern from `api.ts` -- could share the base fetch logic
- **Issue**: No retry logic for transient failures

### `src/lib/storage.ts` (82 lines)
- **Status**: Good
- localStorage -> cookie -> memory fallback chain is a solid defensive pattern
- **Issue**: Cookies do not set `Secure` flag, which means tokens are sent over HTTP in dev. Acceptable for development but should be flagged for production hardening.

### `src/components/layouts/AppShell.tsx` (50 lines)
- **Status**: Clean
- Good accessibility: skip-to-content link
- Proper composition of sidebar, topbar, breadcrumbs, main content, and overlays
- Hotkey bindings are well-organized

### `src/components/layouts/AppSidebar.tsx` (92 lines)
- **Status**: Good
- Uses `NAV_GROUPS` and `PROJECT_NAV_GROUP` from constants -- clean
- Context-aware: shows project nav group only when on a project route
- **Issue**: Uses regex `isProjectRoute` directly instead of TanStack Router's match system

### `src/components/layouts/TopBar.tsx` (87 lines)
- **Status**: Good with issues
- **Issue**: Notification badge is hardcoded to "3" -- should be dynamic or hidden when zero
- **Issue**: Avatar image path `/avatars/user.jpg` is hardcoded -- should use user data from auth context
- **Issue**: Logout menu item has `className="text-destructive"` but no `onClick` handler -- it does nothing
- **Issue**: Profile and Settings menu items also have no click handlers

### `src/components/layouts/BreadcrumbBar.tsx` (64 lines)
- **Status**: Clean
- UUID detection for skipping path segments is smart
- `SEGMENT_LABELS` map for human-readable labels
- No issues found

### `src/components/Dashboard.tsx` (127 lines)
- **Status**: Good
- Proper loading/error/empty state handling
- `StatCard` is well-componentized
- Uses attention dashboard sections, live activity feed, and agent summary
- **Issue**: Empty state action `onClick: () => {}` does nothing -- should open create dialog or navigate

### `src/components/dashboard/AttentionCards.tsx` (120 lines)
- **Status**: Needs work
- `AttentionSection` generic component is well-designed
- **Critical Issue**: `NeedsReviewSection`, `OpenClarificationsSection`, `BlockedTasksSection`, `StaleAgentsSection`, and `FailedQualityGatesSection` all contain hardcoded mock data. Two sections have static items with fake IDs (`proj-1`) and three return empty arrays. These should fetch real data from the API.
- **Issue**: No loading states for these sections

### `src/components/dashboard/LiveActivityFeed.tsx` (82 lines)
- **Status**: Needs work
- **Critical Issue**: Uses hardcoded `SAMPLE_EVENTS` array with fake timestamps generated via `Date.now()`. This component always shows the same 3 events regardless of actual system state. Must be replaced with API data.

### `src/components/dashboard/AgentActivitySummary.tsx` (68 lines)
- **Status**: Needs work
- **Critical Issue**: Same as above -- hardcoded `SAMPLE_AGENTS` array. Always shows the same 3 agents.
- **Issue**: All agent links go to `/projects` instead of agent-specific pages

### `src/components/ProjectList.tsx` (102 lines)
- **Status**: Good
- Proper pagination with `useUrlPagination`
- Good loading/error/empty states
- Entity form dialog for creation
- **Issue**: `PROJECT_FIELDS` constant is duplicated -- also defined in `ProjectDetail.tsx`. Should use the shared `projectFields` from `entity-fields.ts`.

### `src/components/ProjectTable.tsx` (52 lines)
- **Status**: Clean
- Simple, focused component
- Uses TanStack Router navigation properly
- No issues

### `src/components/project/ProjectDetail.tsx` (160 lines)
- **Status**: Good with issues
- Good edit/delete functionality with confirmation dialog
- **Issue**: Tab label mismatch -- the 7th tab has `value="settings"` but its label says "Reports" and it renders `<ReportsPage />`. This is confusing.
- **Issue**: `PROJECT_FIELDS` is duplicated from `ProjectList.tsx` and `entity-fields.ts`
- **Issue**: `TAB_ROUTES` mapping includes `settings` but not `reports`, yet the actual tab renders reports
- **Issue**: Does not use `useProjectId` hook (exists but not used here) -- extracts ID inline

### `src/components/project/DeliveryPage.tsx` (221 lines)
- **Status**: Good
- Feature sections with expandable task lists
- Board view toggle
- Task creation inline
- **Issue**: Extracts `projectId` via `useMemo` + regex instead of using `useProjectId` hook
- **Issue**: `FeatureSection` sub-component (108 lines) is large and handles multiple concerns (display, task loading, task creation, deletion). Could be split.

### `src/components/project/StructurePage.tsx` (184 lines)
- **Status**: Good
- Expandable component cards with nested module tables
- **Issue**: Same `projectId` extraction pattern (duplicated)
- **Issue**: `ComponentCard` sub-component could be extracted to its own file

### `src/components/project/QualityPage.tsx` (77 lines)
- **Status**: Clean
- Good use of progress bars and stat cards
- **Issue**: Same `projectId` extraction pattern (duplicated)

### `src/components/project/AuditPage.tsx` (103 lines)
- **Status**: Good
- Uses `useProjectId` hook (one of only two components that do)
- Proper filter selects with pagination
- **Issue**: Native `<select>` elements instead of shadcn `Select` component -- inconsistent with the rest of the UI

### `src/components/project/GitIntegrationPage.tsx` (136 lines)
- **Status**: Good
- `ProviderCard` sub-component is clean
- **Issue**: Same `projectId` extraction pattern (duplicated)

### `src/components/project/ReportsPage.tsx` (136 lines)
- **Status**: Good
- Report generation and markdown export
- **Issue**: `handleExportMarkdown` uses `fetch` directly instead of the `apiRequest` wrapper -- bypasses auth token injection. If the API requires auth, this will fail.

### `src/components/project/BoardView.tsx` (211 lines)
- **Status**: Good
- DnD with `@dnd-kit/core` is properly implemented
- `useQueries` for loading tasks across all features
- Good drag overlay
- **Issue**: The `closestCenter` collision detection may not be ideal for a Kanban board -- `closestCorners` is typically better for vertical lists

### `src/components/project/TaskDetailSheet.tsx` (285 lines)
- **Status**: Needs refactoring
- Most complex component in the codebase
- **Issue**: Exceeds 300 line guidance (borderline). The execution tab section (lines 133-215) contains hardcoded mock data for agent activity, clarifications, reviews, evidence, and git links. These should all use real API data.
- **Issue**: `ListSection` generic helper is defined at the bottom of the file -- should be in UI primitives
- **Issue**: The `key={item.id ?? Math.random()}` fallback in `ListSection` is a React anti-pattern -- it forces remounts on every render if IDs are missing

### `src/components/CommandPalette.tsx` (165 lines)
- **Status**: Good
- Combines static navigation with server-side search
- Recent items in localStorage
- **Issue**: Uses `localStorage` directly instead of `safeStorage` for recent commands
- **Issue**: Duplicate Ctrl+K handler -- `AppShell` also binds Ctrl+K via `useHotkeys`. Both fire, though the palette handles it correctly.

### `src/components/ErrorBoundary.tsx` (48 lines)
- **Status**: Clean
- Class component as required by React for error boundaries
- Proper `getDerivedStateFromError` and `componentDidCatch`
- Simple reload fallback

### `src/components/HealthPage.tsx` (65 lines)
- **Status**: Good
- **Issue**: Database status card always shows "Connected" with a green check -- this is hardcoded, not derived from the health API response. If the database is down, the UI still shows it as connected.

### `src/components/NotFoundPage.tsx` (32 lines)
- **Status**: Clean
- No issues

### `src/components/auth/LoginPage.tsx` (67 lines)
- **Status**: Good
- **Issue**: Uses `window.location.href = '/'` after login instead of TanStack Router navigation. Causes full page reload.

### `src/components/auth/SetupPage.tsx` (75 lines)
- **Status**: Good
- Same `window.location.href` issue as LoginPage

### `src/components/forms/EntityFormDialog.tsx` (132 lines)
- **Status**: Good
- Reusable form dialog with validation
- Auto-slug generation is a nice touch
- Proper error handling and loading states

### `src/components/forms/entity-fields.ts` (99 lines)
- **Status**: Good
- Shared field definitions for all entities
- **Issue**: `projectFields` here duplicates `PROJECT_FIELDS` in both `ProjectList.tsx` and `ProjectDetail.tsx`

---

## Type Safety Assessment

**Score: 8 / 10**

### Strengths
- All API functions have explicit return types (`Promise<T>`)
- All hook return types are inferred correctly from TanStack Query
- Props interfaces are defined for all components
- Type imports use `import type` syntax properly
- TanStack Router module augmentation for type-safe routes

### Issues
- **`any` usage in tests**: Multiple test files use `as any` casts (e.g., `Dashboard.test.tsx` lines with `mockUseDashboardStats.mockReturnValue({...} as any)`). While understandable for mocking, this hides type mismatches.
- **`Record<string, string>` for form data**: `EntityFormDialog.onSubmit` passes `Record<string, string>` which loses field-level type information. Could be generic.
- **Missing `$projectId` param typing**: TanStack Router routes define `$projectId` path param but components extract it from URL via regex instead of using `useParams()` which would be type-safe.
- **`api.ts` `paginationParams`**: Returns `string` with manual concatenation -- not type-checked against URL structure.

---

## Code Quality Assessment

**Score: 7 / 10**

### Function Length Violations (>40 lines)
| File | Function | Lines | Notes |
|------|----------|-------|-------|
| `BoardView.tsx` | `BoardView` | ~120 | Complex but well-structured with memos |
| `TaskDetailSheet.tsx` | `TaskDetailSheet` | ~170 | Should be decomposed |
| `CommandPalette.tsx` | `CommandPalette` | ~100 | Acceptable for orchestration |
| `Dashboard.tsx` | `Dashboard` | ~90 | Template-heavy, acceptable |
| `DataTablePagination.tsx` | `DataTablePagination` | ~70 | UI-heavy, acceptable |
| `DeliveryPage.tsx` | `DeliveryPage` | ~100 | Template-heavy |
| `FeatureSection` (in DeliveryPage) | ~100 | Should be its own file |

### DRY Violations
1. **`projectId` extraction** -- `useMemo(() => { const match = location.pathname.match(...); ... })` duplicated in 7 files. `useProjectId` hook exists but is underused.
2. **`PROJECT_FIELDS`** -- Defined in `ProjectList.tsx`, `ProjectDetail.tsx`, and `entity-fields.ts` (3 copies).
3. **Error/loading/empty state triad** -- Every page repeats the same `if (isLoading) return <PageSkeleton />; if (error) return <ErrorState />; if (!data?.length) return <EmptyState />` pattern. Could be abstracted into a `DataPage` wrapper.
4. **Native `<select>` vs shadcn `Select`** -- `AuditPage.tsx` and `TaskDetailSheet.tsx` use native `<select>` while `DataTablePagination.tsx` uses the shadcn `Select`. Should be consistent.

### Magic Strings/Numbers
- Notification count `3` hardcoded in `TopBar.tsx`
- Agent heartbeat display `5 min ago`, `30s ago` hardcoded in `TaskDetailSheet.tsx`
- `debounceMs = 300` default in `SearchInput.tsx` (acceptable as a default)
- Status strings (`'backlog'`, `'in-progress'`, `'review'`, `'done'`) used in multiple places without constants

### Dead Code
- `HOTKEYS` constant in `constants.ts` defines hotkey bindings but is never imported -- `AppShell.tsx` defines its own inline bindings
- `useReport` and `useAcceptanceCriterion` and `useDoDItem` and `useSubtask` (singular) hooks exist but are never used
- `useComponent` (singular) hook exists but is never used
- `updateGitProvider` and `updateGitBranch` functions are absent from the API, meaning the hooks correctly don't expose them, but the git provider card has no edit capability

---

## Testing Assessment

**Score: 6.5 / 10**

### Test Coverage Map

| Component | Has Tests | Quality |
|-----------|-----------|---------|
| `StatusBadge` | Yes | Good -- color, label, fallback |
| `PriorityDot` | Yes | -- |
| `DataTablePagination` | Yes | -- |
| `ConfirmDialog` | Yes | -- |
| `EmptyState` | Yes | -- |
| `ErrorState` | Yes | -- |
| `PageSkeleton` | Yes | -- |
| `Dashboard` | Yes | Good -- loading, error, empty, data, recent |
| `CommandPalette` | Yes | Good -- render, filter, navigate, project commands |
| `ErrorBoundary` | Yes | Good -- render, fallback, console log |
| `EntityFormDialog` | Yes | Good -- validation, submit, slug, select |
| `BoardView` | Yes | Good -- columns, drag, filter, click |
| `HealthPage` | Yes | -- |
| `NotFoundPage` | Yes | -- |
| `AuditPage` | Yes | -- |
| `DeliveryPage` | Yes | -- |
| `GitIntegrationPage` | Yes | -- |
| `QualityPage` | Yes | -- |
| `StructurePage` | Yes | -- |
| `ProjectDetail` | Yes | -- |
| `useUrlPagination` | Yes | Good -- defaults, URL read, update |
| `showToast` | Yes | Good -- all methods |

### Missing Tests (Critical)
- `LoginPage` -- No test for authentication flow
- `SetupPage` -- No test for initial setup flow
- `ProjectList` -- No test for list + create
- `ProjectTable` -- No test for table rendering
- `AppShell` -- No test for layout composition
- `AppSidebar` -- No test for nav rendering
- `TopBar` -- No test for theme toggle, search, user menu
- `BreadcrumbBar` -- No test for breadcrumb generation
- `AuthContext` -- No test for token refresh flow
- `api.ts` -- No test for API functions
- `auth.ts` -- No test for auth functions
- `storage.ts` -- No test for fallback chain
- `useHotkeys` -- No test for keyboard shortcuts
- `format.ts` -- No test for `formatRelativeTime`

### Test Quality Issues
- `Dashboard.test.tsx` imports `useProjects` mock but `Dashboard.tsx` does not use `useProjects` directly -- the mock is unnecessary
- Heavy use of `as any` in mock return values
- No integration tests that exercise full page flows (login -> dashboard -> project -> task)

---

## Performance Assessment

**Score: 7.5 / 10**

### Strengths
- All route components are lazy-loaded via `React.lazy`
- `useMemo` is used appropriately in `BoardView` for filtering/grouping
- `useCallback` is used in `useHotkeys`, `AuthContext`, and `AppShell`
- `useUrlPagination` returns memoized values
- `SearchInput` has proper debounce (300ms default)
- `useDashboardStats` has 60s polling interval
- `useHealth` has 30s polling interval

### Concerns
1. **No `QueryClient` stale time configuration** -- Default `staleTime: 0` means every mount refetches. For a dashboard that re-renders on theme toggle or sidebar collapse, this causes unnecessary network requests. Should set `staleTime: 30_000` or similar.
2. **No `gcTime` (garbage collection time) tuning** -- Default is 5 minutes, which is fine, but explicit configuration shows intent.
3. **`BoardView` fires N queries via `useQueries`** -- One per feature. For projects with many features, this creates a burst of parallel requests. Consider a single `/features/{id}/tasks` aggregated endpoint.
4. **`TaskDetailSheet` always mounts all tab content** -- Even tabs the user hasn't clicked are rendered (though hidden). TanStack components handle this correctly, but the `useAcceptanceCriteria`, `useDoDItems`, and `useSubtasks` hooks all fire immediately regardless of which tab is active.
5. **No code splitting beyond route level** -- `@dnd-kit/core` (used only in `BoardView`) is loaded on every route because it's bundled with the main chunk. Should be dynamically imported.
6. **`formatRelativeTime` does not use `useMemo` or caching** -- Called on every render for each activity item. For lists with many items, this recalculates on every re-render.

---

## Dependency Assessment

**Score: 8 / 10**

### Runtime Dependencies
| Package | Used? | Notes |
|---------|-------|-------|
| `react` / `react-dom` | Yes | Core |
| `@tanstack/react-query` | Yes | Server state management -- excellent usage |
| `@tanstack/react-router` | Yes | Routing -- good but underutilized (regex instead of params) |
| `@tanstack/react-router-devtools` | Yes | Dev only |
| `next-themes` | Yes | Theme management -- works well |
| `@dnd-kit/core` | Yes | Drag and drop -- only used in BoardView |
| `@base-ui/react` | Partial | Used by shadcn/ui base-nova style |
| `@radix-ui/react-slot` | Yes | Used by Button |
| `cmdk` | Yes | Command palette |
| `lucide-react` | Yes | Icons -- used consistently |
| `sonner` | Yes | Toast notifications |
| `shadcn` | Yes | CLI for adding components |
| `class-variance-authority` | Yes | Component variants |
| `clsx` / `tailwind-merge` | Yes | Class name utilities |
| `tw-animate-css` | Yes | Animation utilities |
| `@fontsource-variable/geist` | Yes | Font |

### Dev Dependencies
All appropriate and modern versions. No unused dev dependencies detected.

### Potential Additions
- Consider `@tanstack/react-router` `useParams()` to replace regex-based param extraction
- Consider `zod` for runtime form validation (currently manual)

---

## Naming Conventions Assessment

**Score: 9 / 10**

### Strengths
- **Files**: kebab-case for hooks (`use-projects.ts`), PascalCase for components (`ProjectList.tsx`) -- consistent
- **Components**: PascalCase throughout -- correct
- **Hooks**: `use` prefix consistently applied
- **Constants**: UPPER_SNAKE_CASE for exports (`NAV_GROUPS`, `STATUS_COLORS`)
- **Types**: PascalCase interfaces (`AuthUser`, `FormField`)
- **CSS**: BEM-like utility classes, consistent custom property naming

### Minor Issues
- `constants.ts` exports `HOTKEYS` but it's never used (dead code)
- `api.ts` function names are inconsistent: `fetchProjects` vs `searchGlobal` vs `completeTask` -- some use `fetch`, some use action verbs

---

## Separation of Concerns Assessment

**Score: 8 / 10**

### Strengths
- API layer (`lib/api.ts`) cleanly separates HTTP from components
- Auth layer (`lib/auth.ts`) is separate from general API
- Hooks layer provides data access abstraction
- UI primitives are in `components/ui/`
- Domain pages are in `components/project/`
- Layout components are in `components/layouts/`
- Form field definitions are in `components/forms/entity-fields.ts`

### Issues
- **Business logic in components**: `DeliveryPage.tsx` and `StructurePage.tsx` contain data transformation logic that could live in hooks
- **Duplicate data**: `PROJECT_FIELDS` in three places
- **Mock data in components**: `LiveActivityFeed`, `AgentActivitySummary`, `AttentionCards` mix data with presentation

---

## Refactoring Recommendations

### Priority 1: Critical

#### 1.1 Replace hardcoded mock data with API calls
**Files**: `LiveActivityFeed.tsx`, `AgentActivitySummary.tsx`, `AttentionCards.tsx`, `TaskDetailSheet.tsx` (execution tab)
**Impact**: Functional correctness -- these components currently show fake data to users
**Approach**:
- Create `useActivityFeed`, `useAgents`, `useAttentionItems` hooks
- Add corresponding API endpoints if they don't exist
- Show loading skeletons and empty states instead of fake data

#### 1.2 Fix `TopBar.tsx` logout handler
**File**: `src/components/layouts/TopBar.tsx`
**Impact**: Logout button does nothing
**Approach**: Import `useAuth`, call `logout()` on click, navigate to `/login`

#### 1.3 Fix `HealthPage.tsx` database status
**File**: `src/components/HealthPage.tsx`
**Impact**: Misleading health information
**Approach**: Remove the hardcoded "Connected" database card or derive its status from the health API response

#### 1.4 Fix `ReportsPage.tsx` markdown export auth
**File**: `src/components/project/ReportsPage.tsx`
**Impact**: Export will fail if API requires authentication
**Approach**: Use `apiRequest` wrapper or include auth headers manually

### Priority 2: High

#### 2.1 Use `useProjectId` hook everywhere
**Files**: `DeliveryPage.tsx`, `StructurePage.tsx`, `QualityPage.tsx`, `GitIntegrationPage.tsx`, `ReportsPage.tsx`, `CommandPalette.tsx`, `Dashboard.tsx`
**Impact**: DRY, type safety, single source of truth
**Approach**: Replace all `useMemo(() => location.pathname.match(...)` with `const projectId = useProjectId()`

#### 2.2 Split `api.ts` by domain
**File**: `src/lib/api.ts` (310 lines)
**Impact**: Maintainability, adherence to file size limits
**Approach**: Create `api/projects.ts`, `api/tasks.ts`, `api/quality.ts`, `api/reports.ts`, `api/git.ts`, `api/search.ts`, `api/dashboard.ts`. Keep `api/core.ts` with `apiRequest` and shared utilities.

#### 2.3 Consolidate `PROJECT_FIELDS` duplication
**Files**: `ProjectList.tsx`, `ProjectDetail.tsx`, `entity-fields.ts`
**Impact**: DRY
**Approach**: Use `projectFields` from `entity-fields.ts` everywhere. Delete local copies.

#### 2.4 Fix `ProjectDetail` tab/routing mismatch
**File**: `src/components/project/ProjectDetail.tsx`
**Impact**: Confusing UX -- "Settings" tab shows reports
**Approach**: Either rename the tab to "Reports" with `value="reports"` or implement actual project settings

#### 2.5 Add missing tests for critical paths
**Files**: `LoginPage`, `SetupPage`, `AuthContext`, `api.ts`, `storage.ts`, `TopBar`, `AppSidebar`
**Impact**: Confidence in auth flows and core infrastructure
**Approach**: Start with `AuthContext` and `LoginPage` as they gate all other functionality

### Priority 3: Medium

#### 3.1 Configure `QueryClient` defaults
**File**: `src/main.tsx`
**Impact**: Performance -- reduce unnecessary refetches
**Approach**: Set `staleTime: 30_000`, `retry: 1` (or 2), and `refetchOnWindowFocus: false` for non-critical queries

#### 3.2 Use TanStack Router params instead of regex
**Files**: All components extracting `projectId` from URL
**Impact**: Type safety, cleaner code
**Approach**: Use `useParams({ from: '/projects/$projectId' })` from TanStack Router

#### 3.3 Use `safeStorage` in `CommandPalette.tsx`
**File**: `src/components/CommandPalette.tsx`
**Impact**: Consistency with storage abstraction
**Approach**: Replace `localStorage.getItem/setItem` with `safeStorage.getItem/setItem`

#### 3.4 Replace native `<select>` with shadcn `Select`
**Files**: `AuditPage.tsx`, `TaskDetailSheet.tsx`
**Impact**: Visual consistency
**Approach**: Use `<Select>` from `@/components/ui/select`

#### 3.5 Extract `ListSection` to UI primitives
**File**: `src/components/project/TaskDetailSheet.tsx`
**Impact**: Reusability
**Approach**: Move to `src/components/ui/ListSection.tsx`

#### 3.6 Remove dead code
**Files**: Remove unused hooks (`useReport`, `useAcceptanceCriterion`, `useDoDItem`, `useSubtask`, `useComponent`), remove unused `HOTKEYS` constant, remove unused `useProjects` mock from `Dashboard.test.tsx`

#### 3.7 Add token auto-refresh
**File**: `src/contexts/AuthContext.tsx`
**Impact**: Better UX -- prevents sudden logouts
**Approach**: Decode JWT expiry, set a timer to refresh 60 seconds before expiry

#### 3.8 Lazy-load `@dnd-kit/core` in `BoardView`
**File**: `src/components/project/BoardView.tsx`
**Impact**: Bundle size -- dnd-kit is only needed for the board view
**Approach**: Dynamic import or separate chunk via Vite manual chunks config

---

## Component Map

### Layout Hierarchy
```
main.tsx
  QueryClientProvider
    ThemeProvider
      RouterProvider
        AuthProvider (root route)
          AppShell
            TooltipProvider
              SidebarProvider
                [skip-to-content link]
                AppSidebar
                  SidebarHeader (UPCP logo)
                  SidebarContent
                    NAV_GROUPS (Main, System)
                    PROJECT_NAV_GROUP (conditional)
                  SidebarRail
                SidebarInset
                  TopBar
                    SidebarTrigger
                    Search button
                    ThemeToggle
                    Notifications
                    User dropdown
                  Separator
                  BreadcrumbBar
                  ErrorBoundary
                    main#main-content
                      <Outlet /> (route content)
                Toaster (sonner)
                CommandPalette
                ShortcutsDialog
```

### Route Components (lazy-loaded)
```
/                   -> Dashboard
/projects           -> ProjectList
/projects/$id       -> ProjectDetail (tabs: overview, structure, delivery, quality, audit, git, settings)
/projects/$id/*     -> ProjectDetail (same component, different active tab)
/reports            -> ReportsPage
/settings           -> NotFoundPage (placeholder)
/health             -> HealthPage
/login              -> LoginPage
/setup              -> SetupPage
*                   -> NotFoundPage
```

### Page Components
```
Dashboard
  StatCard (x4)
  NeedsReviewSection -> AttentionSection
  OpenClarificationsSection -> AttentionSection
  BlockedTasksSection -> AttentionSection
  StaleAgentsSection -> AttentionSection
  FailedQualityGatesSection -> AttentionSection
  LiveActivityFeed
  AgentActivitySummary
  Recent Projects list

ProjectList
  ProjectTable
  DataTablePagination
  EntityFormDialog

ProjectDetail
  StructurePage -> ComponentCard -> module table
  DeliveryPage -> FeatureSection -> task table
    BoardView -> DraggableTaskCard + DroppableColumn
    TaskDetailSheet -> tabs (Details, Execution, AC, DoD, Subtasks)
  QualityPage -> stat cards + progress bars
  AuditPage -> timeline
  GitIntegrationPage -> ProviderCard -> branches + commits
  ReportsPage -> report table + generate/export
```

### UI Primitives (15 domain-specific + shadcn/ui base)
```
StatusBadge         -- Status-colored badge with dot
PriorityDot         -- Priority indicator dot with tooltip
AgentAvatar         -- Avatar with status dot and pulse
AgentStatusBadge    -- Agent status colored badge
ActorBadge          -- Agent/Human/System actor badge
ClarificationBanner -- Clarification question banner
ReviewVerdictCard   -- Review approval/rejection card
EmptyState          -- Icon + title + description + CTA
ErrorState          -- Error icon + message + retry
PageSkeleton        -- Configurable loading skeleton
ConfirmDialog       -- Confirmation dialog with loading
DataTablePagination -- Full pagination controls
SearchInput         -- Debounced search with clear
ShortcutsDialog     -- Keyboard shortcuts reference
DataTable           -- Generic data table
PageHeader          -- Page header primitive
```

### Hooks (18 total)
```
use-projects       -- CRUD for projects
use-project-id     -- Extract projectId from URL
use-components     -- CRUD for components
use-modules        -- CRUD for modules
use-features       -- CRUD for features
use-tasks          -- CRUD for tasks + completeTask
use-subtasks       -- CRUD for subtasks
use-quality        -- CRUD for acceptance criteria + DoD items
use-quality-stats  -- Quality statistics
use-reports        -- CRUD for reports
use-audit          -- Audit events + create
use-git            -- Git providers, branches, commits
use-dashboard      -- Dashboard statistics (60s polling)
use-health         -- Health status (30s polling)
use-url-pagination -- URL-based pagination state
use-hotkeys        -- Keyboard shortcut bindings
use-mobile         -- Mobile breakpoint detection
```

### Data Flow
```
Component -> useXxx hook -> useQuery/useMutation -> api.ts functions -> fetch() -> Backend
                                            |
                                    QueryClient cache
                                            |
                                    invalidateQueries (on mutation)
```
