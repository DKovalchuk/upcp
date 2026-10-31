# TASK-0161 — E2E coverage: spec↔reality sync + uncovered critical flows

**Source:** ROADMAP_UNIFIED «After M20» п.4 (production hardening), выделено
из TASK-0160 AC6 (2026-10-31)
**Milestone:** Production hardening
**Spec:** mini-spec (AC ниже)
**Points:** 5
**Status:** pending

## Goals

1. Свести `docs/testing/e2e-critical-flows.md` к реальности: документ
   описывает 3 флоу с аспирационными селекторами/test-именами, которые не
   соответствуют фактическим suites (root `tests/e2e/`: api/auth/health/
   navigation; `frontend/e2e/`: 16 spec-файлов).
2. Найти критические флоу без e2e-покрытия (например, фичи M20 — bulk
   operations, comments/audit export, notifications flow; фильтринг
   SPEC-0026 URL-sync) и закрыть их тестами.

## Acceptance Criteria

- [ ] AC1: inventory-таблица в конце задачи: критический флоу → spec-файл →
      покрыт/нет (evidence: имя теста).
- [ ] AC2: `docs/testing/e2e-critical-flows.md` отражает фактические suites
      (пути, имена тестов, команды запуска) — аспирационные сниппеты либо
      приведены к коду, либо помечены как roadmap.
- [ ] AC3: каждый выявленный непокрытый критический флоу закрыт e2e-тестом
      (red→green: тест падает/фильтруется до реализации проверки — новая
      проверка сама по себе является поведением; обоснование в отчёте).
- [ ] AC4: оба e2e-сьюта зелёные после изменений (команды + счётчики);
      регрессий против baseline нет.
- [ ] AC5: связанные доки (docs/testing/INDEX-запись при необходимости)
      обновлены.

## Out of scope

- Unit/vitest покрытие (отдельная плоскость); load/perf сценарии (TASK-0163).

## Verification

_(заполняется: команды сьютов, счётчики, inventory-таблица)_
