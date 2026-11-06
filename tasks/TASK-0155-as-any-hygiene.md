# TASK-0155 — `as any` test hygiene (parent: TASK-0097 audit note)

**Parent:** TASK-0097 (S16.4 polish — audit note: «`as any` в тестах снова
вырос до 89 вхождений в 15 файлах … → отдельный hygiene-item в очереди»)
**Milestone:** Этап 4 (production hardening + хвосты)
**Spec:** mini-spec по AC TASK-0097 §6.9 («`as any` count in test files
reduced by ≥80%»)
**Points:** 3
**Status:** DONE (closed 2026-10-25)

## Objective

Вернуть тестам типизированные моки (общие хелперы S16.4) и убрать
`any`-эскейпы из прод-кода; зафиксировать бюджет enforcement-тестом.

## Investigation (2026-10-25, evidence)

- Тесты: **90 вхождений `as any` в 15 файлах** (раскачка после S16.4).
- Прод-src: **4** — `hooks/use-filters.ts` ×2, `components/dashboard/ProjectSelector.tsx` ×2
  (`navigate({ search: … as any })`).
- Хелперы существуют: `src/test/helpers.ts` (`mockQueryResult<T>`,
  `mockSuccessQuery<T>`, `mockErrorQuery`, `mockLoadingQuery<T>`).

## Acceptance Criteria (verified 2026-10-25)

- [x] **Enforcement-тест** `src/test/as-any-hygiene.test.ts`:
      red (`count 90 exceeds budget 18`) → **green (2/2)**; бюджеты:
      тесты ≤18 (≥80% от 90), prod ≤4 (задокументированные эскейпы)
- [x] Тестовые `as any` → типизированные касты `as ReturnType<typeof useX>`
      (**90 → 0**; все15 файлов; маппинг мок→хук детерминирован,
      payload-литералы не менялись — механическая и безопасная замена)
- [x] Прод-src 4 эскейпа: **probe по факту tsc** → снятие кастов даёт
      **TS2322/TS2353** (`navigate({search})` принимает только
      `true | ParamsReducerFn` — роутеры зарегистрированы **без
      search-валидаторов**; `project_id` отсутствует в типе) →
      типизация требует рефактора router.tsx (validateSearch по
      маршрутам) = вне скоупа гигиены → **документированное исключение**
      (комментарии с probe-доказательством на обоих сайтах, бюджет4)
- [x] Полные гейты: vitest **466/466 (56 файлов)** (+2 enforcement),
      oxlint 0 errors, `tsc -b` exit 0
- [x] PROJECT_STATUS синхронизирован; пункт очереди зачёркнут
- [x] Отклонения зафиксированы

## Evidence

- Enforcement red: `test-file "as any" count 90 exceeds budget 18`
  (offenders-словарь по файлам) → после миграции: **2 passed**
- Миграция:15 файлов, ~90 сайтов — `mockReturnValue({…} as any)` →
  `mockReturnValue({…} as ReturnType<typeof <hook>>)` (query-моки,
  mutation-моки `{mutateAsync: vi.fn()}`, `mockFetch.mockResolvedValue`)
- Probe (prod): tsc c удалёнными кастами → 4 ошибки TS2322/TS2353 →
  касты восстановлены + сопроводительные комментарии; TSC=0 после
- Полные гейты: vitest 466/466, oxlint LINT=0, tsc -b TSC=0,
  enforcement 2/2

## Deviations / notes (recorded per §7)

1. **Замена кастов, а не переход на хелперы**: выбран cast-only
   (`ReturnType<typeof useX>`) — механический, без изменения payload-
   литералов и без новых импортов; хелперы `mockSuccessQuery<T>` и др.
   остаются рекомендованным паттерном для НОВЫХ тестов (S16.4-наследие,
   применяется в свежих тестах сессии). Метрика AC — счётчик `as any` —
   выполнена: 90 → 0.
2. **4 prod-эскейпа задокументированы** (см. AC): корневая причина —
   отсутствие `validateSearch` у роутов; follow-up: router search-
   validators typing (отдельная задача, касается router.tsx +
   потребителей search).
3. Счётчик enforcement: файл-тест исключён из скана (содержит иглу);
   бюджет считает по `src/**` (тест-файлы и prod раздельно).

## Files

| File | Action |
|------|--------|
| `frontend/src/test/as-any-hygiene.test.ts` | CREATE — бюджет-enforcement (AC) |
| `frontend/src/components/{project/DeliveryPage,StructurePage,AuditPage,ReportsPage,ProjectDetail,ClarificationsTab,ReviewsTab,BoardView,EvidenceTab,GitIntegrationPage,QualityPage}.test.tsx` | MODIFY — `as any` → typed ReturnType (11 файлов) |
| `frontend/src/components/agents/{AgentDetailPage,AgentCenterPage}.test.tsx` | MODIFY — то же (2 файла) |
| `frontend/src/components/dashboard/{AgentActivitySummary,AttentionCards}.test.tsx` | MODIFY — то же (2 файла) |
| `frontend/src/hooks/use-filters.ts` | MODIFY — документирующий комментарий к эскейпам |
| `frontend/src/components/dashboard/ProjectSelector.tsx` | MODIFY — документирующий комментарий к эскейпам |
