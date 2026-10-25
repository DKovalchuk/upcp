# TASK-0157 — ZAP authenticated baseline (hook + login-mint) [backlog §8 item A]

**Source:** SPEC-0027 backlog §8 («ZAP authenticated baseline (скрипты image без `-H`)»);
`tests/security/dast/README.md` Auth-section follow-up («needs a context file
+ auth script mount»); решение Dmitry 2026-10-25 (ask): **Hook + login-mint**
**Milestone:** backlog §8
**Spec:** mini-spec (AC ниже) — производный от SPEC-0024 Phase4/SPEC-0027
**Points:** 5
**Status:** DONE (2026-10-25 — live `SCAN_RC=0`, гейты green)

## Objective

Сделать ZAP baseline/full-скан **аутентифицированным**: покрывать защищённую
поверхность (страницы под сессией + API под Bearer), сохранив stock-образ и
redaction-контракт.

## Investigation (2026-10-25, evidence — probe самого образа)

- `zap-baseline.py -h` (ghcr.io/zaproxy/zaproxy:stable): **нет `-H`** ✓
  (README прав); есть `-n context_file`, `-U user`, **`--hook <py>`**,
  `--plan-only`; отдельного `zap-automationFramework.py` нет (AF встроен
  через `--auto`, помеченный unsupported при `--hook` — классический флоу).
- `zap_common.py`: `load_custom_hooks` (SourceFileLoader) →
  `trigger_hook('cli_opts'|'zap_started', zap, target|'zap_tuned',
  zap|'zap_pre_shutdown'|'pre_exit')` — **хук получает ZAP API-клиент** ✓.
- Bearer-логин невозможен в context-файле без скриптов (README) → хук сам
  чеканит токен: `POST <target>/auth/login` (stdlib urllib, в-контейнере
  сеть compose доступна: target `http://app:8080`) → глобальный заголовок
  через `network.addHttpRequestHeader('Authorization', 'Bearer …', True)`.
- Seed-покрытие API: classic-spider JSON не обходит → хук форсит
  `core.access_url()` для списка probe-URL из конфига (пассив+актив
  baseline правил прогоняются по ответам, инстансы попадают в JSON-отчёт
  с `uri=http://app:8080/api/v1/...` = доказательство покрытия).
- Creds: `tests/security/common.py` — `PERF_EMAIL=admin@example.com`,
  `PERF_PASSWORD=TestAdmin123!` (env-переопределяемые дефолты, сидинговые
  тестовые — не прод-секреты). Хук читает их **из env в-контейнере** →
  в генерируемом файле/артефактах секретов НЕТ; compose передаёт env в
  zap-сервис. Один логин на прогон — лимит /auth/login 5/min не задевается.
- Redaction уже покрывает JWT/bearer (`zap_config.yaml: redact.patterns`)
  → токен в логах/отчётах = REDACTED ✓.

### Iterations 1-3 (live) + static probes → финальный механизм (2026-10-25)

Live-итерации сузили дизайн (все — строгий rc2, никакого тихого фоллбэка):

1. **run #1**: `AttributeError: network has no addHttpRequestHeader` —
   generated python-zap v0.6.0 не знает метода (48 network-методов без него).
2. **run #2**: raw JSON к `127.0.0.1:8080` → `Connection refused` — демон
   НЕ на loopback:8080: скрипты строят клиент как
   `ZAPv2(proxies={'http': 'http://<zap_ip>:<port>'})` с `port = get_free_port()`
   (`zap-baseline.py:398-399,551`).
3. **run #3**: `zap.base = http://zap/JSON/` → `EAI_AGAIN` (DNS `zap`
   из ран-контейнера не резолвится) — но клиент при этом работает:
   `zap-baseline.py:553→554` — `wait_for_zap_start(zap)` (транспорт
   `_request` → `session.request(..., proxies=<script-built>)`) проходит
   **до** `trigger_hook('zap_started')` ⇒ рабочий путь = только клиентский.

Static-пробы образа (docker run, zipfile-скан jar/плагинов):

- `network.addHttpRequestHeader` **не существует вовсе**: нет в generated
  клиенте, нет в `/zap/zap-2.17.0.jar`, нет в `network-beta-0.25/0.31.zap`
  (zipfile-scan class-констант; `unzip` в образе есть — результаты надёжны).
  Сырой URL-путь к network API мёртв по определению.
- Клиентский `_request(url, ...)` = `requests.Session().request(..., proxies=
  self.__proxies)` с guard `url.startswith('http://zap/')` — единственный
  доказанно живой транспорт (тот же путь, что version-poll).
- **Replacer** — аддон в `/zap/plugin/` (release-21/22; addRule/setRule есть
  и в main jar), клиентский метод `replacer.add_rule(...)` →
  `replacer/action/addRule/`. Официальная справка аддона (извлечена из
  help-плагина): match type **Request Header = «will add if not present»**
  (match string = имя заголовка, replacement = значение) — ровно нужная
  семантика; `Match Regex` при этом отключён.

Финальный дизайн хука: mint (POST /auth/login, env-креды) →
`zap.replacer.add_rule(REQ_HEADER, matchstring=Authorization, replacement=
Bearer <token>)` (envelope != ok → status error) → probes через
`ProxyHandler` по адресу из `getattr(zap, '_ZAPv2__proxies')['http']`
(путь сканового трафика: пассивный скан видит ответы) со строгой проверкой
HTTP-статуса: **401/403/5xx = заголовок не внедрён → status error → wrapper
rc2**; статус-файл `ok header=replacer probes=N codes=…`.

## Acceptance Criteria

- [x] `zap_config.yaml`: секция `auth` (`enabled`, `login_path`,
      `probe_urls[]`) — секретов в файле нет (только env-имена/URL)
- [x] Wrapper: генерация `zap_auth_hook_<ts>.py` в report-dir + `--hook`
      в command (при auth.enabled), очистка хука после прогона;
      mint-failure → infra-код 2 (жёсткий: сломанная аутентификация =
      сломанный authenticated-baseline, не тихий unauth-фоллбек)
- [x] RED-тесты (backend/tests — скоуп pytest): build_command c `--hook`;
      рендер хука содержит login/probe/`Authorization` и **не содержит**
      кредов; main() пишет и удаляет хук-файл (mocked subprocess);
      auth.enabled=false → без `--hook`; + 4 exec-теста сгенерированного
      хука (успех/отказ replacer/probe 401/mint-failure)
- [x] **Live verification** (env-lifecycle: up → run → down): скан с хуком
      зелёный; в scan-log строка mint+header (redacted); в JSON-отчёте
      инстансы с `uri=…/api/v1/…` (доказательство authenticated-достижимости)
- [x] Gates: pytest (полный сьют), ruff/mypy; README даст обновлён
- [x] PROJECT_STATUS: пункт §8-A зачёркнут
- [x] Отклонения зафиксированы

## Evidence

- **Live run #4 (2026-10-25, env-lifecycle up → seed → scan → down,
  `DONE_LIVE4`)**:
  - scan-log `zap_baseline_20261025-050217.log`: `auth_hook: minted token
    (REDACTED)`, `auth_hook: replacer addRule -> 'OK'`, `auth_hook: probe
    via proxy http://localhost:47170`, `probe / -> HTTP 404`,
    `probe /api/v1/projects -> HTTP 200`, `probe /api/v1/agents -> HTTP 200`,
    `probe /api/v1/analytics/agents/overview -> HTTP 200`;
  - wrapper: `SCAN_RC=0` (high=0 medium=0 low=1 info=1) — строгая проверка
    статус-файла пройдена (`ok header=replacer probes=4 codes=404,200,200,200`);
  - ZAP JSON: `api_uri_count=7`, уникальные URI — `http://app:8080/api/v1/agents`,
    `…/analytics/agents`, `…/analytics/agents/overview`, `…/projects` =
    AC «инстансы с `uri=…/api/v1/…`» ✓;
  - результат `tests/security/results/zap_auth_live.json` (suite `zap`),
    стек поднят/опущен чисто.
- **Тесты (TDD red → green)**: `test_zap_scan_auth.py` (7: конфиг-секция,
  рендер-маркеры без секретов, build_command ± `--hook`, main lifecycle +
  cleanup, disabled → legacy, status-missing → rc2) +
  `test_zap_auth_hook.py` (4: успех со всеми аргументами add_rule и proxy;
  addRule-отказ → без probes; probe 401 → `error probe`; mint-failure → без
  правила) — red `4 failed` → green `11 passed`.
- **Гейты**: полный сьют **1037 passed** (RC=0); `ruff check` +
  `ruff format --check` по изменённым файлам — clean. Mypy-гейт проекта =
  `backend/app` (pre-commit `files: ^backend/app/`) — код задачи его не
  затрагивает (изменённые пути: `tests/security/dast/*`, `backend/tests/*`,
  compose, docs); тесты `backend/tests` по конвенции проекта вне mypy-охвата
  (проверено на существующем тест-файле — та же картина).

## Deviations / notes

- **Механизм: replacer вместо network API** (AC подразумевал
  `network.addHttpRequestHeader`): метода нет ни в python-zap v0.6.0, ни в
  ZAP 2.17.0 (zipfile-скан `zap-2.17.0.jar` + `network-beta-*.zap` — сырой
  URL-путь мёртв по определению). Заменён на replacer-правило `REQ_HEADER`
  (официальная семантика аддона «will add if not present») — глобальный
  заголовок на весь трафик скана, поведенчески эквивалентно.
- **Probes через прокси-транспорт клиента** вместо `core.access_url`:
  `access_url` не возвращает HTTP-статус; `ProxyHandler` по адресу из
  `_ZAPv2__proxies` даёт код ответа → «auth сработал» = доказательство
  (200), «не внедрён» = строгий отказ (401/403 → rc2), плюс трафик идёт
  путём самого скана (пассивный скан записывает ответы).
- **Приватный `_ZAPv2__proxies`** — ровно то, что скрипты кладут в
  `ZAPv2(proxies=…)` (`zap-baseline.py:551`); порт даёт `get_free_port()`
  (live: `localhost:47170`) — хардкод невозможен; закреплено контракт-тестом.
- **`addRule` отвечает `'OK'`** (не `'ok'`) — проверка нормализует регистр
  (`.strip().lower()`), подтверждено live.
- Итерации #1-#3 (AttributeError → refused → EAI_AGAIN) — в Investigation.

## Files

| File | Action |
|------|--------|
| `tests/security/dast/zap_config.yaml` | MODIFY — секция auth (+ комменты механизма) |
| `tests/security/dast/zap_scan.py` | MODIFY — hook-генерация (replacer + proxy probes), command, cleanup, mint-failure |
| `tests/security/dast/README.md` | MODIFY — Auth-секция (implemented), exit-code 2 |
| `docker-compose.test.yml` | MODIFY — env кредов в zap-сервис |
| `backend/tests/test_zap_scan_auth.py` | CREATE — red-тесты контракта wrapper'а/рендера |
| `backend/tests/test_zap_auth_hook.py` | CREATE — exec-тесты сгенерированного хука |
