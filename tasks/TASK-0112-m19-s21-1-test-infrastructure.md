# TASK-0112 — M19 S21.1: Test Infrastructure

**Milestone:** M19
**Sprint:** S21.1
**Points:** 5
**Spec:** SPEC-0022 §S21.1
**Status:** DONE (closed 2026-10-25)

**Audit 2026-10-24 (evidence):** markers ✅ (`pyproject.toml:50-54` slow/
integration/unit), coverage ✅ (`@vitest/coverage-v8`, `test:coverage`,
каталог `frontend/coverage/` с cobertura), conftest импортирует все модели ✅
(`tests/conftest.py:15-23`), suites зелёные ✅ (CI 465-469).
**Gap (closed 2026-10-25):** AC «engine duplication eliminated — all test
files use shared engine» — 17/89 тест-файлов создавали собственные
`create_engine`. Разбор «dedup vs зафиксированные исключения» выполнен:
**17 → 0 миграций + 2 документированных исключения**.

## Objective

Unify test infrastructure: centralize conftest, add pytest markers, add frontend coverage.

## Acceptance Criteria (verified 2026-10-25)

- [x] **Engine duplication eliminated — all test files use shared engine
      from conftest.py** — закрыт с enforcement-тестом (см. Evidence):
      red **17 violators** → миграция всех → green; исключения только
      документированные (см. Deviations §1)
- [x] conftest.py imports all models for `create_all()` — audit ✅
      (`tests/conftest.py:15-23`)
- [x] Pytest markers added — audit ✅ (`pyproject.toml:50-54`)
- [x] Frontend `@vitest/coverage-v8` — audit ✅
- [x] All existing tests still pass — **полный сьют 1023 passed**,
      ruff `All checks passed`, mypy `no issues found in 114 source files`
- [x] `pytest --markers` shows custom markers — audit ✅

## Evidence

- **Enforcement red→green**: новый `backend/tests/test_engine_dedup.py`
  (AST-скан всех `test_*.py` под `backend/tests/` на вызовы
  `create_engine`, allowlist только для2 задокументированных исключений).
  Red: `1 failed` со списком ровно **17 нарушителей** (совпало с аудитом)
  → после миграции: green (в составе сьюта).
- **Миграции (17 файлов, три рецепта):**
  - *D-паттерн (8)*: модульные `_test_engine`+`TestSessionLocal` →
    `from tests.conftest import _override_session, _test_engine,
    _TestSession as TestSessionLocal` (шаблон `test_reporting_api.py`);
  - *B-паттерн (5)*: `_engine`+`_Session` → алиасы
    `... import _TestSession as _Session, _test_engine as _engine`
    (тела файлов не менялись);
  - *A-паттерн (4)*: локальные in-memory фикстуры/фабрики
    (`db_session` fixture, `_in_memory_db()`) удалены → conftest
    `db_session` (drop+create per test) / `_TestSession` c тем же
    drop+create-режимом.
- **Полные гейты**: backend **1023 passed** (exit 0), `ruff check backend`
  clean (после автофиксов I001/F401), `mypy backend/app` clean (114 файлов).

## Deviations / notes (recorded per §7)

1. **2 задокументированных исключения** (allowlist в enforcement-тесте):
   `test_agent_create_commit.py` и `test_auth_commit_before_respond.py` —
   сознательные сценарии с ДВУМЯ engine-инстансами (проверка
   cross-connection commit-видимости); сведение к одному движку сломало бы
   тестируемое поведение. Вне scope: live-сьюты (`tests/security/`,
   `tests/performance/`) работают с реальными БД — вне инварианта.
2. **conftest `db_session` ужесточён**: `create_all` → `drop_all` +
   `create_all` per test — свежесть, эквивалентная удаляемым локальным
   in-memory-фикстурам (коммиты на общем StaticPool-соединении иначе
   протекали бы между тестами).
3. **FK-enforcement fallout (общий движок включает `PRAGMA foreign_keys=ON`,
   локальные движки его не имели)** — три семейства правок, все red→green:
   - `test_analytics_api._seed_project_with_claims` и
     `test_analytics._setup_project`: `flush()` родителя перед ребёнком
     (без `relationship()` UOW не упорядочивает вставки в одну фазу);
   - `test_reporting._in_memory_db`: pre-seed `proj-0`/`proj-1` —
     `report.project_id` это FK, тесты обращаются к этим id;
   - **fix(quality)** (отдельный коммит): `EvidenceService.upload_file`
     теперь валидирует существование задачи ДО file-I/O → NotFound →
     **404**. Раньше: FK-off-движки принимали сирот-строку (201 с
     висячим task_id), FK-on давал unhandled IntegrityError → 500.
     Контракт эндпоинта (`except NotFound → 404`) был задуман изначально
     — проверки в сервисе просто не было; тест-контракт
     `in (201, 404)` ужесточён до `== 404`.
4. **Latent sibling НЕ исправлен** (вне red-покрытия): `EvidenceService.
   create` (POST `/tasks/{id}/evidence`) имеет тот же NIL-паттерн
   (нет проверки task → при FK-on путь с несуществующей задачей даст 500).
   Ни один тест этот путь не задевает → задокументировано как кандидат
   в follow-up (тот же паттерн, что create()-500 в TASK-0109).
5. Enforcement-тест сканирует `backend/tests/**/test_*.py`; сам он
   `create_engine` не вызывает (AST-подход игнорирует строковые литералы).

## Files

| File | Action |
|------|--------|
| `backend/tests/test_engine_dedup.py` | CREATE — AST-enforcement (AC invariant) |
| `backend/tests/conftest.py` | MODIFY — `db_session`: drop+create per test |
| `backend/tests/test_{analytics,audit,reporting,notification_channels}.py` | MODIFY — A-рецепт (fixture/factory → conftest) |
| `backend/tests/test_{delivery,gitread,quality,quality_stats,structure}.py` | MODIFY — B-рецепт (алиасы conftest) |
| `backend/tests/test_{analytics_api,audit_api,dashboard,mcp_integration,notification_channels_api,project_crud,quality_pagination,reporting_api}.py` | MODIFY — D-рецепт (conftest-импорты) |
| `backend/app/quality/service.py` | MODIFY — upload_file: task-existence → NotFound (fix(quality)-коммит) |
| `backend/tests/test_quality.py` | MODIFY — миграция + контракт `== 404` (fix(quality)-коммит) |
