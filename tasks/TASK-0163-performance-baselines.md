# TASK-0163 — Performance benchmarks: консолидация baseline + budgets + воспроизводимость

**Source:** ROADMAP_UNIFIED «After M20» п.4 (production hardening), выделено
из TASK-0160 AC6 (2026-10-31)
**Milestone:** Production hardening
**Spec:** mini-spec (AC ниже)
**Points:** 5
**Status:** pending

## Goals

Превратить разрозненные perf-артефакты в трекаемый benchmark-бюджет:
сейчас есть `tests/performance/` (runner, analyzer, locustfiles, lighthouse),
отчёты в `tests/performance/reports/load_*.md` (последние: SLO 2154/2154,
46.7 rps — TASK-0150), Lighthouse-бюджет 0.8 (`make lighthouse` —
TASK-0153), `dashboard/stats` budget (TASK-0149) — единого baseline-документа
и процедуры сравнения «текущий прогон vs baseline» нет.

## Acceptance Criteria

- [ ] AC1: `docs/testing/performance-baselines.md` создан: таблица
      SLI/SLO/budgets с числами и источником (endpoint/metric, baseline
      значение, дата снимка, ссылка на отчёт в `tests/performance/reports/`):
      mixed-scenario throughput/latency/SLO, `dashboard/stats`, Lighthouse
      score-budget, e2e perf-бюджеты (load <3s из TASK-0128) — что применимо.
- [ ] AC2: раздел «Как воспроизвести»: точные команды прогонов (locust runner,
      `make lighthouse`, analyzer) + критерий сравнения с baseline
      (что считается регрессией).
- [ ] AC3: baseline-документ связан из `docs/INDEX.md` и
      `docs/testing/INDEX`-структуры; ссылки на отчёты валидны (файлы
      существуют).
- [ ] AC4: команды воспроизведения проверены настолько, насколько среда
      позволяет (для stack-зависимых — зафиксирован prereq: compose up;
      без прогона — явно указать, что не прогонялось и почему).

## Out of scope

- CI-интеграция perf-бюджетов как hard gate (отдельное решение после
  стабилизации baseline).

## Verification

_(заполняется: команды, вывод, список baseline-строк)_
