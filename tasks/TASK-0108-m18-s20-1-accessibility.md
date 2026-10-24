# TASK-0108 — M18 S20.1: Accessibility

**Milestone:** M18
**Sprint:** S20.1
**Points:** 8
**Spec:** SPEC-0021 §S20.1
**Status:** DONE (closed 2026-10-25)

**Audit 2026-10-24 (evidence):**
- KeyboardSensor в `BoardView.tsx:7,127` ✅
- `aria-expanded` в `DeliveryPage.tsx:299` ✅ (компоненты FeatureSection/
  ComponentCard из AC в коде отсутствуют под этими именами — аккордеон живёт
  в DeliveryPage)
- Карточки доски получают focus через dnd-kit `attributes` (spread в
  `DraggableTaskCard`, `BoardView.tsx:61`), KeyboardSensor обрабатывает
  Enter/Space ✅ (явного `tabIndex={0}` в коде нет — достигается dnd-kit'ом)
- **Gaps:** (1) BreadcrumbBar **пропускает** UUID-сегменты, но не разрешает
  имена сущностей — AC «resolve project name» не выполнен; (2) нет новых
  тестов keyboard navigation/ARIA для доски; (3) AC про SavedViewsDropdown
  устарел — компонент `SavedViewsDropdown` в кодовой базе отсутствует
  (нужно закрыть AC как removed или восстановить компонент).

## Objective

Fix accessibility gaps: keyboard DnD, ARIA on accordions, breadcrumb UUID resolution.

## Acceptance Criteria (verified 2026-10-25)

- [x] BoardView has keyboard DnD via `KeyboardSensor` from @dnd-kit
      (audit 2026-10-24; pinned by test: Enter → DragOverlay copy)
- [x] Accordion sections have `aria-expanded`, `role="button"`, keyboard
      handlers — header is a **native `<button type="button">`** (implicit
      role + native Enter/Space) with `aria-expanded`/`aria-controls`;
      pinned by test. Nested-button defect found & fixed (see Deviations)
- [x] BreadcrumbBar resolves project name from project ID (no raw UUIDs)
      — `useProject(firstUuid)` + fallback label «Project» while loading
- [x] BoardView task cards are focusable with keyboard Enter handler —
      `tabIndex: 0` + keydown listeners arrive from dnd-kit `attributes`
      spread; pinned by focus + keyboard-drag tests
- [x] SavedViewsDropdown removes nested button, uses `DropdownMenuItem
      onSelect` — **CLOSED AS REMOVED**: component does not exist in the
      codebase (grep 0 hits), AC deemed stale (see Deviations)
- [x] All existing tests still pass — full frontend suite **441/441
      (52 files)**; `tsc -b` 0; oxlint 0 errors
- [x] New tests for keyboard navigation and ARIA attributes —
      BreadcrumbBar +4 (red 4/4 → green 4/4), BoardView +3 (focus, ARIA,
      Enter→drag), DeliveryPage +1 (accordion ARIA state)

## Evidence

- Red: `vitest run BreadcrumbBar.test.tsx` → **4 failed / 4 (exit 1)**
  (name resolution, fallback label, link, no-fetch contract absent)
- Green after implementation → **4 passed (exit 0)**
- Keyboard-drag test: `fireEvent.keyDown(Enter)` → DndContext state update
  observed → DragOverlay renders 2nd copy of the task (behavioral, not
  implementation pin)
- Touched-files lint: `oxlint <5 files>` → 0 warnings / 0 errors
- Full gates: vitest **52 files / 441 tests passed**, `tsc -b` exit 0,
  oxlint exit 0 (3 warnings pre-existing in untouched files)
- React warning «`<button>` cannot contain a nested `<button>`» — gone
  after the header restructure (was emitted by DeliveryPage tests before)

## Deviations / notes (recorded per §7)

1. **AC «SavedViewsDropdown» closed as removed** (not restored): the
   component has zero references in `frontend/src` — AC is stale relative
   to the current design (task actions live in DeliveryPage/TaskDetail).
   Restoring a removed component would be a feature, not an a11y fix.
2. **Opportunistic a11y fix (in scope):** FeatureSection header was a
   `<button>` wrapping the Delete-feature `<Button>` (invalid nested
   interactive content; surfaced by React warning during the new tests).
   Restructured per ARIA accordion pattern: toggle button and action
   cluster are now siblings; `aria-expanded`/`aria-controls`/click
   behavior preserved (verified by existing expand test + new ARIA test).
3. Board card `role` is `listitem` (overriding dnd-kit's `button`) by
   design — ARIA metadata (`aria-roledescription`, `tabIndex=0`) stays;
   pinned as-is rather than changed (no AC for role).

## Technical Design (as implemented)

### Breadcrumb UUID Resolution

`BreadcrumbBar` extracts the first UUID segment from the route pathname
and resolves it via `useProject(id)` (react-query cache shared with
ProjectDetail). The crumb shows `project.name` — fallback «Project»
while loading/error — never the raw UUID. Hook is called unconditionally
(disabled when `id === ''`), before the `/` early return.

### Keyboard DnD / focusable cards

Verified as already implemented (`KeyboardSensor` + dnd-kit attributes
spread) — covered with behavioral tests instead of code changes.

### ARIA on Accordion

Native button semantics retained (`role` implicit); structure fixed so
actions are not nested inside the toggle (Deviations §2).

## Files

| File | Action |
|------|--------|
| `frontend/src/components/layouts/BreadcrumbBar.tsx` | MODIFY — resolve project name via `useProject` |
| `frontend/src/components/layouts/BreadcrumbBar.test.tsx` | CREATE — 4 tests (red→green) |
| `frontend/src/components/project/DeliveryPage.tsx` | MODIFY — accordion header restructure (nested button fix) |
| `frontend/src/components/project/DeliveryPage.test.tsx` | MODIFY — +1 ARIA state test |
| `frontend/src/components/project/BoardView.test.tsx` | MODIFY — +3 keyboard/ARIA tests |
