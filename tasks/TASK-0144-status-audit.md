# TASK-0144 — Status-аудит: синхронизация статусов задач и планов

**Spec:** mini-spec (этот файл)
**Parent:** план 2026-10-24 (Этап 0 гигиены), после TASK-0143
**Status:** DONE
**Size:** S

## Objective

Проверить пост-мержный hard-гейт Phase B (MR !77), сверить AC 12 задач
(сроки статусов которых расходились с кодом) против реального кода и тестов,
обновить статусы с записью отклонений, поднять SPEC-0026 из DRAFT,
синхронизировать PROJECT_STATUS.md и ROADMAP_UNIFIED.md.

## Acceptance Criteria

- [x] Пост-мержный pipeline на develop проверен: pipelines 465-469 success
      на `7a22b568`, job `quality:gate` green (411s) — hard-гейт работает
- [x] Открытых MR нет; ночной pipeline 470 (schedule) — наблюдение, не отказ
- [x] Статусы сверены по AC против кода (evidence: grep/read файлов):
      12 задач — **7 DONE / 5 PARTIAL**, PENDING/IN PROGRESS не осталось
- [x] Отклонения и gaps записаны в сами файлы задач (не молча)
- [x] SPEC-0026 DRAFT → APPROVED (реализация в develop с MR !56)
- [x] PROJECT_STATUS.md + ROADMAP_UNIFIED.md синхронизированы
- [x] Evidence тестами: targeted pytest 130 passed, targeted vitest 29 passed,
      tsc --noEmit clean, lint 0 errors
- [x] Работа через feature branch + атомарные коммиты + MR

## Result (2026-10-24)

| Статус | Задачи |
|--------|--------|
| DONE | TASK-0097, 0100, 0101*, 0110, 0111, 0113*, 0114 |
| PARTIAL | TASK-0102, 0103*, 0108, 0109, 0112 |

(* — отклонения записаны в файлы задач: миграция 0020 вместо 0019;
minor-фикстура в 0113; ключевой gap 0103 — нет nav-item `/analytics`.)

**Ключевая находка:** M16 и M18 реализованы в коде глубже, чем отражал
roadmap (было 1/4 и 0/4 → фактически 2 закрытых + 2 частичных в каждой).

**Gaps → в очередь PROJECT_STATUS:** analytics nav-item + пагинация + тесты
(0102/0103), channel edit + evidence (0109), breadcrumb name-resolution +
keyboard-тесты + stale AC SavedViews (0108), engine dedup разбор (0112),
`as any` hygiene (0097).
