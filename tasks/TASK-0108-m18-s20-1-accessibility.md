# TASK-0108 — M18 S20.1: Accessibility

**Milestone:** M18
**Sprint:** S20.1
**Points:** 8
**Spec:** SPEC-0021 §S20.1
**Status:** PENDING

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
