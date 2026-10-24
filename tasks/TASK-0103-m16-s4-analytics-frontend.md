# TASK-0103 — M16 Sprint 4: Analytics Frontend + Channel Settings UI

**Spec:** SPEC-0019
**Milestone:** M16
**Sprint:** S18.4
**Status:** PARTIAL
**Size:** L

**Audit 2026-10-24 (evidence):** `AnalyticsPage` + `TrendChart` +
`VelocityChart` + `AgentPerformanceCard` ✅, route `/analytics` ✅
(`router.tsx:263`), Channel settings UI ✅ как `ChannelsSettingsTab`
(create/delete/test; отклонение от плана: `ChannelForm`/`ChannelList`/
`NotificationChannelsPage` не создавались — реализовано одним табом).
**Gaps:**
1. **Nav-item для /analytics отсутствует** — `NAV_GROUPS` в
   `lib/constants.ts` не содержит Analytics, CommandPalette тоже; страница
   достижима только по прямому URL (недостижима из UI).
2. Нет выделенных frontend-тестов analytics (AC: 10 новых тестов);
   каналы покрыты косвенно `SettingsPage.test.tsx` (11 тестов).

## Objective

Build analytics dashboard frontend and notification channel settings UI.

## Acceptance Criteria

- [ ] Analytics dashboard page with tabs (Trends, Agents, Velocity)
- [ ] TrendChart component using Recharts
- [ ] VelocityChart component using Recharts
- [ ] AgentPerformanceCard component
- [ ] NotificationChannelSettings page in Settings
- [ ] Channel CRUD UI (create, list, delete, test)
- [ ] Responsive design (mobile + desktop)
- [ ] All existing tests pass
- [ ] New tests: 10 frontend tests

## Implementation Plan

### Step 1: Types + API Functions
- `frontend/src/types/analytics.ts` — TrendData, AgentPerformance, VelocityData
- `frontend/src/lib/api/analytics.ts` — 5 API functions
- `frontend/src/hooks/use-analytics.ts` — React Query hooks

### Step 2: Analytics Dashboard
- `frontend/src/pages/AnalyticsPage.tsx` — main page with tabs
- `frontend/src/components/analytics/TrendChart.tsx`
- `frontend/src/components/analytics/VelocityChart.tsx`
- `frontend/src/components/analytics/AgentPerformanceCard.tsx`

### Step 3: Channel Settings
- `frontend/src/pages/NotificationChannelsPage.tsx`
- `frontend/src/components/notifications/ChannelForm.tsx`
- `frontend/src/components/notifications/ChannelList.tsx`

### Step 4: Router + Navigation
- `frontend/src/router.tsx` — add /analytics route
- `frontend/src/lib/constants.ts` — add Analytics nav item

### Step 5: Tests
- `frontend/src/pages/AnalyticsPage.test.tsx`
- `frontend/src/components/analytics/*.test.tsx`
- `frontend/src/pages/NotificationChannelsPage.test.tsx`

## Files to Create/Modify

| File | Action |
|------|--------|
| `frontend/src/types/analytics.ts` | CREATE |
| `frontend/src/lib/api/analytics.ts` | CREATE |
| `frontend/src/hooks/use-analytics.ts` | CREATE |
| `frontend/src/pages/AnalyticsPage.tsx` | CREATE |
| `frontend/src/components/analytics/TrendChart.tsx` | CREATE |
| `frontend/src/components/analytics/VelocityChart.tsx` | CREATE |
| `frontend/src/components/analytics/AgentPerformanceCard.tsx` | CREATE |
| `frontend/src/pages/NotificationChannelsPage.tsx` | CREATE |
| `frontend/src/components/notifications/ChannelForm.tsx` | CREATE |
| `frontend/src/components/notifications/ChannelList.tsx` | CREATE |
| `frontend/src/router.tsx` | MODIFY |
| `frontend/src/lib/constants.ts` | MODIFY |
| `frontend/src/pages/AnalyticsPage.test.tsx` | CREATE |
| `frontend/src/pages/NotificationChannelsPage.test.tsx` | CREATE |
