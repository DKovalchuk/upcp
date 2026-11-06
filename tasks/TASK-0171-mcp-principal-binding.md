# TASK-0171 — MCP principal binding: agent_id из контекста, не из аргументов

**Source:** SPEC-0028 §3.4 (S28.4), finding 4 (critical); Dmitry
2026-11-02 («Для чего мы делали аутентификацию?»)
**Milestone:** auth rework (SPEC-0028 batch)
**Spec:** SPEC-0028 §3.4, AC5 (+D5 inventory)
**Points:** 5
**Status:** DONE (реализация завершена 2026-11-04, gates зелёные — см. Evidence)

## Context

`AuthMiddleware` выставляет `request.state.agent_id`, но
`handle_jsonrpc` (`mcp/server.py`) вообще не получает Starlette
`Request` — состояние теряется на границе. MCP-инструменты принимают
`agent_id` **из аргументов вызова** (`mcp/tools.py:591+`): любой
аутентифицированный агент может claim/release/heartbeat от имени
другого агента. Аутентификация есть, привязки принципала → действие нет.

## Goals

1. Принципал из agent_auth (SPEC-0028 S28.3) провайдится в JSON-RPC
   dispatch: роут `/mcp` получает `Request`, `call_tool(...)` принимает
   principal явно (передача контекста — не глобальные mutable-переменные).
2. `agent_id` в аргументах инструмента сверяется с принципалом:
   несовпадение → отказ (403-эквивалент JSON-RPC error + structured
   warning + span attrs); совпадение → работает. Для user-JWT-вызовов
   (если D5 оставит dual-accept) — политика: только явные admin-инструменты.
3. Инвентаризация вызывающих `/mcp` (Bearer vs X-Agent-Token) — решение
   D5 (tighten до agent-only либо временный dual-accept с tracked-задачей).
4. Убрать попутные `SessionLocal`-фолбэки в `mcp/tools.py`/`context_pack.py`
   в пользу сессии запроса (перекликается с SPEC-0029 §8).

## Test design (совместная проработка до кода — SPEC-0028 §6 / D6)

- **Behavior:** tools/call от агента A с `agent_id=A` — успех; с
  `agent_id=B` — отказ; без аутентификации — 401 ещё на входе в `/mcp`;
  действия агента пишутся в аудит от имени А.
- **Boundaries:** инструменты без `agent_id` в аргументах (profile, list);
  инструменты, требующие user-контекст (если есть); двойной вызов
  параллельно (контекст не «протекает» между запросами — проверка
  contextvar-изоляции).
- **Conditions:** auth enabled; agent active/revoked на входе; D5-режим
  (только ключ / dual-accept).
- **AC:** SPEC-0028 AC5 (spoofing-отказ), AC4 для `/mcp` (enumeration
  включает MCP-ручки).
- **Matrix:**
  - unit: сверка принципала vs аргумента (позитив/негатив/равенство);
    JSON-RPC error-shape.
  - integration: настоящий `POST /mcp` двумя агентами (A пытается быть
    B → отказ; A корректно → success); изоляция контекста между
    параллельными запросами.
  - negative-класс (прежний пропуск): «аутентифицированный, но чужой
    принципал» — покрыть ВСЕ инструменты, принимающие `agent_id`
    (параметризация по списку инструментов).

## Decomposition

| # | Item | Depends |
|---|---|---|
| 1 | Инвентаризация вызывающих `/mcp` + инструментов с `agent_id` (red-тесты spoofing) | 0170 |
| 2 | Провижининг принципала в dispatch + сверка `agent_id` | 1 |
| 3 | Session-fallback cleanup в mcp | 2 |
| 4 | Evidence: spoofing-матрица зелёная, полный прогон | 3 |

## Evidence (2026-11-04, branch `feature/TASK-0168-api-surface-registry`)

Коммиты (red → green, атомарные):
`8f16330 test(mcp): principal-binding spoofing matrix — RED (TASK-0171)` →
`9052061 feat(mcp): bind tool-call agent_id to the authenticated principal (TASK-0171)`.

### Red → Green

- **RED** (тесты написаны ДО реализации; файл импортирует только
  pre-existing символы → собирается и падает ассертами):
  `9 failed, 9 passed` — 6 spoof-кейсов (по одному на каждый
  инструмент с `agent_id`), missing-principal, observability
  (warning+span), concurrent-spoof. Пасс-часть — characterization:
  inventory-pin, 6×A→A (vacuous до реализации), 401-на-входе
  (закреплено TASK-0170), hermetic-escape.
- **GREEN**: targeted `18 passed`; все гейты — таблица ниже.

### Инвентарь инструментов с `agent_id` (AC; источник — схемы `get_tools()`)

| # | Tool | required | A→A (позитив) | A→B (спуф) |
|---|------|----------|---------------|------------|
| 1 | `claim_task` | task_id, agent_id | pass | -32001 |
| 2 | `release_task` | task_id, agent_id | pass | -32001 |
| 3 | `heartbeat_task` | task_id, agent_id, progress_percent, current_step, next_step | pass | -32001 |
| 4 | `request_clarification` | task_id, agent_id, question | pass | -32001 |
| 5 | `submit_task_for_review` | task_id, agent_id | pass | -32001 |
| 6 | `get_agent_inbox` | agent_id | pass (полный: `result.is_error=false`) | -32001 |

Параметризация негативного теста строится из `AGENT_ID_TOOLS`,
вычисленного на импорте из `get_tools()`; отдельный пин
`test_agent_id_tool_inventory_matches_expected` ловит дрейф инвентаря.
Вне инвентаря: `answer_clarification` (`answered_by`),
`attach_evidence` (`created_by_id`) — equality-проверка на них не
распространяется (решённое правило «аргументы, названные agent_id»;
см. Risks).

### Binding-rule ветки (`mcp/server.py::_enforce_principal_binding`)

| `disable_auth` | Принципал в `request.state` | `agent_id` (аргумент/схема) | Исход |
|---|---|---|---|
| true (hermetic) | — | — | SKIP — legacy-поведение (пин hermetic-escape) |
| false | отсутствует | — | `-32001 "Forbidden: no authenticated principal"` (fail-closed для mis-mount) |
| false | есть | равен принципалу (string compare) | pass → handler |
| false | есть | не равен / объявлен в схеме, но не передан | `-32001 "Forbidden: agent identity mismatch"` + warning + span |
| false | есть | не объявлен и не передан | pass (вне правила) |

- Проверка только для метода `tools/call`, до `call_tool` (отказ не
  смешивается с `result.is_error` хендлера); отказ — штатный
  `JSONRPCResponse.error` внутри HTTP 200 (protocol-correct).
- Наблюдаемость: `logger.warning(extra={"action":
  "auth.principal_mismatch", "entity_type": "agent"})` с
  tool/principal/reason в message; span-attrs
  `upcp.auth.principal_mismatch=true` + `upcp.auth.sub` (lazy otel
  import — паттерн `agent_auth._observe_scope_denial`).
- Принципал берётся напрямую из `request.state` (zero new identity
  imports в dispatch; blanket TASK-0170 пишет его до handler).
- Fail-closed сценарий: в production-mount «auth on + нет принципала»
  недостижим (blanket/gate → 401 раньше) — ветка закреплена через
  documented seam: scope-gate выключен `app.dependency_overrides`,
  без blanket (симуляция mis-mounted роутера) → -32001.
- Параллель-изоляция: 4 потока / 2 агента, каждый запрос видит только
  свой принципал (2× pass + 2× spoof); собственный file-backed engine
  (см. отклонение 6); стабильно 5/5 повторов.

### Gates (последние строки)

| Gate | Результат |
|---|---|
| targeted (новый файл) | RED **9 failed, 9 passed** → GREEN **18 passed** |
| `test_auth_enumeration.py` + `test_context_boundaries.py` (без правок — файлы не тронуты) | **25 passed** |
| существующие mcp×6 + context_pack + agent_surface_auth | **109 passed** |
| `test_engine_dedup.py` | **1 passed** (исключение задокументировано) |
| FULL `pytest backend/tests -q -n auto` | **1275 passed, 0 failed, Total coverage: 90.58%** (бейзлайн 1257 / 90.41%) |
| `ruff check backend` | All checks passed! |
| `ruff format --check` (мои 3 файла) | 3 files already formatted |
| `mypy backend/app` | Success: no issues found in 119 source files |

Полный прогон С untracked-файлами сиблинга TASK-0172 (их red-фаза в
общем checkout): +184 failing/error — `test_rbac_gates_coverage.py` (180)
и `test_rbac_role_gates.py` (4 failed + 5 errors), к TASK-0171 не
относятся; судить по 0 failures на моей части (запуск с `--ignore` этих
двух файлов даёт 1275/0).

### Отклонения (зафиксированы)

1. **Decomposition item 3 (Session-fallback cleanup) НЕ выполнен** —
   `mcp/tools.py`/`context_pack.py` `SessionLocal`-фолбэки не тронуты:
   явный allow-list батча (TASK-0176 scope).
2. **Отсутствие `agent_id` у инструмента из инвентаря = отказ** (не
   только неравенство): правило читает и схему, не только переданные
   аргументы — закрывает `submit_task_for_review`, чей хендлер
   толерирует отсутствие `agent_id` (`if agent_id:`) и действовал бы
   без атрибуции.
3. Сообщение missing-principal — «Forbidden: no authenticated
   principal» (код -32001 закреплён задачей, формулировка — наша).
4. Fail-closed-сценарий проверен через `dependency_overrides` на
   scope-gate (см. выше) — иначе 401 от гейта не даёт дойти до handler.
5. D5-инвентарь вызывающих `/mcp` — уже выполнен в TASK-0170 (Bearer
   на /mcp никем не используется) — здесь не менялся.
6. `test_engine_dedup.ALLOWED_OWN_ENGINES` += `test_mcp_principal_binding.py`
   — санкционированное механизмом инварианта документированное
   исключение: общий StaticPool in-memory коннект не переживает
   параллельные записи sqlite3 (`InterfaceError: API misuse`), для
   concurrent-теста нужен engine с отдельным коннектом на сессию.
7. `docs/architecture/mcp-tools.md` НЕ редактировался: его
   Authentication-секция и инструменты (`whoami`, `get_capabilities`) —
   aspirational/stale ещё до этой задачи; дрейф наблюдением на
   отдельную docs-задачу.

### §12 Multi-factor analysis

- **Соответствие:** AC5 закрыт спуф-матрицей по всем 6 инструментам +
  missing-principal + A→A позитивы + параллель-изоляция; AC4/enumeration
  не тронуты (25 passed без правок); hermetic AC10 сохранён и закреплён
  (обе ветки флага пинятся тестами); Goals 1-2 выполнены, 3 — из 0170,
  4 — отложен в 0176 (отклонение 1).
- **Архитектура/DDD:** изменения только в `mcp/server.py` + тесты;
  identity — исключительно через публичный
  `identity.dependencies.get_agent_auth` (прецедент TASK-0170);
  boundary exact-set gate зелён без новых записей baseline; сессия
  запроса не тронута (bindings без I/O).
- **Производительность:** проверка — in-memory `frozenset` + один
  string-compare на tools/call, без запросов и аллокаций на уровне БД;
  `get_tools()` на dispatch — как раньше.
- **Безопасность:** fail-closed в обе стороны (нет принципала → отказ;
  аргумент `agent_id` у НЕ-инвентарного инструмента тоже сверяется);
  сверка ДО `call_tool` — отказ не может утечь через `result.is_error`;
  сравнение строковое, не через SQL/like.
- **Надёжность/наблюдаемость:** structured warning + span-attrs по
  утверждённому паттерну; отказ — штатный JSON-RPC error при HTTP 200;
  общий `-32603`-путь не изменился; OpenAPI контракт-тесты зелены.
- **Тестируемость:** +18 тестов; red-фаза сохранена (9 failed до
  реализации); обе ветки флага, обе стороны отказа, observability и
  concurrency покрыты; покрытие 90.41 → 90.58%.
- **Документация:** докстринги `mcp/server.py` синхронизированы;
  task-файл обновлён; specs/PROJECT_STATUS не тронуты (allow-list).

### Risks / что дальше

- **TASK-0176:** `SessionLocal`-фолбэки в `mcp/tools.py`/
  `context_pack.py` остаются базованными (здесь не трогали) — их
  бейзлайн в `context_boundary_baseline.py` актуален.
- **Identity-аргументы с другими именами** (`answered_by`,
  `created_by_id`) не привязаны к принципалу — spoof-вектор формально
  возможен; если нужен — отдельная задача (расширение правила).
- **Сиблинг TASK-0172** пишет в общий checkout (их red-файлы
  untracked) — полный прогон интерпретировать с исключением их файлов
  до их green-коммита.
