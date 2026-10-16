# TASK-0124: Portfolio Table

**Spec:** SPEC-0025 S25.5
**Status:** DONE (closed 2026-10-16)
**Priority:** MEDIUM
**Effort:** 3pts

## Objective

Add a portfolio overview table showing all projects with health scores.

## Changes

### Frontend
- Create API function `fetchPortfolioOverview()` in `lib/api/portfolio.ts` (already exists, wire it)
- Create hook `usePortfolioOverview()` in `hooks/use-dashboard.ts`
- Create `PortfolioTable` component using shadcn `Table`
- Columns: Project Name, Health (progress bar), Tasks (done/total), Status, Top Issue
- Health colors: ≥80 emerald, 50-79 amber, <50 red
- Click row → `/projects/:id`
- "Show more" button if >5 projects
- Only render when >1 project exists
- Empty state: hidden (not useful with0-1 projects)

## Acceptance Criteria

- [ ] Table shows all projects with correct data
- [ ] Health score color-coded correctly
- [ ] Click row navigates to project detail
- [ ] "Show more" works for >5 projects
- [ ] Hidden when 0-1 projects
- [ ] Responsive (horizontal scroll on mobile)
