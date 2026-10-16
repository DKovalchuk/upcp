# TASK-0127: Dashboard Responsive Layout

**Spec:** SPEC-0025 S25.8
**Status:** DONE (closed 2026-10-16)
**Priority:** LOW
**Effort:** 2pts

## Objective

Final layout assembly with responsive design and animations.

## Changes

### Frontend — Dashboard.tsx
- Reorganize layout into5 rows:
  1. KPI Cards (5-col)
  2. Donut (1/3) + Velocity (2/3)
  3. Attention Grid (3-col)
  4. Activity (2/3) + Agents (1/3)
  5. Portfolio Table (full width)
- Responsive breakpoints:
  - Desktop (≥1024px): full layout
  - Tablet (641-1024px): 2-col KPI, 2-col attention, stacked charts
  - Mobile (≤640px): single column everything
- Add `animate-fade-in-up` to each row with stagger delay
- Add `animate-stagger` to stat cards
- Project selector above KPI cards, sticky on scroll
- Section headers with subtle dividers
- Dark mode: test all new components in dark theme

## Acceptance Criteria

- [ ] Layout matches spec on desktop (1440px)
- [ ] Tablet layout: 2-col grids, stacked charts
- [ ] Mobile layout: single column, full-width cards
- [ ] Animations smooth, no layout shift
- [ ] Project selector sticky on scroll
- [ ] Dark mode looks correct
- [ ] No horizontal overflow on any screen size
