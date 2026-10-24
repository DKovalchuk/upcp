# TASK-0108 — M18 S20.1: Accessibility

**Milestone:** M18
**Sprint:** S20.1
**Points:** 8
**Spec:** SPEC-0021 §S20.1
**Status:** PARTIAL

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

## Acceptance Criteria

- [ ] BoardView has keyboard DnD via `KeyboardSensor` from @dnd-kit
- [ ] Accordion sections (FeatureSection, ComponentCard) have `aria-expanded`, `role="button"`, keyboard handlers
- [ ] BreadcrumbBar resolves project name from project ID (no raw UUIDs)
- [ ] BoardView task cards are focusable (`tabIndex={0}`) with keyboard Enter handler
- [ ] SavedViewsDropdown removes nested button, uses `DropdownMenuItem onSelect`
- [ ] All existing tests still pass
- [ ] New tests for keyboard navigation and ARIA attributes

## Technical Design

### Keyboard DnD (BoardView)

Use `KeyboardSensor` from `@dnd-kit/core` alongside existing `PointerSensor`:

```tsx
const sensors = useSensors(
  useSensor(PointerSensor),
  useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
);
```

### ARIA on Accordions

Add to `FeatureSection` and `ComponentCard`:
- `aria-expanded={isExpanded}`
- `role="button"` on clickable headers
- `onKeyDown` handler for Enter/Space

### Breadcrumb UUID Resolution

In `BreadcrumbBar`, resolve project ID to name using `useProject` hook or local cache. Display name instead of UUID.

### Focusable Task Cards

Add `tabIndex={0}` and `onKeyDown` (Enter to open) to BoardView task cards.
