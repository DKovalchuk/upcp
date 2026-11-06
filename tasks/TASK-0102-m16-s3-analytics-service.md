# TASK-0102 — M16 Sprint 3: Analytics Service + API

**Spec:** SPEC-0019
**Milestone:** M16
**Sprint:** S18.3
**Status:** DONE (closed 2026-10-25)
**Size:** L

**Audit 2026-10-24 (evidence):** `AnalyticsService` — 4 метода ✅, API — 6
эндпоинтов (AC: 5) ✅, роутер зарегистрирован ✅, тесты проходят ✅.
**Gaps (closed 2026-10-25):**
1. **Pagination on list endpoints** → закрыто: `/analytics/agents/overview`
   (единственный неограниченный list-эндпоинт) получил `limit/offset` +
   `total` через общий `pagination_dependency` (S15.2-контракт
   `{items,total,offset,limit}`). Временные ряды (trends/velocity/
   health-history) ограничены на уровне query-параметров
   (`weeks` ge=1 le=52, `days` ge=1 le=365) — пагинация для них
   неприменима, это решение зафиксировано как AC-интерпретация.
2. **API-слой тестов** → закрыт: новый `test_analytics_api.py` — 6 тестов
   (по одному на каждый эндпоинт; overview проверяет limit/offset/total и
   сдвиг offset). Служебных тестов стало 6 (было 5, +1 на пагинацию).

## Objective

Implement analytics service with project trends, agent performance, team velocity, and health history.

## Acceptance Criteria (verified 2026-10-25)

- [x] AnalyticsService with 4 methods: get_project_trends, get_agent_performance,
      get_team_velocity, get_health_history (+ get_global_velocity,
      get_agents_overview — сверх AC)
- [x] GET /analytics/project/{id}/trends — task completion rate over time
- [x] GET /analytics/agent/{id}/performance — tasks completed, success rate, avg time
- [x] GET /analytics/project/{id}/velocity — tasks completed per week
- [x] GET /analytics/project/{id}/health-history — health score over time
- [x] GET /analytics/agents/overview — all agents summary **+ pagination**
      (`limit`/`offset`/`total` in response)
- [x] Pagination on list endpoints — see решение выше (overview пагинирован;
      временные ряды ограничены weeks/days-капами)
- [x] All existing tests pass — full suite **1021 passed** (exit 0);
      frontend 446/446 (аддитивные поля ответа совместимы)
- [x] New tests: 6 service tests + 5 API tests — **6 service + 6 API**
      (AC превышен на 1 API-тест: покрыты все 6 эндпоинтов)

## Evidence

- Red: `pytest test_analytics*` → **3 failed / 9 passed, exit 1**
  (empty → tuple contract; pagination kwarg отсутствовал; ответ overview
  без total/limit/offset)
- Green: **12 passed, exit 0**; `ruff check`/`ruff format --check` clean,
  `mypy` clean
- Full gates: backend **1021 passed** (ruff/mypy — см. счётчики выше),
  frontend **446/446 (53 files)**
- API-тесты — отдельный слой `test_analytics_api.py` (`_test_app` +
  `dependency_overrides[get_session]`, seeding через `TestSessionLocal`),
  как требовал AC («не как отдельный слой» из аудита)

## Deviations / notes (recorded per §7)

1. **AC «Pagination on list endpoints» интерпретирован узко**: пагинация
   добавлена единственному реально неограниченному list-эндпоинту
   (`/analytics/agents/overview`); временные ряды пагинировать нельзя
   (это графики), их ограничивают `weeks`/`days`-капы из коробки.
2. Service-контракт `get_agents_overview` изменён с `list` на
   `(items, total)` (S15.2-конвенция) — единственный вызывающий в Python
   (эндпоинт) и существующие тесты обновлены; фронтенд потребляет только
   `items`, аддитивные поля безопасны (проверено полным сьютом).
3. Порог AC (5 API-тестов) превышен: 6 тестов — по одному на эндпоинт.
4. Не в scope (замечено при расследовании): `get_agent_performance`
   делает `session.get(Task)` на каждый claim (N+1) — существующий
   паттерн, не трогали; кандидат в отдельную задачу, если профилирование
   покажет значимость.

## Files

| File | Action |
|------|--------|
| `backend/app/reporting/analytics.py` | MODIFY — `get_agents_overview(limit, offset) -> (items, total)` |
| `backend/app/api/v1/analytics.py` | MODIFY — overview: `pagination_dependency`, ответ `{items,total,offset,limit}` |
| `backend/tests/test_analytics.py` | MODIFY — empty → tuple-контракт, +`test_agents_overview_pagination` (6 сервисных) |
| `backend/tests/test_analytics_api.py` | CREATE — 6 API-тестов (отдельный слой) |
