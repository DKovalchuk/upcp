# UPCP UI/UX Comprehensive Audit

**Date:** 2026-07-27
**Scope:** Every component, page, layout, hook, and design token in the frontend
**References:** Linear, Vercel Dashboard, Stripe Dashboard, Raycast

---

## Executive Summary

### Overall Quality: 6.5 / 10

The UPCP frontend has a **solid architectural foundation** — TanStack Router/Query, shadcn/ui (base-ui variant), Tailwind CSS 4, next-themes, proper design tokens, keyboard shortcuts, and clean component separation. The bones are professional-grade. However, the execution falls short of Linear/Vercel/Stripe quality in polish, density, responsiveness, and interaction refinement.

### Top 3 Strengths

1. **Comprehensive design token system.** CSS custom properties cover brand colors, status/priority/agent colors, spacing, typography, animation, shadows, radius, and dark mode — all properly mapped to shadcn/ui variables. This is rare at this stage.
2. **Keyboard-first architecture.** Command palette (Ctrl+K), sequence hotkeys (g+d, g+p), shortcuts dialog, skip-to-content link, and proper focus-visible indicators. This puts UPCP ahead of most admin tools.
3. **Clean data layer.** TanStack Query hooks with proper cache invalidation, pagination via URL params, optimistic-ready mutation patterns, and consistent API client with auth/refresh/error handling.

### Top 5 Critical Issues

1. **Hardcoded sample data in production components.** `LiveActivityFeed` and `AgentActivitySummary` render static `SAMPLE_EVENTS` / `SAMPLE_AGENTS` arrays instead of real API data. Dashboard attention cards are also hardcoded. This makes the dashboard non-functional.
2. **Native HTML `<select>` elements in 3 locations** (AuditPage filters, TaskDetailSheet status, EntityFormDialog select fields) break visual consistency with the shadcn Select used elsewhere.
3. **Tab mislabeling in ProjectDetail.** The tab labeled "Settings" (`value="settings"`) actually renders `<ReportsPage />`. Users clicking "Settings" get reports.
4. **Dark mode surface separation is insufficient.** Background (#0a0a0f) and surface (#111118) differ by only ~2% perceived lightness. Cards blend into the page. Borders at `rgba(255,255,255,0.08)` are nearly invisible.
5. **No real responsive adaptation for data-dense views.** BoardView forces a 4-column grid that breaks on tablet. Tables overflow without horizontal scroll hints. The main content padding (`p-4 lg:p-6`) is too tight for dense data.

### Quick Wins (Easy Fixes, High Impact)

| # | Fix | Impact | Effort |
|---|-----|--------|--------|
| 1 | Replace hardcoded data in LiveActivityFeed + AgentActivitySummary with API hooks | Dashboard becomes functional | Low |
| 2 | Replace native `<select>` with shadcn `<Select>` in AuditPage + TaskDetailSheet | Visual consistency | Low |
| 3 | Fix "Settings" tab label to "Reports" in ProjectDetail | Prevents user confusion | Trivial |
| 4 | Increase dark mode surface contrast (#111118 -> #16161e) and border opacity (0.08 -> 0.12) | Dark mode usability | Trivial |
| 5 | Add `aria-label` to all icon-only buttons (TopBar, ProjectDetail, DeliveryPage) | Accessibility compliance | Low |
| 6 | Remove dead `Layout.tsx` component | Reduces confusion | Trivial |
| 7 | Add `h-7 w-7` icon buttons minimum to `h-8 w-8` | Better touch targets | Low |

---

## Per-Component Analysis

### Dashboard (`Dashboard.tsx`)

**Quality: 6/10**

**Issues:**
- [CRITICAL] `LiveActivityFeed` renders hardcoded `SAMPLE_EVENTS` — not connected to any API
- [CRITICAL] `AgentActivitySummary` renders hardcoded `SAMPLE_AGENTS` — not connected to any API
- [CRITICAL] All 5 attention card sections (`NeedsReviewSection`, etc.) use hardcoded data
- [MEDIUM] Stat cards use inline color classes (`bg-primary/10 text-primary`) instead of design tokens
- [MEDIUM] `trend="up"` is hardcoded on "Tasks In Progress" and "Tasks Done" — not derived from data
- [LOW] "Recent Projects" section duplicates what ProjectList shows — consider removing or making it a compact widget
- [LOW] No date range filter or refresh button

**Recommendations:**
1. Create `useActivityFeed()`, `useActiveAgents()`, `useAttentionItems()` hooks backed by real API endpoints
2. Make trend indicators compute from historical data (week-over-week)
3. Add a "Last updated: X ago" indicator with manual refresh
4. Add customizable widget layout (drag-to-reorder cards)

**Reference:** Linear's home view — dense, real-time, keyboard-navigable, zero placeholder data

---

### ProjectList (`ProjectList.tsx`)

**Quality: 6/10**

**Issues:**
- [MEDIUM] Only 3 table columns (Name, Status, Created) — too sparse for project management
- [MEDIUM] No sorting or filtering capability
- [MEDIUM] No search bar for projects
- [LOW] No grid/card view alternative
- [LOW] ProjectTable renders inside a Card, but the card header + table feel disconnected

**Recommendations:**
1. Add columns: Description (truncated), Tasks count, Last Activity, Owner
2. Add sortable column headers (use DataTable component which already supports this)
3. Add SearchInput for filtering
4. Consider a grid view option for projects with cover images or status indicators

**Reference:** Vercel Dashboard project list — dense, searchable, sortable, with deployment status

---

### ProjectTable (`ProjectTable.tsx`)

**Quality: 5/10**

**Issues:**
- [MEDIUM] No keyboard navigation for rows (only click handlers, no `role="button"` or Enter key)
- [MEDIUM] `toLocaleDateString()` without options produces inconsistent formats across browsers
- [LOW] No column sorting despite DataTable component existing with sort support
- [LOW] Empty state duplicates the parent's empty state check — redundant

**Recommendations:**
1. Use the existing `DataTable<T>` component which already has sorting, filtering, density, and pagination
2. Add `onKeyDown` handler for Enter/Space on table rows
3. Use `Intl.DateTimeFormat` with explicit options for consistent date display

**Reference:** Stripe Dashboard tables — sortable, filterable, consistent date format, dense

---

### ProjectDetail (`ProjectDetail.tsx`)

**Quality: 6/10**

**Issues:**
- [CRITICAL] Tab "Settings" (`value="settings"`) renders `<ReportsPage />` — mislabeled
- [MEDIUM] Overview tab is a plain key-value grid — could be much richer
- [MEDIUM] Edit/Delete buttons are small icon-only buttons (h-8 w-8) without aria-labels
- [LOW] No project activity timeline in Overview
- [LOW] No quick stats (task completion %, active features, etc.) in Overview

**Recommendations:**
1. Fix tab label: "Settings" -> "Reports" or create a proper Settings page
2. Enhance Overview with: completion progress bar, feature count, recent activity snippet, health indicators
3. Add `aria-label="Edit project"` and `aria-label="Delete project"` to icon buttons
4. Consider a sticky tab bar that remains visible while scrolling

**Reference:** Linear project view — rich overview with progress, activity, and quick actions

---

### DeliveryPage (`DeliveryPage.tsx`)

**Quality: 7/10**

**Issues:**
- [MEDIUM] Board view triggers N+1 queries: `useQueries` fetches tasks for every feature simultaneously
- [MEDIUM] Feature sections don't persist expanded state — collapsing loses the loaded tasks
- [LOW] Search filter only applies within expanded features, not globally
- [LOW] No bulk actions (bulk status change, bulk delete)
- [LOW] "Feature" button label could be clearer ("New Feature")

**Recommendations:**
1. Add a dedicated `/api/v1/projects/{id}/tasks` endpoint that returns all tasks with feature info — eliminates N+1
2. Persist expanded feature IDs in URL params or local state
3. Make search global (search across all features, auto-expand matches)
4. Add bulk selection with checkbox column

**Reference:** Linear's cycle/feature view — global search, inline editing, keyboard shortcuts for status changes

---

### StructurePage (`StructurePage.tsx`)

**Quality: 6/10**

**Issues:**
- [MEDIUM] No search or filter for components
- [MEDIUM] No visual hierarchy — flat list of expandable cards. A tree view would better represent the Component > Module hierarchy
- [LOW] Module table has no pagination (assumes small count)
- [LOW] No drag-and-drop to reorder or reassign modules

**Recommendations:**
1. Add SearchInput for filtering components and modules
2. Consider a tree view component for clearer hierarchy visualization
3. Add module count badge on collapsed component cards
4. Add component-level stats (task count, completion %)

**Reference:** Linear's project structure — tree view with inline stats, keyboard navigation

---

### QualityPage (`QualityPage.tsx`)

**Quality: 7/10**

**Issues:**
- [MEDIUM] No drill-down into specific AC/DoD items — just aggregate stats
- [MEDIUM] Progress bars lack color thresholds (should be red < 50%, yellow 50-80%, green > 80%)
- [LOW] No trend data (is quality improving or declining?)
- [LOW] "Quality Gate" card is static text — should show actionable gate status

**Recommendations:**
1. Add a table of tasks grouped by quality status (all pass, partial, no criteria)
2. Add color thresholds to progress bars
3. Add a quality trend chart (line chart showing AC/DoD pass rate over time)
4. Make the quality gate interactive — show which tasks are blocking

**Reference:** Stripe's compliance dashboard — clear pass/fail indicators, drill-down capability

---

### AuditPage (`AuditPage.tsx`)

**Quality: 5/10**

**Issues:**
- [CRITICAL] Uses native `<select>` elements for event type and entity type filters — breaks design consistency
- [MEDIUM] No search within audit events
- [MEDIUM] Timeline dots use hardcoded color map that doesn't cover all event types (falls back to `bg-slate-400`)
- [LOW] No date range picker
- [LOW] No export functionality
- [LOW] Actor display shows truncated UUID instead of resolved name

**Recommendations:**
1. Replace native `<select>` with shadcn `<Select>` components
2. Add SearchInput for full-text search within audit events
3. Add date range picker (from/to)
4. Resolve actor IDs to names via a lookup or include names in the API response
5. Add CSV/JSON export button

**Reference:** Linear's activity log — searchable, filterable, resolved entity names, clean timeline

---

### GitIntegrationPage (`GitIntegrationPage.tsx`)

**Quality: 6/10**

**Issues:**
- [MEDIUM] No ability to connect a new git provider from the UI (no "Add Provider" button)
- [MEDIUM] Provider status badge uses generic StatusBadge — should have git-specific states (connected, syncing, error)
- [LOW] No commit-to-task linking from this view
- [LOW] Branch table has no action column (checkout, compare)

**Recommendations:**
1. Add "Connect Repository" button with provider selection dialog
2. Add git-specific status indicators (connected, syncing, auth expired, error)
3. Allow linking commits to tasks/features directly from the commits table
4. Show branch protection status and PR counts

**Reference:** GitHub's repository settings — clear connection status, branch management

---

### ReportsPage (`ReportsPage.tsx`)

**Quality: 6/10**

**Issues:**
- [MEDIUM] Only "daily" report type available — should offer weekly, monthly, custom
- [MEDIUM] No report preview — just a table row with truncated summary
- [LOW] Export uses `fetch()` directly instead of the API client — bypasses auth header
- [LOW] No date range filtering for reports

**Recommendations:**
1. Add report type selector (daily, weekly, sprint, custom range)
2. Add a report preview panel (click row to expand/view full report)
3. Use `apiRequest` for the export endpoint to include auth headers
4. Add a "Generate Report" dialog with type and date range options

**Reference:** Linear's analytics — date range selector, exportable charts, drill-down

---

### BoardView (`BoardView.tsx`)

**Quality: 7/10**

**Issues:**
- [MEDIUM] N+1 query pattern — `useQueries` fires one request per feature
- [MEDIUM] No keyboard-accessible drag-and-drop (only PointerSensor configured)
- [MEDIUM] 4-column grid breaks on tablet — should be 2 columns on medium screens
- [LOW] Tasks without a matching column status fall into "backlog" silently
- [LOW] No column customization (rename, add, remove columns)
- [LOW] DragOverlay card is duplicated from DraggableTaskCard — should be shared

**Recommendations:**
1. Add `KeyboardSensor` from @dnd-kit for accessibility
2. Use a single API endpoint that returns all tasks for a project
3. Add responsive column layout: 1 col mobile, 2 col tablet, 4 col desktop
4. Extract a shared `TaskCard` component used by both DraggableTaskCard and DragOverlay
5. Add "Add Column" and column rename capabilities

**Reference:** Linear's board view — keyboard DnD, swimlanes, column customization, filters

---

### TaskDetailSheet (`TaskDetailSheet.tsx`)

**Quality: 7/10**

**Issues:**
- [CRITICAL] Execution tab shows hardcoded agent data ("code-quality-guard", "5 min ago", "30s ago") — not from API
- [MEDIUM] Status change uses native `<select>` instead of shadcn Select
- [MEDIUM] Component/Module IDs shown as raw UUIDs instead of resolved names
- [MEDIUM] Sheet width is `sm:max-w-[600px]` — could use more space for dense content
- [LOW] No rich text editing for description (plain textarea)
- [LOW] No file attachment capability
- [LOW] No task history/timeline

**Recommendations:**
1. Connect Execution tab to real agent task data via API
2. Replace native `<select>` with shadcn Select or a status dropdown with colored options
3. Resolve component_id and module_id to names using lookups
4. Consider full-page task view for complex tasks (not just sheet)
5. Add a "History" tab showing all changes to the task

**Reference:** Linear's task detail — rich editor, keyboard shortcuts, activity log, linked PRs

---

### LoginPage (`LoginPage.tsx`)

**Quality: 5/10**

**Issues:**
- [MEDIUM] No "remember me" checkbox
- [MEDIUM] No password visibility toggle (eye icon)
- [MEDIUM] Error message doesn't auto-dismiss and has no close button
- [LOW] Uses `window.location.href` for navigation instead of router — causes full page reload
- [LOW] No loading spinner on the submit button — just text changes to "Signing in..."
- [LOW] No branding beyond "UPCP" text — could have a logo

**Recommendations:**
1. Add password visibility toggle
2. Use `navigate({ to: '/' })` from TanStack Router instead of `window.location.href`
3. Add a proper loading spinner to the submit button
4. Add "Forgot password?" link (even if not yet functional)
5. Add subtle background pattern or gradient for visual interest

**Reference:** Vercel's login page — clean, branded, with provider options

---

### SetupPage (`SetupPage.tsx`)

**Quality: 5/10**

**Issues:**
- [MEDIUM] No password strength indicator
- [MEDIUM] Same issues as LoginPage (window.location, no visibility toggle)
- [LOW] No confirmation password field
- [LOW] Display name field has no character limit indication

**Recommendations:**
1. Add password strength meter (weak/fair/strong/very strong)
2. Add password confirmation field
3. Use router navigation instead of window.location
4. Add a progress indicator (Step 1 of 1)

**Reference:** Vercel's signup flow — password strength, clear requirements

---

### HealthPage (`HealthPage.tsx`)

**Quality: 5/10**

**Issues:**
- [CRITICAL] Database card is hardcoded as "Connected" — not from API data
- [MEDIUM] No detailed metrics (response time, error rate, uptime percentage)
- [MEDIUM] "Auto-refresh" card is informational only — should show last refresh time and toggle
- [LOW] No historical health data or trend

**Recommendations:**
1. Fetch real database health from the API
2. Add response time, uptime %, and error rate cards
3. Make auto-refresh configurable (toggle on/off, change interval)
4. Add a simple health timeline (last 24h status)

**Reference:** Vercel's system status page — real-time, detailed, with incident history

---

### NotFoundPage (`NotFoundPage.tsx`)

**Quality: 7/10**

**Issues:**
- [LOW] No search suggestion
- [LOW] No recently visited pages
- [LOW] Card layout is centered but doesn't fill the viewport height

**Recommendations:**
1. Add a search input or command palette trigger
2. Add "Recently visited" links
3. Center vertically in the viewport (`min-h-[60vh] flex items-center`)

**Reference:** GitHub's 404 — octocat illustration, search, recent repos

---

### ErrorBoundary (`ErrorBoundary.tsx`)

**Quality: 6/10**

**Issues:**
- [MEDIUM] No error reporting/logging to external service
- [MEDIUM] No "copy error details" button for support
- [LOW] No technical details toggle (for developers)

**Recommendations:**
1. Add error logging (console.error is there, but consider Sentry-like reporting)
2. Add a "Copy Error Details" button that copies stack trace
3. Add a collapsible "Technical Details" section

**Reference:** Vercel's error pages — clean, with error ID and copy button

---

### AppShell (`AppShell.tsx`)

**Quality: 8/10**

**Issues:**
- [LOW] Main content padding `p-4 lg:p-6` is tight for data-dense views — consider `p-4 lg:p-8`
- [LOW] No page transition animation between routes

**Recommendations:**
1. Increase main content padding for breathing room
2. Add subtle fade transition between route changes
3. Consider adding a footer with version info and links

**Reference:** Linear's app shell — tight but breathable, smooth transitions

---

### AppSidebar (`AppSidebar.tsx`)

**Quality: 7/10**

**Issues:**
- [MEDIUM] No way to switch between projects from within a project (must go back to /projects)
- [LOW] No recently visited projects section
- [LOW] No search within sidebar for large nav lists
- [LOW] UPCP logo is just a "U" in a box — should be a proper logo

**Recommendations:**
1. Add a project switcher dropdown in the project nav section
2. Add a "Recent" section showing last 3 visited projects
3. Replace the "U" text with an SVG logo
4. Add keyboard shortcut indicators next to nav items

**Reference:** Linear's sidebar — project switcher, recent items, keyboard hints

---

### TopBar (`TopBar.tsx`)

**Quality: 7/10**

**Issues:**
- [CRITICAL] Notification badge shows hardcoded "3" — not from API
- [MEDIUM] Notification bell has no click handler — non-functional UI element
- [LOW] "UPCP" text in top bar is redundant with sidebar logo
- [LOW] User avatar dropdown items (Profile, Settings, Logout) have no click handlers

**Recommendations:**
1. Connect notifications to a real API or remove the badge count
2. Add notification panel/dropdown
3. Remove redundant "UPCP" text or replace with page-specific title
4. Implement user menu actions (at minimum, Logout should work)

**Reference:** Linear's top bar — functional notifications, quick actions, user menu

---

### BreadcrumbBar (`BreadcrumbBar.tsx`)

**Quality: 6/10**

**Issues:**
- [MEDIUM] UUID segments are silently skipped — should show entity name (project name, not ID)
- [MEDIUM] Current page is a clickable link — should be plain text (not linked)
- [LOW] No aria-label on the nav element

**Recommendations:**
1. Resolve UUID segments to entity names using route context or a lookup
2. Make the last breadcrumb item non-clickable (current page)
3. Add `aria-label="Breadcrumb"` to the nav element
4. Consider merging breadcrumbs into the TopBar to save vertical space

**Reference:** Linear's breadcrumbs — resolved names, current page emphasized, compact

---

### CommandPalette (`CommandPalette.tsx`)

**Quality: 8/10**

**Issues:**
- [MEDIUM] No action commands (e.g., "Create Project", "Create Task", "Toggle Theme")
- [LOW] Search results don't show the entity type icon prominently
- [LOW] No loading indicator while search is fetching
- [LOW] Recent items persist across sessions via localStorage — may become stale

**Recommendations:**
1. Add action commands: Create Project, Create Task, Toggle Theme, Toggle Sidebar
2. Add a loading spinner in the search results area
3. Clear stale recent items (items that no longer exist)
4. Add section for "Actions" alongside Navigation and Search Results

**Reference:** Raycast — actions, clipboard history, calculator, system commands

---

### EntityFormDialog (`EntityFormDialog.tsx`)

**Quality: 7/10**

**Issues:**
- [CRITICAL] `select` fields use native HTML `<select>` — inconsistent with shadcn Select used in DataTablePagination
- [MEDIUM] No field-level validation beyond "required" (no email format, no min/max length)
- [MEDIUM] `textarea` uses raw HTML without shadcn styling
- [LOW] No dirty state tracking (no "unsaved changes" warning)
- [LOW] No keyboard shortcut to submit (Cmd+Enter)

**Recommendations:**
1. Replace native `<select>` with shadcn `<Select>` component
2. Add a shadcn-styled Textarea component
3. Add field-level validation rules (minLength, maxLength, pattern)
4. Add Cmd+Enter to submit
5. Track dirty state and warn on close if unsaved

**Reference:** Linear's create dialog — clean, keyboard-driven, with validation

---

### DataTable (`DataTable.tsx`)

**Quality: 7/10**

**Issues:**
- [MEDIUM] Not actually used by any page — ProjectList/ProjectTable bypass it with custom tables
- [LOW] No column visibility toggle
- [LOW] No column resizing
- [LOW] No bulk selection (checkbox column)
- [LOW] No export functionality

**Recommendations:**
1. Adopt DataTable in ProjectList, ReportsPage, AuditPage for consistency
2. Add column visibility toggle (dropdown with checkboxes)
3. Add bulk selection with action bar
4. Add CSV export

**Reference:** TanStack Table demos — column pinning, resizing, visibility, faceted filters

---

### StatusBadge (`StatusBadge.tsx`)

**Quality: 8/10**

**Issues:**
- [LOW] `border-transparent` on outline variant removes visual border — consider a subtle colored border
- [LOW] No animation on status change

**Recommendations:**
1. Add a subtle colored border instead of transparent (`border-{color}/20`)
2. Consider a brief highlight animation on status change

---

### PriorityDot (`PriorityDot.tsx`)

**Quality: 7/10**

**Issues:**
- [LOW] All priorities render the same size dot — consider larger dots for higher priorities
- [LOW] `role="img"` with `tabIndex={0}` on a span is unusual — should be the container, not the dot

**Recommendations:**
1. Scale dot size by priority (P0: h-3 w-3, P3: h-2 w-2)
2. Simplify the accessibility markup

---

### ClarificationBanner (`ClarificationBanner.tsx`)

**Quality: 8/10**

**Issues:**
- [LOW] No inline answer form — "Answer" button requires a callback but no visible input

**Recommendations:**
1. Add an expandable inline response form when "Answer" is clicked

---

### ReviewVerdictCard (`ReviewVerdictCard.tsx`)

**Quality: 8/10**

**Issues:**
- [LOW] Confidence bar is tiny (w-16) — hard to read
- [LOW] `onAccept`/`onReject` props exist but are never passed in the TaskDetailSheet usage

**Recommendations:**
1. Make confidence bar wider (w-24 or full width)
2. Wire up accept/reject actions in TaskDetailSheet

---

### ShortcutsDialog (`ShortcutsDialog.tsx`)

**Quality: 7/10**

**Issues:**
- [LOW] Task shortcuts (T C, T R, T S, T E, T Q) are listed but not implemented in useHotkeys
- [LOW] No search within shortcuts

**Recommendations:**
1. Implement the listed task shortcuts or remove them from the dialog
2. Add a search/filter input at the top

---

## Design System Assessment

### Colors

**Score: 7/10**

**Strengths:**
- Comprehensive 6-color brand palette with CSS custom properties
- Full status (9 states), priority (4 levels), and agent (5 states) color maps
- Agent vs Human vs System semantic colors (violet/blue/slate)
- Proper dark mode variants for every color
- Tailwind utility classes using the token system

**Issues:**
- [HIGH] Dark mode background (#0a0a0f) and surface (#111118) differ by only ~2% perceived lightness — cards visually merge with the page
- [HIGH] Dark mode border at `rgba(255,255,255,0.08)` is nearly invisible — card boundaries are unclear
- [MEDIUM] `STATUS_COLORS` in constants.ts duplicates the CSS custom properties in index.css — two sources of truth
- [MEDIUM] Some components use hardcoded Tailwind colors (`bg-emerald-500/10`) instead of CSS variables — not themeable
- [LOW] No color contrast automated checks — some text-on-background combinations may fail WCAG AA

**Recommendations:**
1. Increase dark mode surface lightness to `#16161e` or `#1a1a24`
2. Increase dark mode border opacity to `rgba(255,255,255,0.12)` minimum
3. Consolidate color definitions: use CSS variables everywhere, remove duplicate maps from constants.ts
4. Run an automated contrast check (axe-core or similar) on all status/priority badge combinations

### Typography

**Score: 6/10**

**Strengths:**
- Geist Variable is an excellent choice (modern, clean, good metrics)
- JetBrains Mono for code — proper monospace pairing
- Base 14px/1.5 line height is appropriate for a data-dense tool

**Issues:**
- [MEDIUM] No fluid typography — headings use fixed sizes (text-2xl, text-lg) that don't scale
- [MEDIUM] Inconsistent heading hierarchy: Dashboard uses `text-2xl font-bold` for stats, `text-sm font-semibold uppercase` for section headers, while pages use `text-lg font-semibold` for section titles
- [MEDIUM] No established type scale — components pick sizes ad hoc
- [LOW] `font-heading` is defined but never used explicitly in components

**Recommendations:**
1. Define a type scale with CSS custom properties: `--text-xs` through `--text-3xl` with fluid clamp() values
2. Standardize: Page title = `text-2xl font-bold tracking-tight`, Section header = `text-sm font-semibold uppercase tracking-wider`, Card title = `text-base font-medium`
3. Use `font-heading` for headings consistently

### Spacing

**Score: 6/10**

**Strengths:**
- 4px grid defined with CSS variables (--spacing-xs through --spacing-3xl)
- Cards use consistent `--card-spacing` variable
- Good use of Tailwind spacing utilities

**Issues:**
- [HIGH] Inconsistent section spacing across pages: `space-y-4`, `space-y-6` used interchangeably — no standard section rhythm
- [MEDIUM] Main content area padding is `p-4 lg:p-6` — too tight for a professional tool (should be `p-4 lg:p-8` minimum)
- [MEDIUM] No minimum 80px between major sections as recommended for professional tools
- [LOW] Some components have ad hoc margins that break the grid (`mt-1.5`, `gap-3`)

**Recommendations:**
1. Define section spacing as a CSS variable: `--section-spacing: clamp(3rem, 5vw, 5rem)`
2. Standardize page layout: `space-y-8` between major sections minimum
3. Increase main content padding to `p-4 lg:p-8`
4. Audit all margin/gap usage for grid alignment

### Animations

**Score: 7/10**

**Strengths:**
- Well-defined animation tokens: heartbeat-pulse, badge-pop, slide-in-right, fade-in-up, stagger-fade-in
- Proper `prefers-reduced-motion` support that disables all animations
- Good easing curves (ease-default, ease-spring)
- Stagger animations for lists with nth-child delays

**Issues:**
- [MEDIUM] All animations are entry-only — no exit animations (items disappear instantly)
- [MEDIUM] No page/route transition animations
- [MEDIUM] Hover interactions are limited to color changes — no micro-interactions (subtle scale, shadow lift)
- [LOW] Stagger animation only supports up to 8 children (nth-child 1-8)
- [LOW] No loading shimmer animation beyond basic skeleton pulse

**Recommendations:**
1. Add exit animations using CSS `@starting-style` or a library like framer-motion
2. Add subtle route transition (fade or slide)
3. Add hover micro-interactions: card shadow lift (`hover:shadow-md`), button subtle scale (`active:scale-[0.98]`)
4. Consider a shimmer gradient for skeleton loading instead of flat pulse

### Dark Mode

**Score: 5/10**

**Strengths:**
- Complete token mapping for all colors in dark mode
- `next-themes` with system preference detection
- `disableTransitionOnChange` prevents flash during theme switch
- Proper semantic color adjustments (emerald-400 for dark, emerald-600 for light)

**Issues:**
- [HIGH] Surface separation is insufficient — background and surface are too similar
- [HIGH] Border visibility is too low — cards blend together
- [MEDIUM] `--primary-foreground` in dark mode is `#0a0a0f` (near-black) which may not contrast well with `#60a5fa` primary
- [MEDIUM] Some components use hardcoded light-mode colors that don't adapt (e.g., `bg-violet-500/10` works in both modes but `text-violet-600` should be `text-violet-400` in dark)
- [LOW] No high-contrast mode option

**Recommendations:**
1. Increase surface lightness: `#111118` -> `#16161e` or `#1a1a24`
2. Increase border opacity: `rgba(255,255,255,0.08)` -> `rgba(255,255,255,0.12)`
3. Test all badge/badge combinations in dark mode for contrast
4. Consider a dark mode specific border color (`--border-dark: #2a2a35`)

---

## Information Architecture

### Navigation

**Score: 7/10**

**Strengths:**
- Sidebar with collapsible icon mode (rail)
- Project context navigation appears dynamically on project routes
- BreadcrumbBar for hierarchical wayfinding
- Command palette with recent, navigation, project commands, and search
- Max 7 items in main nav (2 main + 3 system)

**Issues:**
- [HIGH] Settings route renders NotFoundPage — the nav item leads to a dead end
- [MEDIUM] No project quick-switcher (must navigate back to /projects list)
- [MEDIUM] Project sub-navigation has 6 items (Overview, Structure, Delivery, Quality, Audit, Git + Settings/Reports = 7) — at the limit
- [LOW] No way to collapse or pin the project nav section

**Recommendations:**
1. Fix Settings route or create a real Settings page
2. Add a project switcher dropdown in the sidebar (like Linear's workspace switcher)
3. Consider grouping less-used project tabs (Audit, Git, Reports) into a "More" dropdown

### Hierarchy

**Score: 7/10**

**Strengths:**
- Clear hierarchy: Dashboard -> Projects -> Project Detail (tabs) -> Features -> Tasks
- Proper use of headings for screen readers
- Good progressive disclosure (expandable features/components)

**Issues:**
- [MEDIUM] Dashboard attention cards compete with stat cards for visual priority
- [MEDIUM] Project detail header and tabs feel disconnected — no visual bridge
- [LOW] No visual indication of the current depth level in the hierarchy

**Recommendations:**
1. Establish clear visual hierarchy: primary actions larger, secondary smaller
2. Add a project summary bar between the header and tabs
3. Use subtle background color shifts to indicate depth

### Progressive Disclosure

**Score: 7/10**

**Strengths:**
- Features expand to show tasks (accordion pattern)
- Components expand to show modules
- Task detail as a side sheet preserves context
- Tabs in ProjectDetail and TaskDetailSheet

**Issues:**
- [MEDIUM] All task details behind a sheet — no inline quick-edit
- [LOW] No "expand all" / "collapse all" for feature sections
- [LOW] No breadcrumb within the task detail sheet

**Recommendations:**
1. Add inline quick-edit for task status and priority (click to change)
2. Add "Expand All" / "Collapse All" toggle for feature sections
3. Show context breadcrumb in the sheet header (Project > Feature > Task)

---

## Interaction Patterns

### Keyboard Navigation

**Score: 8/10**

**Strengths:**
- Skip-to-content link (`<a href="#main-content">`)
- Command palette (Ctrl+K) with search, recent, and project commands
- Sequence hotkeys (g+d, g+p, g+r, g+s)
- Shortcuts dialog (? key)
- Focus-visible indicators on all interactive elements
- Proper disabled state handling

**Issues:**
- [MEDIUM] Task shortcuts listed in ShortcutsDialog (T C, T R, T S, T E, T Q) are not implemented
- [MEDIUM] Board drag-and-drop has no keyboard alternative
- [LOW] Tab order in expandable feature sections may skip content
- [LOW] No keyboard shortcut to toggle between list/board view in DeliveryPage

**Recommendations:**
1. Implement or remove the task shortcuts from the dialog
2. Add KeyboardSensor to @dnd-kit for board navigation
3. Add `v` key to toggle list/board view
4. Test complete tab order through all interactive elements

### Mouse Interactions

**Score: 6/10**

**Strengths:**
- Hover states on cards, table rows, and links
- Pointer cursor on clickable elements
- Tooltips on icon buttons and truncated text

**Issues:**
- [MEDIUM] Some icon buttons are only 28px (h-7 w-7) — below the 44px WCAG recommended touch target
- [MEDIUM] Delete buttons (ghost variant, icon only) are easy to accidentally click — no confirmation step for module deletion in StructurePage
- [LOW] No right-click context menus
- [LOW] No double-click interactions for quick actions

**Recommendations:**
1. Increase minimum icon button size to h-8 w-8 (32px) with adequate padding
2. Add a hover delay or confirmation for destructive actions
3. Consider context menus for table rows (right-click or kebab menu)
4. Add double-click to open task detail from table

### Touch Support

**Score: 4/10**

**Issues:**
- [HIGH] BoardView drag-and-drop only has PointerSensor — needs TouchSensor for mobile
- [HIGH] Many interactive elements are below 44px touch target minimum
- [MEDIUM] No swipe gestures for common actions (swipe to delete, swipe to change status)
- [MEDIUM] No pull-to-refresh on data views
- [LOW] Sheet (side panel) works on mobile but occupies full width — no way to dismiss by swiping down

**Recommendations:**
1. Add TouchSensor with activation delay to BoardView
2. Increase all interactive element minimum sizes to 44px
3. Consider swipe actions on task cards and table rows
4. Test all views on mobile viewport (375px width)

---

## Missing Features

| Feature | Description | Priority | Reference |
|---------|-------------|----------|-----------|
| **Real-time updates** | WebSocket or SSE for live dashboard updates, agent status, activity feed | Critical | Linear, Vercel |
| **Notifications panel** | Functional notification dropdown with read/unread, not just a badge | High | Linear, GitHub |
| **Settings page** | User preferences, theme, notification settings, API keys, team management | High | All references |
| **Inline editing** | Click-to-edit for task title, status, priority without opening sheet | High | Linear |
| **Bulk actions** | Select multiple tasks/features for batch status change, delete, move | Medium | Linear, Jira |
| **Global search** | Full-text search across all entities with keyboard navigation | Medium | Linear, Raycast |
| **Keyboard DnD** | Keyboard-accessible drag-and-drop on board view | Medium | Linear |
| **Date range picker** | For reports, audit, and dashboard filtering | Medium | Stripe |
| **Rich text editor** | For task/feature descriptions (Markdown or TipTap) | Medium | Linear, Notion |
| **File attachments** | Upload and attach files to tasks | Low | Linear, Jira |
| **Custom views** | Save custom filter/sort/view configurations per user | Low | Linear |
| **Activity timeline** | Global activity feed with filtering by actor/entity/type | Low | Linear, GitHub |
| **Export/import** | CSV/JSON export for projects, tasks, reports | Low | Jira, Asana |
| **User profile page** | Edit display name, avatar, password, preferences | Low | All references |
| **Multi-language** | i18n support for non-English users | Low | All references |
| **Onboarding flow** | First-run wizard for new users | Low | Vercel, Linear |
| **Command actions** | Command palette actions (create project, change theme) beyond navigation | Low | Raycast |
| **Context menus** | Right-click menus on tasks, projects, features | Low | Linear, macOS |
| **Offline support** | Service worker for offline access to cached data | Low | Notion |

---

## Priority Matrix

### Critical (Must Fix)

1. **Replace hardcoded sample data** in LiveActivityFeed, AgentActivitySummary, and AttentionCards with real API hooks
2. **Fix "Settings" tab** in ProjectDetail that renders ReportsPage
3. **Replace native `<select>`** in AuditPage, TaskDetailSheet, and EntityFormDialog with shadcn Select
4. **Improve dark mode contrast** — increase surface lightness and border opacity
5. **Fix Settings route** — either create a Settings page or remove from navigation
6. **Connect TopBar notifications** to real data or remove hardcoded badge

### High (Should Fix)

7. **Increase icon button sizes** from h-7 to h-8 minimum for better touch targets
8. **Add aria-labels** to all icon-only buttons throughout the application
9. **Standardize section spacing** — use `space-y-8` minimum between major sections
10. **Standardize heading hierarchy** — consistent size/weight/spacing across all pages
11. **Implement N+1 fix** — add `/projects/{id}/tasks` endpoint for BoardView
12. **Resolve entity names** in breadcrumbs and audit log (don't show raw UUIDs)
13. **Connect HealthPage database card** to real API data
14. **Implement task shortcuts** listed in ShortcutsDialog or remove them
15. **Use DataTable** in ProjectList, ReportsPage, AuditPage for consistency

### Medium (Nice to Have)

16. Add route/page transition animations
17. Add hover micro-interactions (shadow lift, subtle scale)
18. Add column visibility toggle to DataTable
19. Add bulk selection and actions
20. Add inline quick-edit for task status/priority
21. Add password visibility toggle on LoginPage/SetupPage
22. Use router navigation instead of `window.location.href` in auth pages
23. Add search functionality to AuditPage
24. Add date range filtering to ReportsPage
25. Add TouchSensor to BoardView for mobile drag-and-drop
26. Create a project switcher in the sidebar
27. Consolidate color definitions (CSS variables as single source of truth)
28. Add fluid typography with clamp()

### Low (Future)

29. Rich text editor for descriptions
30. File attachments on tasks
31. Context menus (right-click)
32. Custom saved views
33. Offline support with service worker
34. Multi-language support
35. Onboarding flow
36. Export/import functionality
37. WebSocket for real-time updates
38. User profile management page

---

## Appendix: Component Inventory

| Component | File | Quality | Key Issue |
|-----------|------|---------|-----------|
| Dashboard | `Dashboard.tsx` | 6/10 | Hardcoded data |
| ProjectList | `ProjectList.tsx` | 6/10 | Sparse columns |
| ProjectTable | `ProjectTable.tsx` | 5/10 | Not using DataTable |
| ProjectDetail | `ProjectDetail.tsx` | 6/10 | Tab mislabeling |
| DeliveryPage | `DeliveryPage.tsx` | 7/10 | N+1 queries |
| StructurePage | `StructurePage.tsx` | 6/10 | No search/filter |
| QualityPage | `QualityPage.tsx` | 7/10 | No drill-down |
| AuditPage | `AuditPage.tsx` | 5/10 | Native select |
| GitIntegrationPage | `GitIntegrationPage.tsx` | 6/10 | No add provider |
| ReportsPage | `ReportsPage.tsx` | 6/10 | Single report type |
| BoardView | `BoardView.tsx` | 7/10 | N+1, no keyboard DnD |
| TaskDetailSheet | `TaskDetailSheet.tsx` | 7/10 | Hardcoded execution |
| LoginPage | `LoginPage.tsx` | 5/10 | window.location |
| SetupPage | `SetupPage.tsx` | 5/10 | No password strength |
| HealthPage | `HealthPage.tsx` | 5/10 | Hardcoded DB status |
| NotFoundPage | `NotFoundPage.tsx` | 7/10 | No search |
| ErrorBoundary | `ErrorBoundary.tsx` | 6/10 | No error details |
| AppShell | `AppShell.tsx` | 8/10 | Tight padding |
| AppSidebar | `AppSidebar.tsx` | 7/10 | No project switcher |
| TopBar | `TopBar.tsx` | 7/10 | Hardcoded notification |
| BreadcrumbBar | `BreadcrumbBar.tsx` | 6/10 | UUID not resolved |
| CommandPalette | `CommandPalette.tsx` | 8/10 | No actions |
| EntityFormDialog | `EntityFormDialog.tsx` | 7/10 | Native select |
| DataTable | `DataTable.tsx` | 7/10 | Not adopted |
| StatusBadge | `StatusBadge.tsx` | 8/10 | Transparent border |
| PriorityDot | `PriorityDot.tsx` | 7/10 | Same-size dots |
| AgentAvatar | `AgentAvatar.tsx` | 7/10 | No click action |
| AgentStatusBadge | `AgentStatusBadge.tsx` | 7/10 | No tooltip |
| ActorBadge | `ActorBadge.tsx` | 8/10 | Good |
| ClarificationBanner | `ClarificationBanner.tsx` | 8/10 | No inline answer |
| ReviewVerdictCard | `ReviewVerdictCard.tsx` | 8/10 | Tiny confidence bar |
| EmptyState | `EmptyState.tsx` | 8/10 | Good |
| ErrorState | `ErrorState.tsx` | 7/10 | No details |
| PageSkeleton | `PageSkeleton.tsx` | 7/10 | Limited variants |
| SearchInput | `SearchInput.tsx` | 8/10 | Good |
| PageHeader | `PageHeader.tsx` | 7/10 | Unused |
| ShortcutsDialog | `ShortcutsDialog.tsx` | 7/10 | Unimplemented shortcuts |
| ConfirmDialog | `ConfirmDialog.tsx` | 8/10 | Good |
| Layout (legacy) | `Layout.tsx` | 3/10 | Dead code, remove |
