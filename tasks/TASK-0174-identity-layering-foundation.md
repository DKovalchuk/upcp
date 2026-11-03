# TASK-0174 — Identity layering foundation: repositories + cache provider + сервисы

**Source:** SPEC-0029 §3.1-S29.4; Dmitry 2026-11-02 («middleware сам
запрашивает БД… нужен сервис, внутри — repository, кеш — отдельным
провайдером»)
**Milestone:** auth rework (SPEC-0029 batch)
**Spec:** SPEC-0029 §3.1-3.4, AC1-AC4, AC6
**Points:** 8
**Status:** DONE (2026-11-03 — repository + AuthCacheProvider +
SubjectStateService/AgentTokenService, red→green, все gates зелёные)

## Context

В identity нет repository-слоя вообще (repo-wide grep: 0); middleware
делает `SessionLocal`-запросы и содержит кеш-логику инлайново
(`_fetch_user_state`, `_user_state`, ветка agent-token); логика
agent-token продублирована дважды с разной семантикой записи
(`commit` vs `flush`); `sha256` дублируется. Это пилот слоистого
паттерна (D2) для всей дальнейшей работы (SPEC-0028 потребляет сервисы).

## Goals

1. `identity/repositories.py` — **единственный** модуль auth-пути с
   `SessionLocal`/`db.query` (S29.1): `UserRepository.get_auth_state`,
   `AgentTokenRepository.find_by_hash` / `touch_last_used`,
   `AgentRepository.get`. Lazy-import `SessionLocal` сохранён
   (тестовый шов, SPEC-0029 D3).
2. `identity/cache_provider.py` — **единственный** доступ к Redis в
   auth-пути (S29.2): `AuthCacheProvider.get/set/delete`, никогда не
   бросает наружу; инжектируем (фейк в тестах).
3. `identity/subject_state.py` — `SubjectStateService(repo, cache)`
   (S29.3): cache-aside TTL 60s, DB авторитетна, Redis-outage → DB.
4. `identity/agent_token_service.py` — `AgentTokenService(repo)`
   (S29.4): единый `sha256`, revoked/expired/agent-active, touch через
   репозиторий с commit-before-response (устраняет commit/flush-расхождение).
5. Тестовые швы мигрируют: патчим repository/provider-конструкторы, а не
   `mw._fetch_user_state` / модульные приватки (SPEC-0029 D3, AC6).

## Test design (совместная проработка до кода — SPEC-0029 §6 / D6)

- **Behavior:** сервисы дают в точности прежние результаты/исключения
  (паритет — SPEC-0029 D4): состояния `active|unknown|disabled`;
  `verify` → principal/None по жизненному циклу ключа.
- **Boundaries:** cold cache / hit / TTL-протухание / Redis-down /
  повреждённое значение в кеше (parse-fail → фолбэк в БД, как сейчас
  в `permissions._cached_permissions`); одновременные misses
  (допустим двойной DB-read — не строим дистрибутивную блокировку).
- **Conditions:** реальный DB + фейковый Redis; реальный Redis + убитый
  DB-фолбэк; часы на границе TTL (expires edge — frozen clock).
- **AC:** SPEC-0029 AC1 (grep-контракт), AC3 (cache-spy: 1-й вызов 1 DB
  read + 1 write, 2-й — 0 reads), AC4 (одна точка touch), AC5 (один
  sha256), AC6 (швы), AC8.
- **Matrix:**
  - unit: кеш-политика (позитив hit, негатив miss, негатив outage,
    граница TTL), verify-матрица (valid/revoked/expired/inactive ×5),
    репозитории — по состоянию (unknown/disabled/None).
  - integration: оба направления фолбэка (cache-down→DB, db-miss→…);
    commit-invariant: сразу после verify следующий запрос видит
    `last_used_at`.
  - contract: grep-тест AC1/AC5.
- **Red-фаза:** сервисные тесты написать до выноса логики из middleware
  (на текущей логике — characterization, потом переключение).

## Decomposition

| # | Item | Depends |
|---|---|---|
| 1 | Репозитории + provider (red: контракты пустые → green) | — |
| 2 | `SubjectStateService` (кеш-политика red→green) | 1 |
| 3 | `AgentTokenService` (жизненный цикл red→green, touch-инвариант) | 1 |
| 4 | Миграция тестовых швов + grep-контракт AC1/AC5 | 2-3 |
| 5 | Evidence: полный прогон (паритет) | 4 |

## Notes

- Middleware в этой задаче НЕ переписывается — сервисы вводятся как
  новый источник; подключение (`web_auth`/`agent_auth`) — TASK-0169/0170.
  Допустимо временно два потребителя (middleware + сервисы), если это
  снижает размер диффа; финальное удаление старого пути — в 0169.

## Evidence (2026-11-03)

Ветка `feature/TASK-0174-identity-layering-foundation`, коммит `6627ed9`
(8 файлов, +1273; pre-commit ruff/format/mypy Passed). Новые модули:
`identity/repositories.py`, `identity/cache_provider.py`,
`identity/subject_state.py`, `identity/agent_token_service.py` + 4
тестовых файла; существующие файлы не тронуты (scope соблюдён).

**Red (до реализации):** `pytest <4 новых файла> -q` →
`4 errors during collection — ModuleNotFoundError: No module named
'app.identity.repositories' / 'app.identity.cache_provider' /
'app.identity.subject_state' / 'app.identity.agent_token_service'`.

**Green (финальное состояние):**

| Gate | Результат |
|---|---|
| targeted (3 файла брифа) | `38 passed` |
| `test_auth_cache_provider.py` (4-й файл) | `9 passed` (итого 47 новых тестов) |
| auth parity subset (4 файла) | `36 passed` |
| полный прогон `backend/tests -n auto` | `1172 passed, 0 failed`, coverage **89.79%** (≥80%) |
| покрытие новых модулей | 100%: repositories 60/60, cache_provider 26/26, subject_state 30/30, agent_token_service 31/31 |
| `ruff format` + `ruff check` (8 новых файлов) | `8 files already formatted`, `All checks passed` |
| `ruff check backend` | 4 ошибки — все в `backend/tests/test_context_boundaries.py` (см. отклонения 8); `ruff check backend/app/identity` → `All checks passed` |
| `mypy backend/app` | `Success: no issues found in 119 source files` |

**Решение по семантике записи (AC4):** `touch_last_used` выполняет
COMMIT внутри единственной точки записи, которую вызывает сервис —
к моменту возврата `verify()` запись закоммичена (commit-before-response,
`service.py`/TASK-0142). Расхождение middleware-`commit()` vs
agent_auth-`flush()` снято в пользу commit.

**Отклонения от спеки/брифа и причины:**

1. Повреждённое значение кеша (не из `active|unknown|disabled`) →
   фолбэк в БД + перезапись, как `permissions._cached_permissions`
   (по Test design D6 задачи). `_user_state` возвращал мусор как есть →
   401; для трёх легитимных состояний поведение байт-в-байт.
2. tz-naive `expires_at` трактуется как UTC (`_ensure_utc`): на SQLite
   строгое `naive < aware` бросало TypeError (middleware → generic 401,
   agent_auth → 500 при `expires_at != NULL`). На Postgres (offset
   сохраняется) поведение не меняется; без нормализации expired-матрица
   на тестовом движке неисполнима.
3. Grep-контракты AC1/AC5 в этой задаче не добавлялись: middleware и
   agent_auth ещё содержат `SessionLocal`/`_hash_token` (двухпотребительский
   период по Notes) — контракт упал бы by design; переносится в TASK-0175
   вместе с переключением потребителей.
4. Commit-invariant проверен на shared engine: спай `Session.commit`
   (ровно 1 вызов за `verify`) + persistence-чтение после закрытия
   session-less репозитория; двухдвижковый TASK-0142-пробник запрещён
   `test_engine_dedup.py` (allowlist не расширять — правка существующего
   теста вне скоупа).
5. Четвёртый тестовый файл `test_auth_cache_provider.py` сверх трёх
   предложенных: контракт провайдера (never-raise, warnings) — отдельная
   единица; каждый файл ≤300 строк.
6. `scopes: dict[str, object] | None` вместо `dict | None` — mypy strict
   (`disallow_any_generics`); структурно идентично и совпадает с
   `CurrentAgent`.
7. Даты: шаблон брифа указывал 2026-11-02; фактические прогоны и
   завершение — 2026-11-03.
8. Рабочая среда: во время сессии параллельная сессия дописывает
   untracked `backend/tests/test_context_boundaries.py` (mtime во время
   прогона; +23 теста в полном наборе между прогонами) — файл вне моего
   скоупа, его 4 ruff-ошибки не мои и не тронуты; все мои файлы чисты.

**Multi-factor analysis (AGENTS §12):**

- *Требования:* AC2/AC3/AC4/AC6/AC8 закрыты тестами (cache-spy ровно
  1 DB read + 1 write / 0 reads, commit-spy, seam-тесты, паритет-подмножество
  без правок существующих файлов); AC1/AC5 — частично (новые модули
  изолированы, полный grep — в 0175, см. отклонение 3); потребители не
  изменены (scope-проверка: git status только 8 новых файлов).
- *Архитектура:* слои service → repository/cache (D1) внутри identity
  (DDD, пилот D2); внедрение через конструктор; presentation-слой не
  тронут; модули небольшие (78–122 строки), без god-объектов; импортная
  цикличность отсутствует (новые модули ничего не импортируют из
  middleware/auth).
- *Производительность:* hot-path не деградировал — cache hit = 0 DB
  запросов, miss = 1 SELECT + 1 SET (как `_user_state`); agent-путь:
  2 SELECT + 1 UPDATE/COMMIT (как middleware сегодня); новых сессий на
  запрос не добавлено (шов per-call заменяет прежний инлайновый
  `SessionLocal()`).
- *Безопасность:* обхода auth нет при любом сбое кеша (БД авторитетна,
  состояние не «изобретается»); sha256 единый; все запросы
  параметризованы (`filter_by`/`db.get`); секретов нет; логируются
  только ключи и причины деградации, не токены.
- *Наблюдаемость:* структурированные warnings с `action`
  (`auth.cache_{get,set,delete}_failed`,
  `auth.subject_state_cache_unavailable`), `entity_type`, `cache_key`;
  DB-ошибки не глушатся (propagate); метрики/спаны отказов остаются у
  потребителей (D4 — не дублировать).
- *Тестируемость:* швы D3 — lazy `SessionLocal` (патч conftest),
  constructor-session, патч `app.shared.redis.get_redis_client`;
  stub-репозитории/кеш для юнит-матрицы, реальная БД через `db_session`
  для интеграции; 47 тестов: позитивы, негативы (×5 жизненного цикла
  токена, outage, corrupt, disabled/unknown), границы (TTL-протухание,
  `expires_at == now`, naive/aware), оба направления фолбэка, 100%
  покрытие новых модулей.
- *Документация:* docstrings модулей ссылаются на SPEC-0029 §/AC и
  TASK; статус задачи и Evidence обновлены; PROJECT_STATUS, спеки и
  чужие задачи не тронуты (вне скоупа).

**Заметки для downstream (0169/0170/0175):**

- `verify()` возвращает `None` для всех отказов — различие 401-detail
  («has expired» / «not found or inactive») живёт у потребителя; в
  тестах детальные строки не закреплены.
- DB-ошибки из `verify()` всплывают: middleware-потребитель должен
  сохранить свой broad-except → fail-closed 401; для agent-зависимости
  (0175) решение 500-vs-401 принять осознанно.
- Session-less репозитории возвращают detached-but-loaded записи:
  читать можно, мутировать вне `touch_last_used` нельзя.
- `AgentPrincipal` поля совпадают с `CurrentAgent` (agent_id/name/scopes).
- Состояние тестового шва: `SubjectStateService.get` не пишет
  метрики/логи отказов — их место у потребителей (`_reject_subject`).
