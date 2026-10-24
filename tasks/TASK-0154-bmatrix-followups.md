# TASK-0154 — B-matrix follow-ups: 6 blocked rows closure (parent: TASK-0128)

**Parent:** TASK-0128 (dashboard testing) — 6 blocked rows из B-матрицы,
задокументированные как follow-ups 2026-10-17
**Milestone:** Этап 4 (production hardening + хвосты)
**Spec:** SPEC-0025 (dashboard) — mini-spec по строкам матрицы
**Points:** 5
**Status:** DONE (closed 2026-10-25)

## Objective

Закрыть 6 заблокированных строк B-матрицы TASK-0128: clamp/rounding/
навигация в dashboard-компонентах + done/total-схема portfolio.

## Items & Acceptance Criteria (verified 2026-10-25)

Строки матрицы (TASK-0128-dashboard-testing.md):

- [x] **B3.5** «negative count → shows 0» — `Dashboard.tsx`: health_score
      clamp к [0..100]; **missing → 100 сохранён** (B3.6/B3.7 — принятые
      пины документируют этот fallback, менять их вне scope)
- [x] **B6.4** «counts with decimals → rounded» — TaskDistributionDonut:
      `Math.round` в маппинге данных **до** фильтра `>0` (2.4→2, 3.6→4;
      центр-итог и легенда — только целые)
- [x] **B12.7 + B13.7** «"30/36" / "0/0"» — backend portfolio добавляет
      `tasks_done`/`tasks_total` (счётчики per-project из того же batch-
      запроса, без N+1), `task_count` **сохранён аддитивно**
      (TASK-0124-потребители не тронуты); frontend-тип +
      `PortfolioTable` рендерит `done/total`
- [x] **B18.10** «click agent → /agents/:id» — строка агента обёрнута в
      `Link to="/agents/$agentId" params={...}` (typed-route контракт)
- [x] **B19.7** «progress >100 → capped at 100» — `clampPercent` [0..100]
      для ширины и отображения (negative → 0 включительно)
- [x] **B15.3 + B15.4 (ProjectSelector)** — `project_id`, отсутствующий в
      загруженном списке (unknown или не-UUID), нормализуется в «All»
      (membership-based проверка: фикстуры `p1`-стиля и реальные UUID
      работают одинаково)

Общие AC:

- [x] Red-тесты на каждый item (падали до правки) → green — **red 9 FE +
      2 BE → green**: целевые 5 FE-файлов + matrix_ab
- [x] Полные гейты: vitest **464/464 (55 файлов)**, oxlint 0 errors,
      `tsc -b` exit 0; backend **1022 passed**, ruff check/format clean,
      mypy clean
- [x] PROJECT_STATUS синхронизирован; строка очереди зачёркнута
- [x] Отклонения зафиксированы (см. ниже)

## Evidence

- Red (FE): `9 failed / 102 passed, exit 1` — ровно новые строки: B3.5 ×2,
  B6.4, B18.10, B19.7, B12.7, B13.7, B15.3, B15.4
- Red (BE): `2 failed / 15 passed, exit 1` — A8.3-контракт (поля
  отсутствовали) + value-тест
- Green: целевые файлы — 5/5 FE-файлов (AgentActivity 14/14) + matrix_ab
  **17 passed**; полные сьюты: FE 464/464, BE 1022
- Фиксации по ходу: (a) AgentActivitySummary требовал мока роутера в
  тесте (компонент теперь использует `Link` — паттерн Dashboard.test);
  (b) typed-route ошибка tsc → `to="/agents/$agentId" + params`
  (вместо template-строки); (c) ruff format применён заранее (pre-commit
  stash-conflict избегается)

## Deviations / notes (recorded per §7)

1. **B3.5 vs B3.6/B3.7**: clamp только для значений; missing/null → 100
   оставлен как ранее принятый контракт (PROJECT_STATUS-заметка про
   «маскирование» `?? 100` не переопределяет явные пины B3.6/B3.7).
2. **`task_count` сохранён** рядом с новыми полями (аддитивный контракт;
   A8.5-тест на сумму сумм продолжает работать).
3. ProjectSelector: membership-нормализация вместо строгого UUID-формата —
   фикстуры тестов используют не-UUID id (`p1`), обе строки матрицы
   (unknown/non-UUID → All) покрыты одним механизмом.
4. Вне scope: debounce B15.5 и «project deleted» B15.6 — уже имели
   покрытие/документированное поведение.

## Files

| File | Action |
|------|--------|
| `frontend/src/components/Dashboard.tsx` | MODIFY — health clamp [0..100] |
| `frontend/src/components/Dashboard.test.tsx` | MODIFY — +2 теста (B3.5) |
| `frontend/src/components/dashboard/TaskDistributionDonut.tsx` | MODIFY — round before filter |
| `frontend/src/components/dashboard/TaskDistributionDonut.test.tsx` | MODIFY — +1 тест (B6.4) |
| `frontend/src/components/dashboard/AgentActivitySummary.tsx` | MODIFY — Link `/agents/$agentId` + clampPercent |
| `frontend/src/components/dashboard/AgentActivitySummary.test.tsx` | MODIFY — router-mock +2 теста (B18.10/B19.7) |
| `frontend/src/components/dashboard/ProjectSelector.tsx` | MODIFY — membership-fallback (B15.3/B15.4) |
| `frontend/src/components/dashboard/ProjectSelector.test.tsx` | MODIFY — B15.3/B15.4 ожидания «All» |
| `frontend/src/components/dashboard/PortfolioTable.tsx` | MODIFY — `done/total` вместо task_count |
| `frontend/src/components/dashboard/PortfolioTable.test.tsx` | MODIFY — фикстуры + B12.7/B13.7 |
| `frontend/src/types/dashboard.ts` | MODIFY — `tasks_done`, `tasks_total` |
| `backend/app/reporting/portfolio.py` | MODIFY — per-project done/total счётчики |
| `backend/tests/test_dashboard_matrix_ab.py` | MODIFY — A8.3 контракт + value-тест, док-заметка |
