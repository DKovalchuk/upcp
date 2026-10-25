# TASK-0158 — Security results → Grafana: Pushgateway [backlog §8 item B]

**Source:** SPEC-0027 backlog §8 («security results → Grafana»); решение
Dmitry 2026-10-25 (ask): **Sec→Grafana: Pushgateway**
**Milestone:** backlog §8
**Spec:** mini-spec (AC ниже) — производный от SPEC-0024 (test env, observability)
**Points:** 3
**Status:** DONE (2026-10-25 — live-цепочка gateway→prometheus зелёная, 1045 passed)

## Objective

Промежуточные результаты security-сьютов (`upcp-security-result/v1`) становятся
видимыми в Grafana: runner пушит метрики в Pushgateway → Prometheus скрейпит →
дашборд `test/security`. Цепочка «Sec→Grafana» замыкается без новых зависимостей
(stdlib urllib на стороне runner).

## Investigation (2026-10-25, evidence — чтение кода/конфигов)

- `tests/security/runner.py`: `main()` собирает `results: list[dict]` после
  прогона сьютов (`print_summary` → `write_report` → `sys.exit(max(codes))`) —
  единственная точка пуша; результаты = `upcp-security-result/v1`
  (`schema, suite, target, checks[], findings[], summary{total,passed,failed}`,
  плюс `duration_seconds` через `summarize(**extra)` — есть не у всех сьютов).
- Порт-контракт: `UPCP_PORT_*` — канонический префикс (память task-0119;
  scaffold-контракт `test_bootstrap_scaffold.py` шаблоны не трогаем).
  Тест- compose в контракт-тестах не покрыт — новые тесты добавляем сами.
- `observability/prometheus-test.yml`: jobs `upcp-app`, `upcp-otel`,
  `prometheus` (scrape 15s) — добавляем job `upcp-security` → `pushgateway:9091`.
- Порты: `.env.test` секция Observability (`UPCP_PORT_PROMETHEUS=39091` …) —
  pushgateway в test-стеке → `UPCP_PORT_PUSHGATEWAY=39092` (рядом с 39091);
  dev/stage ком-файлы не меняются (сервис только в docker-compose.test.yml).
- Grafana: дашборды `observability/grafana/dashboards/test/*.json`
  (schemaVersion 39, `datasource: {"type": "prometheus"}` без uid — шаблон
  `performance.json`, uid-префикс `upcp-test-*`), папка provisioned
  (`test-dashboards.yaml`) — свой файл `security.json` подхватится автоматически.
- Контракт-тесты: `backend/tests/test_observability_configs.py` — text-level
  assertions без YAML-зависимости (стиль TASK-0151) — расширяем тремя тестами.
  Runner-логику тестим отдельным файлом `backend/tests/test_security_runner_push.py`
  (загрузка корневого модуля через sys.modules pre-registration — паттерн
  `test_zap_scan_auth._load_zap_scan`).
- Docs: `docs/11-docker-and-ports.md` (таблица Port Variables),
  `docs/ops/observability-stack.md` (§3 Prometheus / §9 Ports),
  `tests/security/README.md` (Known limitations: «Grafana ingestion … deferred»
  — устарело, закрывается здесь). RU-дерева docs нет — держим EN-прецедент.

## Design decisions

- Сервис compose: `prom/pushgateway:latest` (стиль `prom/prometheus:latest` в
  этом же файле), `127.0.0.1:${UPCP_PORT_PUSHGATEWAY:-39092}:9091`,
  profile `observability`.
- Метрики (gauge, на каждый результат прогона):
  - `upcp_security_pass{suite}` — 1 при `summary.failed == 0`, иначе 0
    (infra-результаты runner'а → 0);
  - `upcp_security_findings{suite,severity}` — по 4 severities ВСЕГДА
    (high/medium/low/info, нули включительно — стабильные серии для дашборда);
  - `upcp_security_duration_seconds{suite}` — только если поле есть в
    результате (честные пробелы вместо фиктивных нулей);
  - `upcp_security_timestamp{suite}` — unix-время пуша.
- Группирующий ключ: `/metrics/job/upcp_security/suite/<suite>` (last-push-wins
  на сьют — ровно нужная семантика «свежий прогон»).
- **Best-effort**: недоступность pushgateway — warning в stderr, runner-код
  прогона НЕ меняется (наблюдаемость не ломает гейт). Env: `PUSHGATEWAY_URL`
  (дефолт `http://127.0.0.1:39092`, стиль `SECURITY_BASE_URL`).

## Acceptance Criteria

- [x] `docker-compose.test.yml`: сервис `pushgateway` (canonical
      `UPCP_PORT_PUSHGATEWAY`, profile observability); `.env.test`: порт 39092
- [x] `observability/prometheus-test.yml`: job `upcp-security` → `pushgateway:9091`
- [x] `tests/security/runner.py`: пуш после каждого прогона (все ветки exit),
      stdlib-only, best-effort (gateway down ≠ change exit code)
- [x] `observability/grafana/dashboards/test/security.json`: панели по
      `upcp_security_pass` / `findings{severity}` / `duration` / `timestamp`
- [x] RED-тесты → green: 3 контрактных в `test_observability_configs.py`
      (compose/prometheus/dashboard) + `test_security_runner_push.py`
      (exposition-тело, PUT + grouping key, best-effort, wiring в main)
- [x] **Live verification** (env-lifecycle): up (стек + pushgateway + prometheus)
      → прогон сьюта → `curl` метрик на gateway → query в prometheus → down
- [x] Gates: pytest (полный сьют), ruff; README/docs синхронизированы
- [x] PROJECT_STATUS: пункт §8-B зачёркнут
- [x] Отклонения зафиксированы

## Evidence

- **Live env-lifecycle run #5 (2026-10-25, `DONE_LIVE5`)**:
  - сьют `fuzz` против живого стека: **55/55 checks, 0 failed, RUN_RC=0**
    (auth_bypass 24, injection 16, malformed 15);
  - runner stdout: `pushgateway: published suite=fuzz`;
  - gateway `curl 127.0.0.1:39092/metrics` — 7 серий:
    `upcp_security_pass{suite="fuzz"} 1`,
    `upcp_security_findings{suite="fuzz",severity=high|medium|low|info} 0`,
    `upcp_security_duration_seconds{suite="fuzz"} 0.48`,
    `upcp_security_timestamp{suite="fuzz"} 1.792898295e+09`;
  - **scrape**: prometheus `/api/v1/targets` →
    `job=upcp-security health=up lastError=` (target `pushgateway:9091`);
  - **query**: `upcp_security_pass` →
    `{suite="fuzz", instance="pushgateway:9091", job="upcp-security"} = 1`;
    `sum by (severity)(upcp_security_findings)` → 4 серии (все 0);
  - Grafana-сторона: контракт-тест на `security.json` (uid + все три
    метрики в promql) + provisioned-папка `test/` (покрыта TASK-0152).
- **Тесты (TDD red → green)**: red **8 failed** → green **11 passed** —
  `test_observability_configs.py` +3 (compose/prometheus/dashboard),
  `test_security_runner_push.py` ×5 (exposition, pass/duration-omission,
  PUT+grouping key, best-effort, wiring `main`). Промежуточный red поймал
  `urllib.Request(data=)` → **POST вместо PUT** — исправлено (PUT =
  полная замена метрик grouping key).
- **Гейты**: полный сьют **1045 passed** (RC=0), `ruff check` +
  `ruff format --check` по всем изменённым файлам — clean.

## Deviations / notes

- **Live #5: prometheus поднялся на 39090, а не 39091** — shell-окружение
  launcher'а грузит root `.env` (`UPCP_PORT_PROMETHEUS=39090`, строка 6), а
  precedence compose: shell env > `--env-file` (тот же механизм, что
  описан для `GRAFANA_ADMIN_PASSWORD` в `docs/ops/observability-stack.md`
  §4.3). Новый `UPCP_PORT_PUSHGATEWAY` в root `.env` отсутствует → корректно
  получил 39092 из `.env.test`. Query-evidence снято по фактическому 39090.
- **`down` без профиля не снимает observability-сервисы**: итоговый
  `down --remove-orphans` удалил core-контейнеры, но pushgateway/prometheus
  остались (network «still in use») — сняты повторным
  `--profile observability down`. Для будущих прогонов: down с теми же
  профилями, что и up.
- **PUT, не POST**: `urllib.request.Request(data=…)` по умолчанию шлёт POST —
  тест поймал до live; PUT обязателен (иначе устаревшая серия
  `duration_seconds` переживёт прогон без duration).
- **`duration_seconds` есть не у всех сьютов** → серия публикуется только
  при наличии поля (честные пробелы вместо фиктивных нулей).
- **Смежная docs-синхронизация**: в `docs/11-docker-and-ports.md` заодно
  исправлены устаревшие ячейки Test-колонки (PROMETHEUS → 39091,
  GRAFANA → 33001 — фактические значения `.env.test`).

## Files

| File | Action |
|------|--------|
| `docker-compose.test.yml` | MODIFY — сервис pushgateway |
| `.env.test` | MODIFY — `UPCP_PORT_PUSHGATEWAY=39092` |
| `observability/prometheus-test.yml` | MODIFY — job `upcp-security` |
| `tests/security/runner.py` | MODIFY — `build_push_body` + `push_metrics` + wiring |
| `observability/grafana/dashboards/test/security.json` | CREATE — дашборд |
| `backend/tests/test_observability_configs.py` | MODIFY — 3 контракт-теста |
| `backend/tests/test_security_runner_push.py` | CREATE — red-тесты пуша |
| `tests/security/README.md` | MODIFY — §8-B закрыт (K limitations) |
| `docs/11-docker-and-ports.md` | MODIFY — строка порта |
| `docs/ops/observability-stack.md` | MODIFY — §3.3 Pushgateway + §9 порт |
| `tasks/TASK-0158-security-results-pushgateway.md` | CREATE — этот файл |
