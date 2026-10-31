# TASK-0160 — Doc/status sync batch (pending-задачи M10/M11, SPEC-0026, roadmap, versioning)

**Source:** отчёт по остаткам плана 2026-10-31 (после закрытия TASK-0159 /
MR !98); Дмитрий: «Хорошо, согласен. Давай доделывать оставшееся»
**Milestone:** documentation / status hygiene (не релизный)
**Spec:** mini-spec (AC ниже)
**Points:** 3
**Status:** in_progress

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

- [ ] AC1: по каждому из TASK-0077, 0078, 0079, 0080, 0081, 0082, 0083,
      0084, 0085, 0086, 0087 — таблица AC → verdict (implemented / gap) с
      evidence (file:line, имя теста); статус меняется только после сверки;
      найденные gap'и — доработка в батче (TDD) либо deviation + follow-up
      задача, решение фиксируется в файле задачи.
- [ ] AC2: SPEC-0026: в шапке зафиксированы APPROVED 2026-10-24 и факт
      реализации (ссылка на MR !56 / задачи), статус DRAFT снят.
- [ ] AC3: ROADMAP_UNIFIED.md: таблицы M16/M18/M19 не показывают PARTIAL по
      закрытым gaps; «After M20 (remaining work)» п.1-2 отмечены закрытыми.
- [ ] AC4: VERSIONING.md согласно решению Дмитрия (варианты: (a) синхронизация
      таблиц без бампа — 0.18.0/0.20.0 delivered в составе 0.19.0–0.22.0;
      (b) бамп 0.23.0 как milestone-closure; (c) отложить).
- [ ] AC5: PROJECT_STATUS.md: Current Task → TASK-0160 DONE, Queued
      актуализирован, версии/M16/M18 отражают решение по AC4.
- [ ] AC6 (если одобрено): файлы задач production hardening созданы
      (3-5 задач с AC), добавлены в PROJECT_STATUS Queued.
- [ ] Evidence: выводы верификации AC1 в этом файле (раздел «Verification»),
      команды/тесты, MR.

## Out of scope

- Релиз/бамп версий (решение по AC4 фиксируется в доках, сами
  pyproject/package.json трогаем только если выбран вариант бампа).
- Новый production-код (кроме gap-фиксов AC1, если они обнаружатся).

## Verification

_(заполняется по результатам: per-task verdict-таблицы, команды, выводы)_
