# TASK-0103 — M16 Sprint 4: Analytics Frontend + Channel Settings UI

**Spec:** SPEC-0019
**Milestone:** M16
**Sprint:** S18.4
**Status:** DONE (closed 2026-10-25)
**Size:** L

**Audit 2026-10-24 (evidence):** `AnalyticsPage` + `TrendChart` +
`VelocityChart` + `AgentPerformanceCard` ✅, route `/analytics` ✅
(`router.tsx:263`), Channel settings UI ✅ как `ChannelsSettingsTab`
(create/delete/test; отклонение от плана: `ChannelForm`/`ChannelList`/
`NotificationChannelsPage` не создавались — реализовано одним табом).
**Gaps (closed 2026-10-25):**
1. **Nav-item для /analytics** → закрыт: `NAV_GROUPS` (System-группа,
   после Reports, icon `TrendingUp`, путь `/analytics`) + отдельная
   команда `Analytics` в CommandPalette (навигация, без shortcut —
   hotkey `G A` не существует в `HOTKEYS`; не выдумывали).
   AppSidebar потребляет `NAV_GROUPS` → ссылка появилась из реестра.
2. **Выделенные frontend-тесты analytics** → закрыто: **11 новых тестов**
   (AC: 10) — `AppSidebar.test.tsx` (2: ссылка Analytics→`/analytics`,
   группы/якорные элементы), `CommandPalette.test.tsx` +2 (команда
   Analytics; выбор → `navigate({to:'/analytics'})`), новая
   `AnalyticsPage.test.tsx` (7: skeleton, секции, trend/velocity-bars,
   agent-строки с null-avg boundary, пустые состояния, week-labels).

## Objective

Build analytics dashboard frontend and notification channel settings UI.

## Acceptance Criteria (verified 2026-10-25)

- [x] Analytics dashboard page — `components/analytics/AnalyticsPage.tsx`
      (секции вместо вкладок — см. Deviations §1; audit-accepted)
- [x] TrendChart component — `components/analytics/TrendChart.tsx`
      (custom CSS-bars — см. Deviations §2)
- [x] VelocityChart component — `components/analytics/VelocityChart.tsx`
- [x] AgentPerformanceCard component — `components/analytics/AgentPerformanceCard.tsx`
- [x] NotificationChannelSettings page in Settings — `ChannelsSettingsTab`
      (5 табов Settings, audit-accepted план-отклонение)
- [x] Channel CRUD UI (create, list, delete, test) — + **edit** закрыт в
      TASK-0109 (2026-10-25)
- [x] Responsive design — grid `grid-cols-1 lg:grid-cols-2` / responsive
      классы компонентов (audit ✅, e2e responsive-тесты TASK-0128 Part C)
- [x] All existing tests pass — full frontend suite **457/457 (55 files)**,
      oxlint 0 errors, `tsc -b` exit 0
- [x] New tests: 10 frontend tests — **11** (см. gaps выше)

## Evidence

- Red (nav): `vitest run AppSidebar + CommandPalette + AnalyticsPage` →
  **3 failed / 19 passed, exit 1** — ровно nav-гэпы: нет ссылки
  `/analytics` в сайдбаре, нет команды/навигации в палитре
  (7 AnalyticsPage-пинов — зелёные с первого запуска: компоненты уже
  были в коде)
- Green: **22 passed, exit 0** по трём файлам
- Полные гейты: vitest **55 files / 457 tests** (было 53/446 → +2 файла,
  +11 тестов), `oxlint` exit 0, `tsc -b` exit 0
- Router `/analytics` подтверждён (`router.tsx:261-266`, в списке роутов
  `:303`); рендер сайдбара проверен через `SidebarProvider` (jsdom-safe:
  matchMedia-полифилл в `src/test/setup.ts`)

## Deviations / notes (recorded per §7)

1. **«Page with tabs (Trends, Agents, Velocity)»** реализовано как одна
   прокручиваемая страница с grid-секциями — не флагалось аудитом 2026-10-24
   (компоненты ✅), вкладки не вводили задним числом.
2. **Recharts в AC** — analytics-компоненты используют лёгкие CSS-bars
   (тот же подход принят аудитом; `dashboard/VelocityChart` с Recharts
   живёт отдельно для дашборда).
3. В `CommandPalette` команде Analytics **не дали shortcut**: в `HOTKEYS`
   нет привязки для analytics, а `G A` занята agents — выдуманный
   шорткат вводил бы пользователя в заблуждение.
4. Канальный план-отклонение (без `ChannelForm`/`ChannelList`/
   `NotificationChannelsPage`) — подтверждено аудитом, не менялось.

## Files

| File | Action |
|------|--------|
| `frontend/src/lib/constants.ts` | MODIFY — Analytics в NAV_GROUPS (System, `TrendingUp`, `/analytics`) |
| `frontend/src/components/CommandPalette.tsx` | MODIFY — команда `analytics` в Navigation |
| `frontend/src/components/CommandPalette.test.tsx` | MODIFY — +2 теста (red→green) |
| `frontend/src/components/layouts/AppSidebar.test.tsx` | CREATE — 2 теста (ссылка Analytics) |
| `frontend/src/components/analytics/AnalyticsPage.test.tsx` | CREATE — 7 тестов (пины компонентов) |
