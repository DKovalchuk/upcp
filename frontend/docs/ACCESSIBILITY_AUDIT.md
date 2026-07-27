# UPCP Accessibility Audit (WCAG 2.1 AA)

**Audit Date:** 2026-07-27
**Scope:** Full frontend component library
**Standard:** WCAG 2.1 Level AA
**Tech Stack:** React 19, TypeScript, Tailwind CSS 4, base-ui (shadcn/ui), TanStack Router/Query

---

## Executive Summary

- **Accessibility Score: 6/10**
- **Critical violations:** 7
- **High violations:** 8
- **Medium violations:** 12
- **Low violations:** 6
- **Total findings:** 33

The UPCP frontend has a solid foundation — semantic HTML, proper form labels, skip navigation, focus indicators, and reduced-motion support. The use of base-ui primitives for Dialog, Sheet, Select, Dropdown, Tabs, and Tooltip provides accessible keyboard handling and ARIA attributes out of the box.

However, there are significant gaps in interactive pattern accessibility (clickable table rows and divs without keyboard support), missing ARIA live regions for dynamic content, and color-only status indicators throughout the application.

---

## Per-Component Findings

### AppShell.tsx

| Finding | WCAG | Severity |
|---------|------|----------|
| Skip navigation link correctly implemented | 2.4.1 | Pass |
| `<main id="main-content">` landmark present | 1.3.1 | Pass |
| ErrorBoundary wraps content properly | -- | Pass |

No issues. This component is exemplary.

---

### AppSidebar.tsx

| Finding | WCAG | Severity |
|---------|------|----------|
| Sidebar nav uses `<ul>`, `<li>` via SidebarMenu | 1.3.1 | Pass |
| SidebarMenuButton uses base-ui Button (keyboard accessible) | 2.1.1 | Pass |
| SidebarRail has `aria-label="Toggle Sidebar"` | 4.1.2 | Pass |
| SidebarGroupLabel uses `<div>` — not identified as heading | 1.3.1 | Medium |

**SidebarGroupLabel heading issue:**
- **WCAG:** 1.3.1 Info and Relationships
- **Severity:** Medium
- **Current:** `SidebarGroupLabel` renders as `<div>` with `text-xs font-medium` styling. Screen readers do not identify these as section headings.
- **Expected:** Navigation groups should be identifiable as headings (e.g., `<h2>` or `role="heading"`) so screen reader users can navigate by heading.
- **Fix:** Pass `render={<h2 />}` to SidebarGroupLabel or add `role="heading" aria-level="2"`.

---

### TopBar.tsx

| Finding | WCAG | Severity |
|---------|------|----------|
| `<header>` landmark used | 1.3.1 | Pass |
| SidebarTrigger has `sr-only` text | 4.1.2 | Pass |
| ThemeToggle has `sr-only` description | 4.1.2 | Pass |
| Notification bell lacks accessible label | 4.1.2 | High |
| Notification count not announced | 4.1.3 | High |
| Search button keyboard trigger works | 2.1.1 | Pass |

**Notification bell button:**
- **WCAG:** 4.1.2 Name, Role, Value
- **Severity:** High
- **Current:** The Bell button relies on a Tooltip for its name. The notification count badge ("3") is a `<span>` inside the button with no ARIA attributes. Screen readers may not announce the count.
- **Expected:** Button should have `aria-label="Notifications (3)"` and the count should be announced when it changes.
- **Fix:** Add `aria-label={`Notifications (${count})`}` to the button. Add `aria-live="polite"` to a container around the count so changes are announced.

**ThemeToggle state communication:**
- **WCAG:** 4.1.2 Name, Role, Value
- **Severity:** Medium
- **Current:** The accessible name is always "Toggle theme (Ctrl+J)" regardless of current theme. The `title` attribute shows the current theme but is not reliably announced.
- **Expected:** Screen reader users should hear the current theme and what the next action will do.
- **Fix:** Change `sr-only` text to `Switch to ${nextTheme} theme (current: ${theme})`.

---

### BreadcrumbBar.tsx

| Finding | WCAG | Severity |
|---------|------|----------|
| `<nav>` element used | 1.3.1 | Pass |
| Missing `aria-label="Breadcrumb"` | 4.1.2 | Medium |
| Links are descriptive | 2.4.4 | Pass |
| Correctly hidden on home page | -- | Pass |

**Missing breadcrumb label:**
- **WCAG:** 4.1.2 Name, Role, Value
- **Severity:** Medium
- **Current:** `<nav>` has no `aria-label`. If multiple `<nav>` elements exist on a page, screen readers cannot distinguish them.
- **Fix:** Add `aria-label="Breadcrumb"` to the `<nav>` element.

---

### Dashboard.tsx

| Finding | WCAG | Severity |
|---------|------|----------|
| Heading hierarchy correct (`h2` for section) | 1.3.1 | Pass |
| Trend arrow uses color only | 1.4.1 | Medium |
| StatCard icons lack `aria-hidden` | 1.1.1 | Low |
| Links in Recent Projects are descriptive | 2.4.4 | Pass |

**Trend arrow color-only indicator:**
- **WCAG:** 1.4.1 Use of Color
- **Severity:** Medium
- **Current:** The `TrendingUp` icon is green for "up" and rotated red for "down". No text alternative conveys the direction.
- **Expected:** Direction should be conveyed by text or `aria-label`, not color alone.
- **Fix:** Add `aria-label={trend === 'up' ? 'Trending up' : 'Trending down'}` and `role="img"` to the trend icon.

---

### ProjectList.tsx

| Finding | WCAG | Severity |
|---------|------|----------|
| Form dialog has proper labels | 3.3.2 | Pass |
| Loading skeleton not announced | 4.1.3 | Medium |
| EmptyState button keyboard accessible | 2.1.1 | Pass |

**Loading skeleton not announced:**
- **WCAG:** 4.1.3 Status Messages
- **Severity:** Medium
- **Current:** Skeleton loading state renders without `aria-busy` or `role="status"`. Screen readers are not informed that content is loading.
- **Fix:** Wrap loading state in `<div aria-busy="true" role="status"><span className="sr-only">Loading projects...</span></div>`.

---

### ProjectTable.tsx

| Finding | WCAG | Severity |
|---------|------|----------|
| Proper `<table>` semantic structure | 1.3.1 | Pass |
| `<TableRow>` has `onClick` without keyboard support | 2.1.1 | Critical |
| No `role="link"` or `tabIndex` on interactive rows | 4.1.2 | Critical |

**Clickable table rows — keyboard inaccessible:**
- **WCAG:** 2.1.1 Keyboard
- **Severity:** Critical
- **Current:** Each `<TableRow>` has `onClick={() => navigate(...)}` and `className="cursor-pointer"` but no `tabIndex`, no `onKeyDown` handler, and no ARIA role. Keyboard-only users cannot navigate to project detail pages from the table.
- **Expected:** Rows should be focusable and activatable via keyboard.
- **Fix:** Either:
  1. Add `tabIndex={0}`, `role="link"`, `onKeyDown={(e) => e.key === 'Enter' && navigate(...)}` to each row, OR
  2. Make the project name a `<Link>` component inside the cell (preferred — keeps semantic meaning).

---

### ProjectDetail.tsx

| Finding | WCAG | Severity |
|---------|------|----------|
| `<h1>` heading present | 1.3.1 | Pass |
| Tabs properly implemented via base-ui | 4.1.2 | Pass |
| Edit/Delete icon buttons lack `aria-label` | 4.1.2 | High |
| Tab value/label mismatch: value="settings" label="Reports" | 1.3.1 | Medium |

**Icon-only buttons without labels:**
- **WCAG:** 4.1.2 Name, Role, Value
- **Severity:** High
- **Current:** Edit (Pencil) and Delete (Trash2) buttons use `size="icon"` with only an SVG icon. No `aria-label`, no `sr-only` text, no tooltip.
- **Expected:** Screen readers announce these as "Edit project" and "Delete project".
- **Fix:** Add `aria-label="Edit project"` and `aria-label="Delete project"` respectively. Wrap in Tooltip for sighted users.

**Tab value/label mismatch:**
- **WCAG:** 1.3.1 Info and Relationships
- **Severity:** Medium
- **Current:** `<TabsTrigger value="settings">Reports</TabsTrigger>`. The value "settings" does not match the label "Reports". This creates confusion in URL routing vs displayed content.
- **Fix:** Align the `value` with the label or use consistent naming.

---

### DeliveryPage.tsx

| Finding | WCAG | Severity |
|---------|------|----------|
| View mode toggle buttons lack `aria-pressed` | 4.1.2 | High |
| FeatureSection header is `<div onClick>` — no keyboard | 2.1.1 | Critical |
| Task table rows have `onClick` without keyboard | 2.1.1 | Critical |
| Delete button has no `aria-label` | 4.1.2 | High |
| `<h2>` heading present | 1.3.1 | Pass |

**FeatureSection expand/collapse — keyboard inaccessible:**
- **WCAG:** 2.1.1 Keyboard
- **Severity:** Critical
- **Current:** The feature section header is a `<div>` with `onClick={onToggle}`. It has `cursor-pointer` styling but no `tabIndex`, no `role="button"`, no `onKeyDown`, and no `aria-expanded` attribute.
- **Expected:** Should be a `<button>` or have `role="button"`, `tabIndex={0}`, `aria-expanded={isExpanded}`, and keyboard handler.
- **Fix:** Replace the `<div>` with a `<button>` element, or add `role="button"`, `tabIndex={0}`, `aria-expanded={isExpanded}`, and `onKeyDown` handler.

**View mode toggle:**
- **WCAG:** 4.1.2 Name, Role, Value
- **Severity:** High
- **Current:** List/Board toggle buttons use `title` for accessible name but lack `aria-pressed` to indicate which view is active. Screen readers cannot determine which button is currently selected.
- **Fix:** Add `aria-pressed={viewMode === 'list'}` and `aria-pressed={viewMode === 'board'}`.

**Task table rows — keyboard inaccessible:**
- **WCAG:** 2.1.1 Keyboard
- **Severity:** Critical
- **Current:** Same issue as ProjectTable — `<TableRow>` with `onClick` but no keyboard support.

---

### StructurePage.tsx

| Finding | WCAG | Severity |
|---------|------|----------|
| ComponentCard header is `<div onClick>` — no keyboard | 2.1.1 | Critical |
| Missing `aria-expanded` on expandable cards | 4.1.2 | High |
| Module delete button lacks `aria-label` | 4.1.2 | High |
| `<h2>` heading present | 1.3.1 | Pass |

**ComponentCard expand/collapse — keyboard inaccessible:**
- **WCAG:** 2.1.1 Keyboard
- **Severity:** Critical
- **Current:** `<CardHeader className="cursor-pointer select-none py-3" onClick={onToggle}>` — the entire card header is clickable but has no keyboard support and no `aria-expanded`.
- **Fix:** Same pattern as DeliveryPage — use a `<button>` wrapper or add `role="button"`, `tabIndex={0}`, `aria-expanded`, and `onKeyDown`.

---

### QualityPage.tsx

| Finding | WCAG | Severity |
|---------|------|----------|
| Progress bars use base-ui Progress component | 4.1.2 | Pass |
| Heading hierarchy correct | 1.3.1 | Pass |
| No interactive elements to audit | -- | N/A |

No significant issues. QualityPage is largely display-only.

---

### AuditPage.tsx

| Finding | WCAG | Severity |
|---------|------|----------|
| Native `<select>` without `<label>` | 3.3.2 | High |
| Color-only timeline dots | 1.4.1 | Medium |
| Timeline structure not semantic | 1.3.1 | Low |

**Unlabeled select filters:**
- **WCAG:** 3.3.2 Labels or Instructions
- **Severity:** High
- **Current:** Two `<select>` elements for event type and entity type filtering have no `<label>` elements. The placeholder `<option>` text ("All event types", "All entity types") serves as visual hint but is not programmatically associated.
- **Fix:** Add `<label htmlFor="event-type-filter">` and `<label htmlFor="entity-type-filter">`, or use `aria-label` on each select.

**Color-only timeline dots:**
- **WCAG:** 1.4.1 Use of Color
- **Severity:** Medium
- **Current:** `EVENT_COLORS` maps event types to colored dots (`bg-emerald-500`, `bg-blue-500`, etc.). The event type is also shown via `StatusBadge`, so this is partially mitigated, but the timeline visual relies on color.
- **Fix:** The StatusBadge provides text labels, so this is acceptable. The dot is decorative — add `aria-hidden="true"`.

---

### TaskDetailSheet.tsx

| Finding | WCAG | Severity |
|---------|------|----------|
| Sheet uses base-ui (focus trap, ARIA) | 2.1.2 | Pass |
| Status select label is `<span>` not `<label>` | 3.3.2 | High |
| Icon-only delete button lacks `aria-label` | 4.1.2 | High |
| Input fields for AC/DoD/Subtask have proper `placeholder` | 3.3.2 | Pass |
| Tab counts announced (e.g., "AC (3)") | 4.1.3 | Pass |

**Status select label not associated:**
- **WCAG:** 3.3.2 Labels or Instructions
- **Severity:** High
- **Current:** `<label className="text-xs font-medium ...">Status</label>` followed by `<select>`. The `<label>` has no `htmlFor` attribute and the `<select>` has no `id`. They are not programmatically associated.
- **Fix:** Add `htmlFor="task-status"` to the label and `id="task-status"` to the select.

---

### BoardView.tsx

| Finding | WCAG | Severity |
|---------|------|----------|
| DnD keyboard support via @dnd-kit | 2.1.1 | Partial |
| Draggable cards have both onClick and drag | 2.1.1 | Medium |
| Column headings use `<h3>` | 1.3.1 | Pass |
| Droppable columns lack ARIA drop zone attributes | 4.1.2 | Medium |

**DnD + click conflict:**
- **WCAG:** 2.1.1 Keyboard
- **Severity:** Medium
- **Current:** DraggableTaskCard has both drag listeners (from `useDraggable`) and `onClick`. The `@dnd-kit` `PointerSensor` requires mouse movement to activate drag, but keyboard users may struggle with the dual interaction model.
- **Expected:** Clear keyboard instructions for drag-and-drop. Consider adding a keyboard-accessible alternative (e.g., a status change dropdown on each card).
- **Fix:** Add `KeyboardSensor` to the sensors list in addition to `PointerSensor`. Add ARIA attributes to droppable columns.

---

### HealthPage.tsx

| Finding | WCAG | Severity |
|---------|------|----------|
| Color-only status indicators (green/red dots) | 1.4.1 | High |
| `<h1>` heading present | 1.3.1 | Pass |
| Status text accompanies color dots | 1.4.1 | Partial |

**Color-only health indicators:**
- **WCAG:** 1.4.1 Use of Color
- **Severity:** High
- **Current:** Green/red dots indicate operational/down status. Text labels ("Operational"/"Down") are present, but the Database card always shows green with no dynamic check, creating a misleading indicator.
- **Fix:** Ensure the Database card status is driven by actual health data. The pattern of text + color is acceptable when text is present.

---

### LoginPage.tsx

| Finding | WCAG | Severity |
|---------|------|----------|
| Form labels properly associated via `htmlFor` | 3.3.2 | Pass |
| Error message displayed in text | 3.3.1 | Pass |
| Error message lacks `role="alert"` | 4.1.3 | Medium |
| Submit button has clear text | 2.4.4 | Pass |

**Error message not announced:**
- **WCAG:** 4.1.3 Status Messages
- **Severity:** Medium
- **Current:** Error message renders in a `<div>` with `text-destructive` styling but no `role="alert"`. Screen readers may not announce login errors.
- **Fix:** Add `role="alert"` to the error message container.

---

### SetupPage.tsx

| Finding | WCAG | Severity |
|---------|------|----------|
| Form labels properly associated | 3.3.2 | Pass |
| Password requirements shown | 3.3.2 | Pass |
| Error message lacks `role="alert"` | 4.1.3 | Medium |

Same error message issue as LoginPage.

---

### NotFoundPage.tsx

| Finding | WCAG | Severity |
|---------|------|----------|
| Icon is decorative, lacks `aria-hidden` | 1.1.1 | Low |
| Link back to dashboard is descriptive | 2.4.4 | Pass |
| Heading present | 1.3.1 | Pass |

---

### ErrorBoundary.tsx

| Finding | WCAG | Severity |
|---------|------|----------|
| Error state has heading and description | 1.3.1 | Pass |
| Reload button is keyboard accessible | 2.1.1 | Pass |
| Error state lacks `role="alert"` | 4.1.3 | Medium |

**Error boundary not announced:**
- **WCAG:** 4.1.3 Status Messages
- **Severity:** Medium
- **Current:** When an error occurs, the error UI replaces content without announcing the change to screen readers.
- **Fix:** Add `role="alert"` to the error card container.

---

### StatusBadge.tsx

| Finding | WCAG | Severity |
|---------|------|----------|
| Text label always present alongside color | 1.4.1 | Pass |
| Colored dot is decorative | 1.1.1 | Low |

The StatusBadge pattern (text + color dot) is acceptable. The dot should be marked `aria-hidden="true"` since the text label conveys the meaning.

---

### PriorityDot.tsx

| Finding | WCAG | Severity |
|---------|------|----------|
| Has `aria-label` and `role="img"` | 4.1.2 | Pass |
| Tooltip provides additional context | -- | Pass |
| `tabIndex={0}` makes it focusable | 2.1.1 | Pass |

No issues. This is a well-implemented accessible component.

---

### AgentAvatar.tsx

| Finding | WCAG | Severity |
|---------|------|----------|
| AvatarImage has `alt={name}` | 1.1.1 | Pass |
| AvatarFallback has initials | 1.1.1 | Pass |
| Status dot has no accessible label | 4.1.2 | Medium |

**Status dot not announced:**
- **WCAG:** 4.1.2 Name, Role, Value
- **Severity:** Medium
- **Current:** The colored status dot (working/idle/blocked/offline/stale) is purely visual with no `aria-label` or screen reader text.
- **Fix:** Add `<span className="sr-only">Status: {status}</span>` after the status dot.

---

### ActorBadge.tsx

| Finding | WCAG | Severity |
|---------|------|----------|
| Icon + text label present | 1.1.1 | Pass |
| Badge color + text | 1.4.1 | Pass |

No issues.

---

### ClarificationBanner.tsx

| Finding | WCAG | Severity |
|---------|------|----------|
| Decorative icon lacks `aria-hidden` | 1.1.1 | Low |
| "Answer" button has descriptive text | 2.4.4 | Pass |
| Blocking state conveyed by color AND text | 1.4.1 | Pass |

---

### ReviewVerdictCard.tsx

| Finding | WCAG | Severity |
|---------|------|----------|
| Confidence bar is visual-only, no ARIA | 4.1.2 | Medium |
| Verdict icon + text label | 1.4.1 | Pass |

**Confidence progress bar:**
- **WCAG:** 4.1.2 Name, Role, Value
- **Severity:** Medium
- **Current:** The confidence bar is a `<div>` with inline width styling. No `role="progressbar"`, `aria-valuenow`, `aria-valuemin`, `aria-valuemax`. Screen readers cannot perceive the confidence level.
- **Fix:** Add `role="progressbar" aria-valuenow={confidence * 100} aria-valuemin={0} aria-valuemax={100} aria-label="Confidence"` to the bar container.

---

### DataTable.tsx

| Finding | WCAG | Severity |
|---------|------|----------|
| Sort headers clickable via `<th onClick>` | 2.1.1 | High |
| No `aria-sort` on sorted columns | 4.1.2 | Medium |
| Row click has no keyboard handler | 2.1.1 | High |
| Density toggle button accessible | 2.1.1 | Pass |

**Sortable headers not keyboard accessible:**
- **WCAG:** 2.1.1 Keyboard
- **Severity:** High
- **Current:** Column headers with `onClick` for sorting have `cursor-pointer` styling but no `tabIndex` or `onKeyDown`. The sort direction arrows are visual only.
- **Fix:** Add `tabIndex={0}`, `role="columnheader"`, `aria-sort={sortDirection}` and `onKeyDown` handler.

**Row click without keyboard:**
- **WCAG:** 2.1.1 Keyboard
- **Severity:** High
- **Current:** Same pattern as ProjectTable — rows with `onClick` but no keyboard support.

---

### DataTablePagination.tsx

| Finding | WCAG | Severity |
|---------|------|----------|
| Page number buttons lack descriptive labels | 2.4.4 | Medium |
| Navigation buttons use Tooltip + icon | 4.1.2 | Pass |
| Select for page size accessible | 3.3.2 | Pass |

**Page number buttons:**
- **WCAG:** 2.4.4 Link Purpose
- **Severity:** Medium
- **Current:** Page number buttons show just "1", "2", "3" etc. Screen readers announce "button 2" without context.
- **Fix:** Add `aria-label={`Page ${page}`}` to each page button.

---

### EmptyState.tsx

| Finding | WCAG | Severity |
|---------|------|----------|
| Decorative icon lacks `aria-hidden` | 1.1.1 | Low |
| Title uses `<h3>` — good heading | 1.3.1 | Pass |
| Action button has descriptive text | 2.4.4 | Pass |

---

### ErrorState.tsx

| Finding | WCAG | Severity |
|---------|------|----------|
| Decorative icon lacks `aria-hidden` | 1.1.1 | Low |
| Title uses `<h3>` | 1.3.1 | Pass |

---

### PageSkeleton.tsx

| Finding | WCAG | Severity |
|---------|------|----------|
| No `aria-busy` or `role="status"` | 4.1.3 | Medium |
| No sr-only loading announcement | 4.1.3 | Medium |

---

### SearchInput.tsx

| Finding | WCAG | Severity |
|---------|------|----------|
| Clear button lacks accessible label | 4.1.2 | Medium |
| `type="search"` provides semantics | 1.3.1 | Pass |

**Clear button:**
- **WCAG:** 4.1.2 Name, Role, Value
- **Severity:** Medium
- **Current:** The X button has no `aria-label` or `sr-only` text. Screen readers announce it as just "button".
- **Fix:** Add `aria-label="Clear search"` to the clear button.

---

### ShortcutsDialog.tsx

| Finding | WCAG | Severity |
|---------|------|----------|
| Dialog uses base-ui (focus trap, ARIA) | 2.1.2 | Pass |
| Keyboard shortcuts displayed visually | -- | Pass |
| `<kbd>` elements are semantic | 1.3.1 | Pass |

No issues.

---

### ConfirmDialog.tsx

| Finding | WCAG | Severity |
|---------|------|----------|
| Dialog uses base-ui with proper ARIA | 4.1.2 | Pass |
| DialogDescription present | 4.1.2 | Pass |
| Cancel/Confirm buttons clearly labeled | 2.4.4 | Pass |

No issues. Well-implemented.

---

### CommandPalette.tsx

| Finding | WCAG | Severity |
|---------|------|----------|
| Uses cmdk library (keyboard navigable) | 2.1.1 | Pass |
| Wrapped in Dialog (focus trapped) | 2.1.2 | Pass |
| Search results have entity type label | 4.1.2 | Pass |

No issues. The cmdk library provides excellent keyboard navigation.

---

### EntityFormDialog.tsx

| Finding | WCAG | Severity |
|---------|------|----------|
| Labels properly associated via `htmlFor` | 3.3.2 | Pass |
| Error messages displayed in text | 3.3.1 | Pass |
| Form-level error lacks `role="alert"` | 4.1.3 | Medium |
| Required fields marked with asterisk | 3.3.2 | Pass |
| Textarea has no character count/limit | -- | Low |

**Form-level error not announced:**
- **WCAG:** 4.1.3 Status Messages
- **Severity:** Medium
- **Current:** `errors._form` renders as `<p className="text-sm text-destructive">` without `role="alert"`.
- **Fix:** Add `role="alert"` to form-level error messages.

---

### Activity Feed & Agent Summary (Dashboard)

| Finding | WCAG | Severity |
|---------|------|----------|
| Uses hardcoded sample data (not accessible concern) | -- | N/A |
| ActorBadge + StatusBadge provide text | 1.4.1 | Pass |
| Activity items are links with descriptive text | 2.4.4 | Pass |

---

### use-hotkeys.ts

| Finding | WCAG | Severity |
|---------|------|----------|
| Correctly skips input/textarea/select | 2.1.1 | Pass |
| Sequence keys have timeout (1s) | 2.1.1 | Pass |
| Hotkey descriptions not exposed to AT | 4.1.2 | Low |

No critical issues. The input-skip logic is well implemented.

---

### index.css

| Finding | WCAG | Severity |
|---------|------|----------|
| `:focus-visible` with 2px solid outline | 2.4.7 | Pass |
| `prefers-reduced-motion` respected | 2.3.3 | Pass |
| Color contrast: primary #2563eb on bg #f8fafc | 1.4.3 | Pass (5.18:1) |
| Color contrast: muted-foreground #64748b on bg #f8fafc | 1.4.3 | Borderline (4.63:1) |
| Dark mode: primary #60a5fa on bg #0a0a0f | 1.4.3 | Pass (7.24:1) |
| Dark mode: muted-foreground #94a3b8 on bg #0a0a0f | 1.4.3 | Pass (6.96:1) |
| Custom scrollbar 6px width | 2.5.8 | Low |

**Muted foreground contrast (light mode):**
- **WCAG:** 1.4.3 Contrast (Minimum)
- **Severity:** Low (borderline)
- **Current:** `--color-text-muted: #64748b` on `--color-bg: #f8fafc` = 4.63:1. This passes AA for normal text (4.5:1) but has minimal margin.
- **Note:** When muted text is used on `--color-surface: #ffffff`, the contrast drops to 4.48:1, which **fails** AA.
- **Fix:** Darken muted-foreground to `#5f6f7e` (5.0:1 on white) for safety margin.

---

## Keyboard Navigation Audit

### What Works

| Pattern | Status |
|---------|--------|
| Skip navigation link | Implemented and functional |
| Sidebar navigation | Full keyboard support via base-ui |
| Dialogs/Sheets | Focus trap via base-ui, Esc to close |
| Dropdown menus | Full arrow key navigation via base-ui |
| Select components | Keyboard navigation via base-ui |
| Tabs | Arrow key navigation via base-ui |
| Command palette (Ctrl+K) | Full keyboard via cmdk |
| Hotkeys (Ctrl+J, ?, G+D, etc.) | Working with input field protection |
| Form inputs and buttons | Standard browser keyboard support |
| Sidebar toggle (Ctrl+B) | Working |

### What Does Not Work

| Pattern | Component | Issue |
|---------|-----------|-------|
| Project table row navigation | ProjectTable.tsx | `<TableRow onClick>` — no keyboard |
| Feature section expand/collapse | DeliveryPage.tsx | `<div onClick>` — no keyboard |
| Task table row navigation | DeliveryPage.tsx | `<TableRow onClick>` — no keyboard |
| Component card expand/collapse | StructurePage.tsx | `<CardHeader onClick>` — no keyboard |
| Module delete button | StructurePage.tsx | Icon button — no `aria-label` |
| Sort headers | DataTable.tsx | `<th onClick>` — no keyboard |
| DataTable row click | DataTable.tsx | `<tr onClick>` — no keyboard |
| Board drag-and-drop | BoardView.tsx | No `KeyboardSensor` configured |

---

## Color Contrast Audit

### Light Mode

| Element | Foreground | Background | Ratio | Pass? |
|---------|-----------|------------|-------|-------|
| Body text | #0f172a | #f8fafc | 15.4:1 | Yes |
| Primary button text | #ffffff | #2563eb | 5.18:1 | Yes |
| Muted text | #64748b | #f8fafc | 4.63:1 | Barely |
| Muted text on card | #64748b | #ffffff | 4.48:1 | **No** |
| Status dot (backlog) | #94a3b8 | #ffffff | 2.73:1 | N/A (decorative) |
| Destructive text | #ef4444 | #f8fafc | 3.94:1 | **No** (normal text) |
| Destructive on bg | #ef4444 | #ffffff | 3.93:1 | **No** (normal text) |

### Dark Mode

| Element | Foreground | Background | Ratio | Pass? |
|---------|-----------|------------|-------|-------|
| Body text | #f1f5f9 | #0a0a0f | 17.8:1 | Yes |
| Primary text | #60a5fa | #0a0a0f | 7.24:1 | Yes |
| Muted text | #94a3b8 | #0a0a0f | 6.96:1 | Yes |
| Destructive text | #f87171 | #0a0a0f | 5.73:1 | Yes |

**Issues:**
1. Muted-foreground on card/surface background fails 4.5:1 in light mode
2. Destructive color (#ef4444) used as text on light backgrounds fails 4.5:1

---

## Screen Reader Audit

### Landmarks

| Landmark | Present? | Element |
|----------|----------|---------|
| `<main>` | Yes | AppShell.tsx |
| `<header>` | Yes | TopBar.tsx |
| `<nav>` (sidebar) | Partial | Sidebar uses `<nav>` implicitly via SidebarMenu `<ul>` |
| `<nav>` (breadcrumb) | Yes | BreadcrumbBar.tsx |
| Skip link | Yes | AppShell.tsx |

### Heading Hierarchy

| Page | Hierarchy | Issue |
|------|-----------|-------|
| Dashboard | h1 (UPCP in TopBar) -> h2 (Needs Attention) | Correct |
| Projects | h1 (UPCP) -> h2 (Projects in CardTitle) | Correct |
| Project Detail | h1 (project name) -> h2 (tab content headings) | Correct |
| Health | h1 (System Health) | Correct |
| Login | h1 (UPCP) | Correct |

### Missing Announcements

| Event | Should Announce | Currently |
|-------|----------------|-----------|
| Page loading | "Loading..." | Silent |
| Data loaded | Content change | Silent |
| Form submission error | "Error: ..." | Silent (no `role="alert"`) |
| Toast notification | "Success: Project created" | Depends on sonner config |
| Task status change | "Task updated" | Silent |
| Search results | "N results found" | Silent |

---

## Focus Management Audit

| Scenario | Current Behavior | Expected |
|----------|-----------------|----------|
| Tab into page | First focusable element after skip link | Correct |
| Open dialog | Focus trapped in dialog (base-ui) | Correct |
| Close dialog | Focus returns to trigger (base-ui) | Correct |
| Open sheet | Focus trapped in sheet (base-ui) | Correct |
| Command palette open | Input focused | Correct |
| Route navigation | Focus stays on sidebar | Should move to main content |
| Error boundary | No focus management | Should focus error heading |

**Route navigation focus:**
- **Issue:** When navigating between routes via sidebar links, focus stays on the clicked sidebar link. The main content area changes but screen readers are not directed to it.
- **Fix:** After route change, programmatically focus `<main>` or the page heading: `mainRef.current?.focus()` (requires `tabIndex={-1}` on `<main>`).

---

## ARIA Usage Audit

### Current ARIA Usage

| Attribute | Count | Locations |
|-----------|-------|-----------|
| `aria-label` | 3 | PriorityDot, SidebarRail, (SVG in assets) |
| `aria-hidden` | 0 | Not used in components |
| `aria-live` | 0 | Not used |
| `aria-expanded` | 0 | Not used in custom components |
| `aria-pressed` | 0 | Not used |
| `aria-sort` | 0 | Not used |
| `aria-busy` | 0 | Not used |
| `role="alert"` | 0 | Not used |
| `role="status"` | 0 | Not used |
| `role="button"` | 0 | Not used (where needed) |
| `role="progressbar"` | 0 | Not used |

### ARIA Deficiencies

The application has **almost no custom ARIA attributes**. It relies entirely on base-ui primitives for ARIA. This works well for standard widgets (dialog, select, tabs, dropdown) but leaves custom interactive patterns completely unlabeled.

---

## Remediation Priority

### P0: Critical (blocks usage for keyboard/screen reader users)

1. **ProjectTable.tsx** — Make table rows keyboard navigable
2. **DeliveryPage.tsx** — Make feature section headers keyboard navigable with `aria-expanded`
3. **DeliveryPage.tsx** — Make task table rows keyboard navigable
4. **StructurePage.tsx** — Make component card headers keyboard navigable with `aria-expanded`
5. **DataTable.tsx** — Make sort headers keyboard navigable with `aria-sort`
6. **DataTable.tsx** — Make clickable rows keyboard navigable
7. **BoardView.tsx** — Add `KeyboardSensor` for drag-and-drop

### P1: High (significant barrier)

8. **TopBar.tsx** — Add `aria-label` to notification bell with count
9. **ProjectDetail.tsx** — Add `aria-label` to edit/delete icon buttons
10. **DeliveryPage.tsx** — Add `aria-pressed` to view mode toggle
11. **AuditPage.tsx** — Add `<label>` to filter select elements
12. **TaskDetailSheet.tsx** — Associate status label with select via `htmlFor`/`id`
13. **HealthPage.tsx** — Fix color-only status indicators
14. **index.css** — Fix muted-foreground contrast on white backgrounds
15. **All icon-only buttons** — Add `aria-label` (DeliveryPage delete, StructurePage delete, etc.)

### P2: Medium (difficult but possible)

16. **All loading states** — Add `aria-busy="true"` and `role="status"` with sr-only text
17. **All error messages** — Add `role="alert"` to form errors (LoginPage, SetupPage, EntityFormDialog)
18. **ErrorBoundary** — Add `role="alert"` to error state
19. **BreadcrumbBar** — Add `aria-label="Breadcrumb"` to nav
20. **AgentAvatar** — Add sr-only status text
21. **SearchInput** — Add `aria-label="Clear search"` to clear button
22. **DataTablePagination** — Add `aria-label` to page number buttons
23. **Dashboard trend icons** — Add `aria-label` for direction
24. **ReviewVerdictCard** — Add `role="progressbar"` to confidence bar
25. **Route navigation** — Focus main content area after navigation
26. **TopBar theme toggle** — Communicate current and next theme state
27. **PageSkeleton** — Add `aria-busy="true"` to loading containers

### P3: Low (minor inconvenience)

28. **EmptyState/ErrorState** — Add `aria-hidden` to decorative icons
29. **ClarificationBanner** — Add `aria-hidden` to decorative icons
30. **NotFoundPage** — Add `aria-hidden` to decorative icon
31. **StatusBadge** — Add `aria-hidden` to decorative color dot
32. **SidebarGroupLabel** — Consider heading role
33. **index.css** — Consider wider scrollbar for motor accessibility

---

## Quick Wins

These fixes are easy to implement with high impact:

1. **Add `aria-label` to all icon-only buttons** (5 min each, ~10 buttons affected)
   - Pattern: `<Button aria-label="Edit project" ...>`
   - Affects: ProjectDetail, DeliveryPage, StructurePage, TaskDetailSheet

2. **Add `role="alert"` to error containers** (2 min each, ~4 locations)
   - Pattern: `<div role="alert" className="...">{error}</div>`
   - Affects: LoginPage, SetupPage, EntityFormDialog, ErrorBoundary

3. **Add `aria-label="Breadcrumb"` to nav** (1 line)
   - Affects: BreadcrumbBar.tsx

4. **Add `aria-hidden="true"` to decorative icons** (1 min each, ~15 icons)
   - Pattern: `<Icon aria-hidden="true" className="..." />`
   - Affects: EmptyState, ErrorState, StatusBadge dot, ClarificationBanner, NotFoundPage

5. **Fix muted-foreground contrast** (1 CSS variable change)
   - Change `--color-text-muted: #64748b` to `#5f6f7e` in light mode

6. **Add `aria-busy` to skeleton loaders** (2 min each, ~5 locations)
   - Pattern: `<div aria-busy="true" role="status"><span className="sr-only">Loading...</span>...</div>`

7. **Add `aria-label` to SearchInput clear button** (1 line)
   - Pattern: `<Button aria-label="Clear search" ...>`

8. **Make ProjectTable rows keyboard accessible** (10 min)
   - Pattern: Wrap project name in `<Link>` component inside `<TableCell>`

---

## Summary of WCAG Criteria Compliance

| Criteria | Level | Status | Notes |
|----------|-------|--------|-------|
| 1.1.1 Non-text Content | A | Partial | Decorative icons missing `aria-hidden` |
| 1.3.1 Info and Relationships | A | Partial | Missing heading roles, label associations |
| 1.3.2 Meaningful Sequence | A | Pass | Reading order matches visual |
| 1.4.1 Use of Color | A | Fail | Color-only indicators in HealthPage, AuditPage |
| 1.4.3 Contrast (Minimum) | AA | Fail | Muted text on white backgrounds |
| 1.4.4 Resize Text | AA | Pass | Tailwind responsive design |
| 1.4.11 Non-text Contrast | AA | Partial | Focus rings pass, some borders borderline |
| 2.1.1 Keyboard | A | Fail | Multiple click-only interactive elements |
| 2.1.2 No Keyboard Trap | A | Pass | Base-ui dialogs have Esc to close |
| 2.4.1 Bypass Blocks | A | Pass | Skip link implemented |
| 2.4.3 Focus Order | A | Partial | Route changes don't move focus |
| 2.4.4 Link Purpose | A | Pass | Links are descriptive |
| 2.4.6 Headings and Labels | AA | Partial | Some headings missing, some labels unassociated |
| 2.4.7 Focus Visible | AA | Pass | `:focus-visible` with 2px outline |
| 3.1.1 Language of Page | A | Pass | `html lang="en"` |
| 3.2.1 On Focus | A | Pass | No unexpected changes on focus |
| 3.2.2 On Input | A | Pass | Selects trigger expected changes |
| 3.3.1 Error Identification | A | Partial | Errors shown in text but not announced |
| 3.3.2 Labels or Instructions | A | Partial | Most labels correct, some missing |
| 4.1.2 Name, Role, Value | A | Fail | Many custom widgets missing ARIA |
| 4.1.3 Status Messages | A | Fail | No live regions for dynamic content |
