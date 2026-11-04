# TASK-0173 — Surface-aware observability: корреляция, трейсы, метрики, rate-limit по типу API

**Source:** SPEC-0028 §3.6 (S28.6); Dmitry 2026-11-02 («запросы от веб и
от агентов должны отслеживаться и анализироваться по разному… разные
форматы корреляции, префикс или разные форматы»)
**Milestone:** auth rework (SPEC-0028 batch)
**Spec:** SPEC-0028 §3.6, AC9
**Points:** 3
**Status:** DONE (2026-11-04, ветка `feature/TASK-0168-api-surface-registry`)

## Context

`CorrelationMiddleware`, `TracingMiddleware`, `MetricsMiddleware`,
`RateLimitMiddleware` — общие и не знают, кто вызывает (web-браузер или
агент). Разделять нужно **данными**, а не дублированием middleware:
`web_auth`/`agent_auth` выставляют `request.state.api_surface`, и
общие middleware читают её. Отдельно: `rate_limit_middleware.py:33`
содержит тот же строковый хардкод префиксов — устранить (переход на
контракт «поверхность из контекста/реестра», а не `startswith`).

## Goals

1. `api_surface` (`web|agent|public`) в `request.state` от auth-зависимостей;
   контекстный признак в structured logs (contextvar, выставляемый в том
   же request-контексте — с учётом, что sync-зависимости в threadpool
   контекст не возвращают: либо async-обёртка, либо чтение scope-state).
2. Корреляция: `X-Request-ID` с префиксом поверхности
   (`web:<uuid>` / `agent:<uuid>`) — ответ и логи; входящий
   клиентский `X-Request-ID` сохраняется (суффиксом/после префикса).
3. OTel: span-атрибуты `upcp.auth.surface` (+ `upcp.auth.principal_type`);
   метрики: label `surface` на request-metrics и auth-denials.
4. Rate-limit: policy по поверхности (конфиги в `settings`:
   `UPCP_RATE_LIMIT_WEB_*` / `*_AGENT_*` — имена уточнить по
   префиксу-контракту TASK-0119), хардкод-строки `startswith` убраны
   (классификация — по registry/`scope["route"]` после маршрутизации
   либо через surface из auth-зависимости — решение в задаче по
   измеримому cost'у).
5. Наблюдаемость без нагрузки: surface-знание доступно до логирования
   хендлера (иначе префикс в логах бесполезен).

## Test design (совместная проработка до кода — SPEC-0028 §6 / D6)

- **Behavior:** web-запрос → id с префиксом `web:`, span-атрибут
  surface=web, метрика с label; agent-запрос — соответственно.
- **Boundaries:** публичные запросы (surface=public, свой префикс);
  входящий `X-Request-ID` от клиента; запрос, отклонённый auth-зависимостью
  ДО хендлера (401-ответ тоже должен быть размечен поверхностью —
  иначе отклонения не разделить!); CORS-OPTIONS (minust surface).
- **Conditions:** tracing установлен/не установлен (opentelemetry
  опционален — существующий паттерн guard'а); disable_rate_limit=true.
- **AC:** SPEC-0028 AC9.
- **Matrix:**
  - unit: формирование id по surface (позитив ×3, граница: клиентский
    id с префиксом уже); span-атрибуты через span-spy; label-чтение
    метрики.
  - integration: парные запросы web/agent → ассерт различий в заголовке,
    лог-записи (capture) и span; 401-отклонение размечено.
  - perf: не добавлять матчинг маршрутов второй раз в middleware
    (измерить overhead ≤ фонового) — «не превращаемся в безупречную
    улитку».

## Decomposition

| # | Item | Depends |
|---|---|---|
| 1 | surface в контексте + формат id/логов (red-тесты парности) | 0169, 0170 |
| 2 | Span-атрибуты + метрики-labels | 1 |
| 3 | Rate-limit: policy по поверхности, удаление startswith-хардкода | 1 |
| 4 | Evidence: парные интеграционные тесты + замер overhead | 2-3 |

## Evidence (2026-11-04)

### Выбран Shape A (два слоя) и почему

Осмотр middleware + тестов (E8) + env-кнопок показал: сегодня лимит — один
IP-бакет в middleware, включаемый только при `not disable_rate_limit` в
`main.py`, с покрытием «`/api/v1/`+`/auth/` префиксами» и строгими
бакетами login/setup/refresh. **Shape A** (floor в middleware + policy как
зависимость после auth) сохраняет этот механизм и его response-форму
буквально (E8 зелёный без правок), поэтому миграционный cost минимален;
добавляет default-deny покрытие (новые/будущие префиксы и `/mcp` теперь
лимитируются) и principal-ключевой слой после auth — различие данными, не
копиями кода (D2). **Shape B** отвергнут: убрал бы pre-auth floor — честный
DoS-компромисс, но без выигрыша в стоимости (Shape A и так требует dep),
только с потерей защиты публичных/неизвестных путей.

Два слоя: (a) глобальный IP-floor в `RateLimitMiddleware` — каждая строка
кроме точного skip-набора (`/health`, `/api/v1/health`, `/metrics`,
`/docs`, `/redoc`, `/openapi.json`, `/docs/oauth2-redirect`), строгие
бакеты через **точный** dict-lookup полного пути; (b) `SurfaceRateLimit`
(dep) в `include_surfaces` **сразу после** auth-зависимости (порядок solve
проверен эмпирически: auth → rate → handler), ключ `user:<id>` /
`agent:<id>` с fallback `ip:<ip>`, честный honors `disable_rate_limit`
per-request. Деп пишет результат в `request.state.surface_rate_limit`;
middleware отдаёт приоритет этим данным при формировании
`X-RateLimit-*` заголовков (bucket-согласованность).

### Настройки (shared/config.py, префикс-контракт TASK-0119)

| Env | Дефолт | Смысл |
|---|---|---|
| `UPCP_RATE_LIMIT_WEB_MAX` | 100 | web-политика: макс. запросов |
| `UPCP_RATE_LIMIT_WEB_WINDOW` | 60 | web-политика: окно, сек |
| `UPCP_RATE_LIMIT_AGENT_MAX` | 100 | agent-политика: макс. запросов |
| `UPCP_RATE_LIMIT_AGENT_WINDOW` | 60 | agent-политика: окно, сек |

Дефолты == исторический бакет `DEFAULT_LIMITS["default"]` → эффективные
лимиты существующих деплоев не меняются (bwd-compat: `UPCP_DISABLE_RATE_LIMIT`
и `DEFAULT_LIMITS` как прежде; контракт-тесты env green).

### Изменения по файлам

- `shared/logging.py` — `surface_var` contextvar + поле `surface` в JSONFormatter.
- `shared/correlation.py` — `sanitize_request_id` (`[A-Za-z0-9._-]{1,64}` /
  иначе uuid4), `resolve_surface` (state → `scope["route"]`-правило:
  web/agent | public | none), заголовок `<surface>:<id>`, сброс
  `surface_var` в finally.
- `identity/web_auth.py`, `identity/agent_auth.py` — attribution на ENTRY
  (state + contextvar до `disable_auth`/верификации → 401 и hermetic
  разметываются); `_store` выставляет contextvar для handler-level пути.
- `shared/tracing_middleware.py` — `upcp.auth.surface` (post-call_next,
  через `resolve_surface`) + `upcp.auth.principal_type` (Goal 3); guard —
  существующий lazy-import в `main.py` не менялся.
- `shared/metrics.py` + `metrics_middleware.py` — **ADDITIVE** label
  `surface` на `upcp_http_requests_total` и `upcp_http_request_duration_seconds`
  (инк/observe post-call_next; `in_progress` остался `method` — surface
  на момент inc неизвестен, задокументировано).
- `shared/rate_limit_middleware.py` — переписан: floor на все пути,
  точный skip-набор, точные строгие бакеты, приоритет
  `state.surface_rate_limit` в заголовках; **никаких префикс-строк**.
- `shared/rate_limit.py` — `SurfaceRateLimit` + фабрика `surface_rate_limit`.
- `shared/config.py` — 4 настройки выше.
- `api/registry.py` — `include_surfaces`: `[auth, rate-policy]` для WEB/AGENT,
  PUBLIC без policy (parity); новый импорт только из `shared` (boundary-green).
- `main.py` — **не менялся**: mount-gate floor без изменений (parity E8).
- Тесты: новые `test_surface_observability.py` (221), `test_surface_metrics.py`
  (66), `test_surface_rate_limit.py` (294), харнесс `surface_probe_harness.py`
  (111) — все ≤300 строк; миграция `test_logging.py` (1 assert).

### Red → Green

1. RED: `ImportError: cannot import name 'sanitize_request_id'` +
   `ImportError: cannot import name 'SurfaceRateLimit'` (collection error,
   precedent `test_web_auth_dependency`) и
   `FAILED test_preserves_existing_request_id` (старое поведение).
2. GREEN (после фиксов тестового харнесса: `Handler.setFormatter`,
   счётчик public-группы, префиксы ключей): **47 passed** targeted.

### Маппинг старых → новых тестов (инвентарь `rg "RateLimit|429" backend/tests`)

| Старый тест | Исход |
|---|---|
| `test_rate_limit.py` (unit `check_rate_limit`) | без изменений, зелёный |
| `test_dashboard_security.py::test_e8_...429` | без изменений, зелёный (Shape A сохранил форму ответа/заголовки floor) |
| `test_security_hardening.py` (env-флаги) | без изменений, зелёный |
| `test_logging.py::test_preserves_existing_request_id` | **мигрирован**: `my-custom-id` → `public:my-custom-id` |
| — | новых сломанных rate-тестов нет; новые кейсы: `test_surface_rate_limit.py` (пороги web≠agent, principal-изоляция, disable-parity, public-skip, floor на неизвестный префикс, реестр-вложение, 429-shape) |

### Grep-proof: ноль path-хардкодов в rate-limit пути

```
grep -rn "startswith" backend/app/shared/rate_limit.py backend/app/shared/rate_limit_middleware.py        → exit 1 (нет совпадений)
grep -rnE 'startswith\("/api|startswith\("/mcp|"/api/v1/"' ...rate_limit*.py                              → exit 1 (нет совпадений)
```
Закреплено скан-тестом `test_rate_limit_modules_contain_no_path_hardcodes`.

### Risk note: метрика-лейблы (дашборды)

`surface` **добавлен** к уже существующим label-наборам (ничего не
удалено/переименовано). Проверено по `observability/grafana/dashboards/test/*`:
все запросы агрегирующие (`sum(rate(...))`, `by (method|status|handler|le)`)
— они продолжают работать: series сплитятся, но внутри sum
пересобираются в те же числа. Остаточный риск: cardinality ×≤4 (web/agent/
public/none) и точные label-матчеры/`count()` во внешних (не-репозиторных)
запросах — при деплое ожидаем кратковременный break в rate()-графиках на
границе серий.

### Замер overhead (декомпозиция п.4)

TestClient, 800 запросов: bare 2.93 ms/req vs стек
tracing+correlation+metrics 4.79 ms/req → **+1.86 ms/req** на весь
наблюдаемый стек (в основном pre-existing BaseHTTPMiddleware-хопы). Мой
дельта-вклад — O(1) dict/set-lookup и contextvar-set/micro-reads; **повторного
матчинга маршрутов нет нигде** (floor: точные множества/dict;
`resolve_surface`: чтение state/scope). Относительная цифра, не perf-лаборатория.

### Deviations

1. **Логи vs префикс (goal 2)**: заголовок несёт `<surface>:<id>`, но в
   JSON-логах `request_id` остаётся bare, а поверхность — отдельным полем
   `surface` (prompt п.1+2: «включить surface в structured logs так же, как
   request_id»). Двойное кодирование префикса внутрь `request_id` избыточно
   при наличии `surface`-поля; JSON-запросы фильтруются по двум полям.
   Публичные маршруты: в логах `surface` отсутствует (контекстный признак
   выставляют только auth-зависимости — prompt п.1), в заголовке `public:`.
2. `main.py` не изменён (mount-gate работает как прежде).
3. Docs/.env.example не правлены (вне allow-list) — строки ниже.

### §12 mini-analysis

- **Соответствие требованиям**: AC9 закрыт (префиксы ×3+none, санитизация,
  span-attr, метрика, rate по поверхности, ноль хардкодов); §3.6/Goals 1-5
  закрыты; Goal 3 `principal_type` — реализован.
- **Архитектура**: D2 — различие данными; boundary-гейт зелёный без правок
  baseline (registry → shared разрешено; shared не импортирует registry —
  классификация по scope/state, обосновано в `resolve_surface`).
- **Производительность**: O(1)-пути, без повторного матчинга (замер выше).
  *low*: два слоя = два redis-roundtrip на web/agent-запрос (floor+policy).
- **Безопасность**: санитизация входящего request-id (log-injection),
  default-deny floor (усиление), strict-бакеты по точному пути.
  *info*: floor-ключ остался «сырой IP» (bwd-compat).
- **Надёжность/наблюдаемость**: 401/500 разметываются (state на entry +
  post-call_next чтения); contextvar гигиена в finally; structured log
  поле `surface`.
- **Тесты**: 76 новых кейсов (позитив/негатив/границы: hostile id ×5,
  санитайзер-юнит, метрики-дельты, 401-атрибуция, disable-parity,
  public-skip, неизвестный префикс, мутационный скан-тест хардкодов).
  *low*: нет отдельного e2e за пределами TestClient (природа задачи —
  unit/integration).
- **Документация**: кодовые докстринги синхронизированы; внешние доки —
  строки ниже (задача отдельным действием, вне allow-list).

### Нужные строки документации (не правились — вне allow-list)

- `.env.example` (после `UPCP_DISABLE_RATE_LIMIT`):
  `UPCP_RATE_LIMIT_WEB_MAX=100`, `UPCP_RATE_LIMIT_WEB_WINDOW=60`,
  `UPCP_RATE_LIMIT_AGENT_MAX=100`, `UPCP_RATE_LIMIT_AGENT_WINDOW=60`.
- `docs/security/rate-limiting.md` §2: схема
  `Request → RateLimitMiddleware (IP-floor, все пути − точный public skip)
  → SurfaceRateLimit (после auth: user/agent-ключ) → Handler`; §3 —
  таблицу лимитов дополнить колонкой surface + env-переменные.
- `docs/architecture/rate-limiting.md`: раздел «Limits vary by route class»
  дополнить двумя слоями и правилом «нет префикс-матчинга, любой
  неизвестный путь лимитируется по умолчанию».

### Gates (финальные выводы)

```
targeted+affected (13 файлов, включая test_auth_enumeration и
test_context_boundaries UNEDITED):        169 passed, 22 warnings in 7.92s
FULL suite backend/tests:                 1545 passed, 0 failed
                                          TOTAL 5726 stmts, 91.22% coverage
ruff check backend:                       All checks passed!
ruff format (16 файлов задачи):           1 reformatted, остальные clean;
                                          format --check новых → all formatted
mypy backend/app:                         Success: no issues found in 119 source files
```
