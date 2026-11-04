# TASK-0170 — Agent auth dependency (API key): TTL, scopes, единая верификация

**Source:** SPEC-0028 §3.3 (S28.3), решение D1 (Dmitry 2026-11-02: остаёмся
на статическом API-ключе + TTL + отзыв + hardening)
**Milestone:** auth rework (SPEC-0028 batch)
**Spec:** SPEC-0028 §3.3, AC4/AC6/AC7; SPEC-0029 S29.4
**Points:** 5
**Status:** DONE (реализация завершена 2026-11-04, gates зелёные — см. Evidence)

## Context

Агентский API (agent-self, workflow claims/heartbeats, `/mcp`) сейчас
аутентифицируется дублированной логикой в двух местах
(`middleware.py:181-217` с `commit()` и `agent_auth.py` с `flush()`),
scopes хранятся, но **не проверяются нигде**, `expires_at` опционален,
`PUBLIC`-гард — строковый. Отдельно: синхронные DB/Redis в async
`dispatch` блокируют event loop.

## Goals

1. `agent_auth` async-зависимость поверх `AgentTokenService`
   (SPEC-0029 S29.4): единый `sha256`, revoked/expired → 401, agent
   активен → иначе 401, `last_used_at` — одна точка записи с
   commit-before-response; I/O в `run_in_threadpool`.
   `request.state.agent_id/agent_name` + `api_surface="agent"`.
2. **Enforcement scopes:** маркировка нативно —
   `dependencies=[Depends(require_agent_scope("..."))]` на агентских
   ручках; нет scope → **403**. Инвентарь ручек и scope-имён (proposal:
   `tasks:*`, `inbox:*`, `profile:read`) — в задаче.
3. **TTL ключей:** новые ключи обязаны получать `expires_at`
   (конфигурируемый максимум, дефолт в задаче); отзыв — мгновенный
   (`revoked_at` уже есть); инвариант — отозванный/протухший ключ не
   проходит следующий же запрос (никаких окон вне явных TTL).
4. Enumeration-тест agent-поверхности: без ключа → 401 на КАЖДОЙ ручке
   (аналог AC1 для agent-группы).
5. Не логировать `X-Agent-Token`/`Authorization` (перехват логов, AC11).

## Test design (совместная проработка до кода — SPEC-0028 §6 / D6)

- **Behavior:** ключ принимается только на agent-поверхности; веб-JWT на
  agent-ручках → 401 (ограничение D5 — предварительная инвентаризация
  вызывающих `/mcp` с Bearer; при зависимости внутренних вызовов —
  временный dual-accept с tracked-задачей).
- **Boundaries:** просроченный vs отозванный vs несуществующий ключ
  (все 401, но с раздельными unit-кейсами); `expires_at=null` у
  старых ключей (grandfather-политика — решить в задаче); параллельные
  запросы на touch.
- **Conditions:** Redis up/down (кеш-политика — SPEC-0029 AC3), agent
  inactive, счётчик `last_used_at`.
- **AC:** SPEC-0028 AC4, AC6, AC7, AC11.
- **Matrix:**
  - unit: `verify()` — позитив; негатив ×5 (нет ключа, неизвестный,
    отозванный, протухший, неактивный агент); граница: ключ истекает
    «сейчас» (clock edge); scope: есть/нет → 200/403.
  - integration: enumeration по agent-группе реестра (негатив-класс);
    touch-инвариант (следующий запрос видит обновлённый `last_used_at`);
    отсутствие ключа в логах (capture).
  - contract: повторное использование хеша-функции (SPEC-0029 AC5).

## Decomposition

| # | Item | Depends |
|---|---|---|
| 1 | `AgentTokenService` red→green (SPEC-0029 S29.4) | 0174 |
| 2 | `agent_auth` + blanket-включение для agent-группы | 1, 0168 |
| 3 | `require_agent_scope` + инвентарь ручек/scopes | 2 |
| 4 | TTL-политика выдачи ключей (agent_endpoints) | 2 |
| 5 | Enumeration + parity-тесты, миграция харнесса | 2-4 |

## Evidence (2026-11-04, branch `feature/TASK-0168-api-surface-registry`)

Коммиты (каждый зелён на своём дереве):
`c71a07b feat(identity): agent-surface auth — blanket dependency, scopes, key TTL (TASK-0170)` →
`7f14253 refactor(identity)!: retire AuthMiddleware and PUBLIC_PATHS — surfaces guard themselves (TASK-0170)` →
docs+task.

### Red → Green

- **RED** (тесты написаны ДО реализации, символы импортированы внутри
  тестов → файл собирается): `16 failed, 8 passed` —
  `test_agent_surface_auth` 12 failed (нет blanket → /mcp/tools 200 вместо
  401; нет 403-скоупов; нет `agent_auth` → ImportError; нет state;
  hermetic-кейсы) + `test_agent_create_commit` 4 failed (TTL: KeyError
  `expires_at`, AttributeError `agent_token_ttl_days`, past-expiry не
  даёт 422); 8 passed — characterization (vacuous 200 на неохранённых
  ручках + пины handler-семантики + старые 5 тестов commit-файла).
- **GREEN**: targeted `24 passed`; затем все гейты (см. ниже).

### Blanket-дизайн и решение по `disable_auth`

- `identity/agent_auth.py`: `agent_auth` (async blanket) → флаг-чек →
  memo → `run_in_threadpool(_verify_principal)` → state на loop;
  `get_current_agent` получил `request: Request`, пишет state и
  **всегда** проверяет (флаг НЕ консультируется — закреплено существующим
  `test_identity_agent_dependency::test_missing_header_rejected`);
  `request.state.{agent_id, agent_name, auth_type="agent",
  api_surface="agent"}` + memo `request.state.current_agent`.
- Реестр: `include_surfaces` вешает `Depends(get_agent_auth())` на
  AGENT-группу (accessor в `identity/dependencies.py` c lazy-import —
  прецедент `get_web_auth`, gate TASK-0177 не нарушен: boundary-тест
  зелён без новых записей baseline).
- **Решение по hermetic-флагу**: blanket и scope-гейт коротко замыкают
  при `disable_auth=true` (паритет: middleware в hermetic-режиме не
  монтировался); handler-level `get_current_agent` продолжает всегда
  проверять (асимметрия закреплена новым тестом). Проверено полным
  сьютом в обоих деревьях.
- **Структурное обоснование (отклонение от буквы задачи)**: гейт
  подчинён `Depends(agent_auth)`, а не `Depends(get_current_agent)`:
  FastAPI решает sub-dependencies ЭAGER (проверено на установленной
  0.139.2, `solve_dependencies`), поэтому sub-dep на handler-зависимость
  отклонил бы hermetic-тесты на голых `create_mcp_router`-сайтах
  (~100 тестов test_mcp*/test_context_pack) до тела гейта. Один прогон
  verify на запрос обеспечен кешем FastAPI (blanket и гейт делят
  `agent_auth`) + memo `request.state` (blanket ↔ handler) — закреплено
  шпион-тестом `verify_detailed == 1`.

### Инвентарь scopes (AC6) и фактическая форма данных

| Роутер | Scope | Маршруты |
|---|---|---|
| `api/v1/agent_self.py` | `agent:self` | GET `/agent/me`, `/agent/inbox`, `/agent/playbook` (3) |
| `api/v1/task_workflow.py` | `agent:workflow` | POST claim, release, heartbeat, progress; GET claims, heartbeats, clarifications; POST clarification, answer (9) |
| `mcp/server.py::create_mcp_router` | `agent:mcp` | GET/POST `/`, GET `/tools`, `/tools/{name}`, `/resources`, `/resources/{name}` (6) |

- **Форма `scopes` (инспекция записи)**: production-запись —
  `AgentTokenCreate.scopes: list[str]` → JSON-массив; аннотация модели
  `Mapped[dict[str, object] | None]` неточна (правка запрещена
  allow-list — задокументировано); тесты старой волны сеют dict
  (`{"read": True}`), часть сеет `[]`. Политика: `None` → ALLOW
  (grandfather — до AC6 enforcement не было вовсе); list → membership;
  dict → truthy-ключ; прочее → DENY (fail-closed, defensive).
- Отказ: 403 `{"detail": "Insufficient scope"}` + метрика
  `upcp_agent_scope_denials_total{scope}` + warning
  `action=auth.scope_denied` + span `upcp.auth.scope_denied`
  (паттерн `permissions.py`; гейт async — span-attrs на loop).

### D5: инвентарь вызывающих `/mcp` (conversion, не blocker)

- **Конвертирован**: `tests/security/authz/test_authz_bypass.py`
  (`test_valid_token_accepted[mcp-tools]` слал валидный admin-JWT →
  теперь `agent_headers`-фикстура чеканит `X-Agent-Token`;
  матрица README обновлена). Это TEST-caller → конверсия разрешена.
- **Без конверсии (совместимо)**: fuzz `auth_bypass` (все /mcp-кейсы
  анонимные → 401 ✓), authz аноним-кейсы ✓, locust/perf (нет вызовов
  /mcp), e2e (`auth.spec.ts` — только `/auth/me`), frontend (нет /mcp),
  scripts/seed (нет). **Реальных не-тестовых Bearer-вызывающих на /mcp
  нет → dual-accept НЕ нужен, blocker'а нет.**

### TTL при выпуске (AC7)

- `AgentTokenCreate.expires_at` (опционально) + endpoint: без значения →
  `now + settings.agent_token_ttl_days` (новое поле
  `UPCP_AGENT_TOKEN_TTL_DAYS`, default 90, `ge=1`); явное значение
  нормализуется в UTC и должно быть в будущем, иначе **422**
  (бизнес-rule, HTTPException); ответ содержит `expires_at`.
- Grandfather: `expires_at IS NULL` у старых ключей — verifier
  (`AgentTokenService.verify_detailed`) отклонирует только не-null
  прошедшее → действуют до отзыва (задокументировано в докстринге
  эндпоинта и в docs).
- `.env.example` + `bootstrap_upcp.py`: мёртвый (не читавшийся никем)
  `UPCP_AGENT_TOKEN_MAX_AGE_DAYS` заменён на живой
  `UPCP_AGENT_TOKEN_TTL_DAYS=90`.

### Retirement-пакет

- Удалено: `backend/app/identity/middleware.py`;
  `backend/tests/test_public_paths.py` (doc-literal-контракт TASK-0148
  сохранён переездом в `backend/tests/test_auth_docs_contract.py` —
  git определил rename 51%; реестрово-Route-половина умерла вместе со
  словарём и покрыта `test_api_surface_registry` + enumeration).
- `main.py`: удалены import + блок
  `if not settings.disable_auth: app.add_middleware(AuthMiddleware)`
  (заменён комментарием-указанием на registry-зависимости).
- Baseline `context_boundary_baseline.py` (в том же коммите): удалены
  ровно 3 ключа — `("main.py","foreign-internal","app.identity.middleware")`,
  `("identity/middleware.py","session-local","SessionLocal")`,
  `("identity/middleware.py","redis","app.shared.redis")`; exact-set
  gate зелёный (нет ни новых, ни stale).
- Очищены ссылки в code+tests: `test_auth_middleware_protection`
  (import PUBLIC_PATHS + `test_public_paths_are_exempt` + docstring),
  `conftest.py`, `identity/permissions.py`, `identity/denylist.py`
  (+ ссылались на удалённые `_fetch_user_state`),
  `test_auth_middleware_user_check.py`, `test_observability_configs.py`,
  `test_context_boundaries.py` (2 синтетических примера),
  `tests/security/authz/README.md`. Исторические упоминания
  («retired/formerly/written GREEN under») оставлены намеренно;
  `web_auth.py` (вне allow-list) остался со stale-фразой «middleware
  stays mounted until TASK-0170» — зафиксировано как заметка.

### Docs (DoD)

- `docs/security/auth-rbac.md` (EN) + `docs/security/auth-rbac.ru.md`
  (RU): header/версия 3.0.0→3.1.0 + pointer на
  `test_auth_docs_contract.py`; §1 переписан на dependency-based auth
  (web_auth/agent_auth blankets, registry, coverage-тесты, retirement);
  новый §2.3 «Agent API key (`X-Agent-Token`)» — TTL 90 дней,
  обязательный `expires_at`, grandfather NULL-ключей, scopes
  (agent:self/agent:workflow/agent:mcp, 403, метрика/span), hermetic;
  §4 — денайлист в `web_auth`; §6 п.1 — флаг без middleware.
- `tests/security/authz/README.md` (матрица D5 + pointer'ы).
- НЕ тронуто (вне affected-prose): `docs/security/agent-permissions.md`
  (аспирационная модель project-bound токенов, не соответствовала коду
  и до этой задачи), threat-model — их «middleware» относится к
  никогда-не-реализованному project-scoping; EN/RU-дрейф про `jti` в
  §2.1/RU (не относится к теме задачи) — наблюдение на отдельную
  docs-правку.

### Gates (последние строки)

| Gate | Результат |
|---|---|
| targeted, дерево коммита 1 (2 новых файла + enumeration + boundaries + agent-dep + agent_self) | **73 passed** |
| targeted, дерево коммита 2 (+ docs-contract + protection) | **58 passed** |
| parity subset (logout_denylist, rbac_enforcement, auth_middleware_protection, web_auth_dependency, security_hardening, auth_middleware(+user_check), workflow/clarification/task_transition, mcp×4, dashboard×2, auth_endpoints, auth_cache_provider) | **240 passed** |
| FULL `pytest backend/tests -q -n auto` (коммит 1) | **1259 passed, 0 failed, coverage 89.75%** (бейзлайн 1240 / 89.17%) |
| FULL (коммит 2/финал) | **1257 passed, 0 failed, Total coverage: 90.41%** |
| `ruff check backend` | All checks passed! |
| `ruff format --check backend` | 268 files already formatted (269→268: middleware.py удалён) |
| `mypy backend/app` | Success: no issues found in 119 source files (120→119) |
| `test_auth_enumeration.py` | зелён БЕЗ правок (fixture уже flip-ает флаг per-request; оконный импорт теперь инертен — механика подтверждена) |

### Отклонения (зафиксированы)

1. Гейт sub-depends на `Depends(agent_auth)` вместо
   `Depends(get_current_agent)` (eager-solve — см. выше); single-exec
   доказан шпион-тестом.
2. Grandfather-политики: `scopes=None` → ALLOW; `expires_at=NULL` →
   ключ жив до отзыва.
3. `disable_auth`: blanket+гейт отключаются; handler-зависимость — нет
   (требование «семантика не меняется» + пин-тест).
4. TTL default = 90 (`ge=1`).
5. Doc-literal тест переехал (не удалён) — иначе AC4 TASK-0148 терял
   регрессию.
6. Реальный `app.main`: точные detail-строки закреплены на
   `include_surfaces`-приложении (детерминировано в обоих коммитах),
   на main — статусы (переходное окно: ещё смонтированный middleware
   в full-suite мог ответить свёрнутыми detail); lifecycle-классы на
   main покрыты.
7. `PROJECT_STATUS.md` НЕ обновлён — явный allow-list задачи
   («notably … PROJECT_STATUS.md») имеет приоритет над общим DoD.
8. `UPCP_AGENT_TOKEN_MAX_AGE_DAYS` (мёртвый) → `UPCP_AGENT_TOKEN_TTL_DAYS`
   в `.env.example`/bootstrap — иначе документированный knob не читается
   кодом.
9. `bootstrap_upcp.py` остаётся не-`ruff format` (pre-existing; хуки
   ограничены `^backend/`) — правка только 2 строк в raw-строке.

### §12 Multi-factor analysis

- **Соответствие**: AC4 (5 классов → 401 с каноническими detail через
  blanket; web-JWT на агент-ручках → 401 — агент-поверхность не читает
  Bearer), AC6 (403-матрица per-router + metric/log/span), AC7 (TTL
  тесты: default/future/past-422/NULL-grandfather), AC10 (полный сьют
  зелёный, ruff/mypy чисты, hermetic сохранён и закреплён тестами),
  AC11 (сырые значения заголовков не логируются — в новых коде только
  agent_id/scope; существующие AC11-тесты зелены), AC1 enumeration —
  зелён нетронутым.
- **Архитектура/DDD**: registry/`mcp/server` потребляют identity только
  через публичную поверхность (`dependencies.get_agent_auth`,
  `get_require_agent_scope`) — boundary exact-set gate зелён (3 записи
  удалены, 0 новых); слои identity не тронуты (сервисы/repositories
  без изменений).
- **Производительность**: verify в threadpool (loop не блокируется);
  1 verify/запрос вместо 2 (было: middleware + handler); hot-path без
  кеш-промахов (agent-verification не кешируется по design — touch
  обязан лететь каждый запрос, AC7-инвариант).
- **Безопасность**: default-deny per-surface; path-строк в auth нет;
  scopes enforcement (ex-finding 5); обязательный TTL ключей (D1);
  403/401 byte-parity; fail-closed на неизвестной форме scopes; флаг —
  test-only.
- **Надёжность/наблюдаемость**: 401/403 формы байт-в-байт сохранены;
  новая метрика + структурный warning + span-attrs по паттерну
  permissions.py; state-контракт для TASK-0171 (agent_id/agent_name/
  auth_type/api_surface) закреплён тестом.
- **Тестируемость**: +19 тестов (15 surface + 4 TTL); red-фаза
  сохранена (16 failed до реализации); characterization-часть
  (vacuous-greens) задокументирована; покрытие выросло 89.17→90.41%.
- **Документация**: докстринги 8 изменённых app-файлов синхронизированы;
  EN+RU auth-docs обновлены; contract-тест doc↔routes зелёный на
  финальном дереве. Находки critical/high — нет; medium — dрейф
  EN/RU `jti` и stale-фраза в `web_auth.py` (обе вне allow-list /
  вне темы) — отложены.

### Risks / что дальше (0171/0172/0173)

- **TASK-0171 (MCP principal binding)**: state-контракт ГОТОВ —
  `request.state.agent_id/agent_name/auth_type/api_surface` выставляет
  blanket на всех агентских ручках, включая POST `/mcp` (gate+blanket
  раньше handler). Осталось: пробросить principal в JSON-RPC dispatch
  (route должен принять Starlette `Request`), сверять `agent_id` из
  аргументов инструмента (403 при рассогласовании, AC5), inventory уже
  сделан здесь (Bearer на /mcp никем не используется).
- **TASK-0172 (RBAC coverage)**: `require_permission` не менялся;
  читает `request.state.user_id` — web_auth выставляет как раньше;
  рисков нет; `permissions.py` получил только docstring-правки.
- **TASK-0173 (surface observability)**: `request.state.api_surface`
  теперь есть ОБЕ стороны (`"web"`/`"agent"`) — готово к prefix'ам
  request-id / span-атрибутам / label `surface`; rate-limit middleware
  ещё путь-ориентирован (вне этой задачи).
