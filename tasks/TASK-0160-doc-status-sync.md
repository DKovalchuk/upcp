# TASK-0160 — Doc/status sync batch (pending-задачи M10/M11, SPEC-0026, roadmap, versioning)

**Source:** отчёт по остаткам плана 2026-10-31 (после закрытия TASK-0159 /
MR !98); Дмитрий: «Хорошо, согласен. Давай доделывать оставшееся»
**Milestone:** documentation / status hygiene (не релизный)
**Spec:** mini-spec (AC ниже)
**Points:** 3
**Status:** DONE (2026-10-31 — все AC закрыты, evidence ниже)

## Goals

1. Закрыть 11 stale-статусов `pending` в TASK-0077…0087 (M10/M11,
   SPEC-0015/0016) — сверкой AC против реального кода и тестов, не слепой
   синхронизацией статусов.
2. Синхронизировать `specs/SPEC-0026-universal-filtering.md` (файл DRAFT,
   PROJECT_STATUS уже фиксирует APPROVED 2026-10-24; фильтринг смержен).
3. Синхронизировать `ROADMAP_UNIFIED.md`: таблицы M16/M18/M19 и раздел
   «After M20» с фактически закрытыми gaps (TASK-0102/0103/0108/0109/0112/
   0154/0155/0156).
4. Разрешить статусы версий 0.18.0 (M16) и 0.20.0 (M18) в `VERSIONING.md`
   — по решению Дмитрия (см. AC4).
5. Обновить `PROJECT_STATUS.md` (Current Task, Queued, версии).
6. production hardening (roadmap «After M20» п.4) декомпозировать в файлы
   задач — по решению Дмитрия (см. AC6).

## Acceptance Criteria

- [x] AC1: по каждому из TASK-0077, 0078, 0079, 0080, 0081, 0082, 0083,
      0084, 0085, 0086, 0087 — таблица AC → verdict (implemented / gap) с
      evidence (file:line, имя теста); статус меняется только после сверки;
      найденные gap'и — доработка в батче (TDD) либо deviation + follow-up
      задача, решение фиксируется в файле задачи.
- [x] AC2: SPEC-0026: в шапке зафиксированы APPROVED 2026-10-24 и факт
      реализации (ссылка на MR !56 / задачи), статус DRAFT снят.
- [x] AC3: ROADMAP_UNIFIED.md: таблицы M16/M18/M19 не показывают PARTIAL по
      закрытым gaps; «After M20 (remaining work)» п.1-2 отмечены закрытыми.
- [x] AC4: VERSIONING.md согласно решению Дмитрия (варианты: (a) синхронизация
      таблиц без бампа — 0.18.0/0.20.0 delivered в составе 0.19.0–0.22.0;
      (b) бамп 0.23.0 как milestone-closure; (c) отложить).
- [x] AC5: PROJECT_STATUS.md: Current Task → TASK-0160 DONE, Queued
      актуализирован, версии/M16/M18 отражают решение по AC4.
- [x] AC6 (если одобрено): файлы задач production hardening созданы
      (3-5 задач с AC), добавлены в PROJECT_STATUS Queued.
- [x] Evidence: выводы верификации AC1 в этом файле (раздел «Verification»),
      команды/тесты, MR.

## Out of scope

- Релиз/бамп версий (решение по AC4 фиксируется в доках, сами
  pyproject/package.json трогаем только если выбран вариант бампа).
- Новый production-код (кроме gap-фиксов AC1, если они обнаружатся).

## Verification

**AC1 — TASK-0077…0087 (11 файлов):** пер-AC верификация 4 параллельными
read-only агентами против кода/тестов → все 11 → **DONE** (статусы и
deviations зафиксированы в самих файлах задач). Гэпы доработаны red→green:

| Gap | Решение | Evidence |
|-----|---------|----------|
| 0078: нет HTTP-тестов evidence-переходов | +9 тестов (200/404/409) | `backend/tests/test_quality_api_transitions.py` |
| 0079: нет HTTP-тестов review-round lifecycle | +10 тестов | тот же файл |
| 0080: submit-review не переходил задачу | transition → `ready_for_review` (red 5 failed → green 24) | `app/quality/service.py` + 5 тестов |
| 0082: кнопка Submit-for-review не подключена | кнопка + guard-allowlist + 400-UX (red 4 failed → green 16/16) | `ReviewsTab.tsx/.test.tsx`, `use-quality.ts` |
| 0083: 4 секции attention только empty-path | +5 positive/boundary HTTP-тестов | `test_attention_sections_positive.py` |
| 0087: нет route-теста health, 404 мёртв | red `200 == 404` → existence-check fix | `test_health_route.py`, `dashboard.py` |
| 0085: нет HTTP-тестов (audit T2) | +10 тестов + route-contract против 404-класса | `test_notification_api.py` |
| 0085: мёртвые пути perf-сценария | `mark-all-read`→`read-all`, 3 analytics-пути → реальные роуты (red → green 10/10) | `scenario_dashboard.py`, PRD |
| 0086: нет тестов колокольчика | +3 теста (dropdown/mark-read/empty) | `NotificationBell.test.tsx` |

Найденные баги (фикс в батче): **verdict-эндпоинт 500** (int `confidence`
vs `dict[str, str | None]`) — `quality.py`; **health 404** для неизвестного
проекта — `dashboard.py`. Наблюдение вне AC: 500 на unknown parent-task
(fk) в `POST .../review-rounds|evidence` → follow-up в Queued.

**AC2 — SPEC-0026:** синхронизирован ранее (Status APPROVED 2026-10-24 +
примечание о реализации в !56); в батче проверено — правок не потребовалось.

**AC3 — ROADMAP_UNIFIED:** M16/M18/M19 таблицы + exit criteria → DONE,
After-M20 п.1-3 закрыты, п.4 → TASK-0161…0163 (commit a97401e).

**AC4 — VERSIONING (решение Дмитрия 2026-10-31: синхронизация без бампа):**
0.18.0/0.20.0 закрыты «без отдельного релиза — delivered в 0.19.0–0.22.0»;
диаграмма `done*` + сноска, секции спринтов → DONE, Version History обновлён
(commit a97401e). `pyproject`/`package.json` не тронуты (0.22.0).

**AC5 — PROJECT_STATUS:** Current Task → TASK-0160, Queued → TASK-0161…0164.

**AC6 — hardening декомпозиция (одобрено):** TASK-0161 (e2e coverage),
TASK-0162 (deployment guide), TASK-0163 (perf baselines) созданы;
находки O1/O4 нотификаций → TASK-0164 (auth-sensitive, эскалация §10).

**Итоговые гейты (2026-10-31, ветка TASK-0160):**
- backend: `.venv/bin/python -m pytest backend/tests -q` → **1089 passed,
  0 failed, coverage 89.45%**; `ruff check` → clean; `mypy backend/app` →
  **114 files, no issues**.
- frontend: `npm test -- --run` → **480/480 (57 files)**; `tsc --noEmit`
  (app+node) → 0; `npm run lint` (oxlint) → 0 errors (3 pre-existing warns).
- Отклонения/наблюдения зафиксированы в файлах задач 0078/0080/0082/0083/
  0084/0085 и в TASK-0164.
