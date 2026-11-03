# TASK-0169 — Web auth dependency (JWT): default-deny + retire AuthMiddleware

**Source:** SPEC-0028 §3.2 (S28.2); Dmitry 2026-11-02 («API веба ожидает
JWT… маркировать ручки встроенным решением FastAPI»)
**Milestone:** auth rework (SPEC-0028 batch)
**Spec:** SPEC-0028 §3.2, AC1/AC2/AC4(web)/AC10/AC11; SPEC-0029 S29.3/S29.5
**Points:** 8
**Status:** DONE (реализация завершена 2026-11-04, gates зелёные — см. Evidence)

## Context

Веб-API (16 роутеров под `/api/v1`) защищается строковым гардом
`AuthMiddleware` + `PUBLIC_PATHS`; `/auth/*` вне гарда и защищён только
`Depends(get_current_user)` по памяти автора ручки (default-ALLOW).
Задача переводит аутентификацию веба на `web_auth`-зависимость
(blanket на `include_router`), убивает хардкод и выравнивает
`get_current_user` на сервисы (SPEC-0029).

## Goals

1. `web_auth` async-зависимость: Bearer → `TokenService.verify` →
   denylist → `SubjectStateService` → `request.state.user_id` +
   `api_surface="web"`; синхронный I/O через `run_in_threadpool`
   (не блокирует event loop); 401-формы идентичны текущим
   (missing / invalid / denylisted / unknown|disabled subject).
2. Blanket `dependencies=[Depends(web_auth)]` для web-группы реестра;
   `/auth`-защищённые ручки — через `get_current_user`, переписанный на
   `SubjectStateService` (SPEC-0029 S29.5).
3. `AuthMiddleware` и `PUBLIC_PATHS` удаляются; миграция тестового
   харнесса (тесты делают `add_middleware(AuthMiddleware)` — сейчас их
   десятки: `test_auth_middleware_protection.py`,
   `test_logout_denylist.py`, `test_security_hardening.py`,
   `test_rbac_enforcement.py`, `test_dashboard_security.py`,
   `test_auth_middleware_user_check.py`).
4. **Перечислительный тест AC1**: обход ВСЕХ web-ручек без кредов → не 2xx
   (401), исключения — только члены `PUBLIC_ROUTERS`. Это пропущенный
   класс сценария (SPEC-0028 finding 9).
5. `disable_auth` (hermetic) сохраняется на время миграции харнесса;
   зафиксировать как test-only (AC10).

## Test design (совместная проработка до кода — SPEC-0028 §6 / D6)

- **Behavior:** неавторизованный запрос к любой web-ручке → 401 с
  прежним body/headers; валидный JWT → поведение не меняется.
- **Boundaries:** публичные ручки (login/setup/refresh/health/docs)
  НЕ получают зависимость; `/mcp` не трогаем (это TASK-0170/0171);
  методы без тела vs с телом; CORS-OPTIONS не проходит через auth.
- **Conditions:** auth enabled (default) и `disable_auth=true`
  (hermetic); Redis up/down (denylist fail-open — SPEC-0027 AC5
  сохраняется); denylist-попадание; субъект удалён/отключён (TTL-кеш 60с).
- **AC:** SPEC-0028 AC1 (enumeration!), AC2, AC10, AC11; SPEC-0027
  регресс-база (55 authz live, 0 xfail).
- **Matrix:**
  - unit: `web_auth` — позитив (валидный JWT→CurrentUser); негатив ×4
    (нет заголовка, кривой формат, протухший, denylisted); негатив ×2
    (unknown/disabled sub); граница: `Bearer` без токена, токен с
    кривым `sub`.
  - integration: enumeration-тест по `app.routes` (негатив-класс!);
    перехват логов → нет значений заголовков (AC11).
  - parity: старые auth-тесты мигрируют на харнесс и должны остаться
    зелёными без смены семантики (SPEC-0029 AC2).
- **Red-фаза:** enumeration-тест и 401-shape тесты написать ДО удаления
  middleware (на текущем коде должны быть green — это characterization;
  после удаления — остаются green на зависимостях).

## Decomposition

| # | Item | Depends |
|---|---|---|
| 1 | `web_auth` (тесты red→green) поверх сервисов SPEC-0029 | 0174, 0175 |
| 2 | Blanket-включение в реестре + `/auth` на сервисах | 1, 0168 |
| 3 | Миграция тестового харнесса (снятие `add_middleware`) | 2 |
| 4 | Удаление `AuthMiddleware`/`PUBLIC_PATHS` + enumeration-тест AC1 | 3 |
| 5 | Evidence: полный прогон + authz live suite | 4 |

## Risks

- Объём миграции тестов — основной риск по времени; семантика 401 не
  меняется, поэтому миграция механическая (сверка форм в первом же тесте).

## Evidence (2026-11-04, branch `feature/TASK-0168-api-surface-registry`)

### Red → Green

- **RED:** `pytest backend/tests/test_web_auth_dependency.py` до
  реализации → collection error (by design, импорт модуля на уровне
  модуля теста):
  `ModuleNotFoundError: No module named 'app.identity.web_auth'`.
- **GREEN:** после создания `backend/app/identity/web_auth.py` —
  15 passed (новый файл), затем blanket в реестре + контрактные/green-гейты.
- **Enumeration — characterization:** `test_auth_enumeration.py` написан
  и зелён ПОД AuthMiddleware (спецификация red-фазы: на текущем коде
  characterization green; после удаления middleware остаётся green на
  зависимостях) — его регресс-ценность реализуется в TASK-0170.

### Что сделано (механизм)

- `identity/web_auth.py`: `async def web_auth(request, token_service=Depends(_get_token_service)) -> None`;
  disable_auth → return; Bearer-extract (byte-parity `startswith("Bearer ")`);
  `verify_access_token` ValueError → 401 invalid; denylist → `note_denied_token`
  → 401 invalid; `SubjectStateService` (фабрика `_get_subject_state_service`,
  session-less) != active → observability `_reject_subject` (метрика
  `auth_subject_rejections_total.labels(reason)`, warning с историческим
  текстом `"auth middleware: rejecting valid JWT…"` + `action=auth.subject_rejected`,
  span-attrs) → 401 invalid; успех → `request.state.user_id/auth_type="user"/api_surface="web"`.
  Весь синхронный пайплайн — один `run_in_threadpool`, `request.state` и
  reject-observability выставляются/логируются на event loop после await.
- `registry.include_surfaces`: WEB-группа → `dependencies=[Depends(web_auth)]`;
  AGENT/PUBLIC без изменений.
- **Редизайн импорта (boundary):** прямой `registry → identity.web_auth` —
  это foreign-internal (baseline править запрещено условием задачи).
  Решение: `identity/dependencies.get_web_auth()` — accessor на публичной
  поверхности identity с lazy-import внутри (на уровне модуля цикл
  `auth → dependencies → web_auth → auth` неизбежен). Тест
  `test_context_boundaries` зелён БЕЗ правок baseline.

### Seam mapping (старый тестовый шов → новый), 19 сайтов / 8 файлов

| Файл (сайтов) | Было | Стало |
|---|---|---|
| `test_auth_middleware_protection.py` (8)* | `app.add_middleware(AuthMiddleware[, token_service=ts])` | `FastAPI(dependencies=[Depends(web_auth)])` / `include_router(..., dependencies=[Depends(web_auth)])`; `dependency_overrides[_get_token_service] = λ: ts`; agent-сайт → `Depends(get_current_agent)`; `_hash_token` → `agent_token_service._hash_token`; autouse-flip `disable_auth=False` |
| `test_security_hardening.py` (3) | то же (MCP-сайты) | два JWT-сайта → `FastAPI(dependencies=[Depends(web_auth)])`+flip+override; agent-сайт → `Depends(get_current_agent)` (без flip) |
| `test_dashboard_security.py` (2) | `make_test_app(...)+add_middleware` | `make_test_app(..., protect=True)` + flip; valid-token → override `_get_token_service` |
| `test_logout_denylist.py` (2) | `add_middleware` в фикстурах (mixed app) | blanket ТОЛЬКО на защищённой части: `APIRouter` + `include_router(protected, dependencies=[Depends(web_auth)])`; `/auth` (public+get_current_user) без blanket; flip в обоих сайтах; override `_get_token_service` уже был |
| `test_auth_middleware_user_check.py` (1) | `mw._fetch_user_state` (spy), `mw.get_redis_client` | `UserRepository.get_auth_state` (class-level spy), `app.shared.redis.get_redis_client`; TTL 60 теперь пинится явно; flip в `app_client` |
| `test_rbac_enforcement.py` (1) | `add_middleware(TS)` | `make_test_app(projects_router, protect=True)` + override `_get_token_service`; flip уже существовал (`_enable_enforcement`) |
| `test_identity_permission_cache.py` (1) | `add_middleware(TS)` | `make_test_app(protect=True)` + override; flip уже существовал |
| `test_dashboard_matrix_ab.py` (1) | `add_middleware(ts)` | `make_test_app(protect=True)` + override + новый flip в `auth_client` |

\* В задаче указано 9 сайтов в protection — фактически 8; 19-й сайт
(`test_identity_permission_cache.py:89`) не был в списке файлов задачи —
мигрирован тоже (итог ровно 19 `add_middleware(AuthMiddleware…)` → 0).
Все утверждения (статусы, точные detail-строки, заголовки) сохранены.
`make_test_app` получил keyword `protect: bool = False` (conftest).

### Gates (последние строки)

- Targeted: `pytest test_web_auth_dependency test_auth_enumeration test_context_boundaries` →
  `40 passed, 18 warnings in 2.07s`.
- Parity subset (9 файлов спецификации + permission_cache): →
  `127 passed, 64 warnings in 14.78s`.
- Full: `pytest backend/tests -q -n auto` →
  `1240 passed, 245 warnings in 19.80s`,
  `Total coverage: 89.17%` (бейзлайн 1223 / 89.84% → +17 новых тестов;
  порог ≥80% соблюдён; см. замечание про middleware.py ниже).
- `ruff check backend` → `All checks passed!`;
  `ruff format --check backend` → `268 files already formatted`.
- `mypy backend/app` → `Success: no issues found in 120 source files`
  (бейзлайн 119 + новый `identity/web_auth.py`).
- Boundary gate зелён без правок `context_boundary_baseline.py`.

### Enumeration results (AC1)

131 target (113 web + 18 agent route×method; 95 уникальных путей) на
реальном `from app.main import app` → **все 401**, исключений не
потребовалось: под middleware — 401 до роутинга; FastAPI (проверено
экспериментом на установленной версии) решает route-dependencies ДО
валидации тела, поэтому и POST-ручки с обязательным body отвечают 401.
AC2: `/health` и `/api/v1/health` → 200 без кредов (health-пробы
за-патчены как в `test_health.py`).

### Отклонения (обязательные фиксации)

- **(a) Перенос удаления AuthMiddleware/PUBLIC_PATHS в TASK-0170**
  (порядок отличается от таблицы декомпозиции, п.4): между задачами
  AGENT-поверхность осталась бы БЕЗ охраны (её зависимость приходит в
  0170), а middleware — единственное, что её держит. Retirement
  приходит, когда обе поверхности несут зависимости: middleware.py +
  монтирование в main.py, PUBLIC_PATHS + `test_public_paths.py` +
  `test_public_paths_are_exempt`, baseline-записи
  (`identity/middleware.py` session-local/redis, `main.py→identity.middleware`),
  ссылки `from app.identity.middleware import …` в protection/conftest.
- **(b) Threadpool вместо блокирующего I/O:** middleware выполнял
  verify/denylist/liveness инлайн в event loop (finding 6);
  `web_auth` по требованию S28.2 гоняет ВЕСЬ синхронный пайплайн одним
  `run_in_threadpool`-вызовом, `request.state` — после await на loop;
  reject-observability (метрика/log/span) — тоже на loop, чтобы
  span-attrs попали в активный span запроса (контекст worker-нити не
  наследуется). Зафиксировано в докстринге `web_auth.py`.
- **(c) Роль enumeration-теста:** characterization green-under-middleware
  (в unit-окружении конфест держит `UPCP_DISABLE_AUTH=true`, а main.py
  монтирует middleware только при выключенном флаге на момент импорта —
  поэтому тест выполняет один «оконный» импорт `app.main` с
  auth-enabled env и тут же восстанавливает env; после 0170 оконный код
  становится инертным, а тест держат зависимости, flip-нутые per-request).
- **(d) Наблюдение для 0170/фронтенда:** на основном приложении blanket
  web_auth стоит и на защищённых `/auth/*`-ручках (WEB-группа), т.к.
  зависимости идут раньше route-уровневого `get_current_user` — неизвестный/удалённый
  субъект там теперь получает `Invalid or expired token` вместо
  `User not found or inactive` (юнит-тесты `/auth` строят свои приложения
  и это не фиксируют; shape согласован с middleware-поверхностью).
- **(e) Coverage-сдвиг:** `identity/middleware.py` упал до 32% — харнесс
  больше не гоняет его JWT/denylist/liveness-ветку (эти поведения теперь
  покрыты тестами `web_auth`); файл удаляется в 0170, суммарный
  показатель 89.17% ≥ 80%.

### §12 Multi-factor analysis

- **Соответствие требованиям:** AC1 (enumeration 131/131 → 401), AC2
  (public 200), AC10 (полный зелёный + ruff/mypy + hermetic-режим
  сохранён и закреплён тестом inert), AC11 (сырой токен не попадает в
  caplog — ассерт в denylist/subject-тестах). Тест-дизайн задачи
  (матрица unit/integration/parity) отработан.
- **Архитектура/DDD:** identity импортирует только own+shared+fastapi;
  публичная поверхность `dependencies.get_web_auth`; циклы исключены;
  boundary-gate зелён без базлайна. Уровень: сервисы SPEC-0029 под
  dependency (repo/cache/seams) — слои не нарушены.
- **Производительность:** синхронный I/O не блокирует loop (S28.2,
  шпион-тест `test_sync_pipeline_runs_in_threadpool`); горячий путь —
  кеши subject/denylist/permissions (TTL 60). Замечание (low): на каждый
  запрос создаётся лёгкая `SubjectStateService(UserRepository(), AuthCacheProvider())`
  (состояния нет) — при желании 0170/0173 может стать Depends-фабрикой.
- **Безопасность:** default-deny по поверхности; пути/строки в auth не
  используются; fail-open только у denylist-Redis (задокументирован,
  AC5); флаг `disable_auth` — test-only, inert-тест закрепил; никаких
  секретов/токенов в логах (AC11).
- **Надёжность/наблюдаемость:** 401-формы byte-parity; метрики/структ.
  логи/span-attrs идентичны middleware (исторический текст warning
  сохранён — преемственность алертов); Redis-outage fail-open → DB.
- **Тестируемость/покрытие:** +17 тестов (позитив/негатив/границы/
  условия), seam-таблица документирована; единственное покрытие,
  упавшее — файл на удаление (см. (e)).
- **Документация:** докстринги мигрированных файлов, registry,
  dependencies, web_auth обновлены; stale `_cached_permissions`-ссылки
  исправлены (отдельный commit). Находок severity critical/high — нет;
  medium — отложенный retirement (уже задачей 0170 закрыт), low —
  заметки (d)/(e) и per-request construction.

### Risks / что делает TASK-0170

- Удалить `identity/middleware.py` + монтирование в `main.py`
  (`if not settings.disable_auth: app.add_middleware(AuthMiddleware)`).
- Удалить `PUBLIC_PATHS`, `tests/test_public_paths.py` и
  `test_public_paths_are_exempt` (protection) — «retired together».
- Baseline: убрать `identity/middleware.py` (session-local, redis) и
  `main.py→identity.middleware`; правки — в том же коммите, что и код.
- Повесить `Depends(agent_auth)` на AGENT-группу; тестовые agent-сайты
  (`Depends(get_current_agent)`) перевести на `agent_auth`.
- `_hash_token` в middleware: тесты уже переведены на
  `agent_token_service._hash_token` (сами тесты у `middleware._hash_token`
  не ссылаются); оставшиеся копии — `agent_endpoints._hash_token`,
  `token_service._hash_token` — вне этой задачи.
- Enumeration: оконный импорт `app.main` становится инертным (кода
  монтирования нет) — тест НЕ трогать, flip в fixture уже per-request.
