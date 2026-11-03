# TASK-0175 — Unify identity dependencies on services: get_current_user / get_current_agent / permission cache

**Source:** SPEC-0029 §3.5 (S29.5); findings 4-5-7 спецификации
**Milestone:** auth rework (SPEC-0029 batch)
**Spec:** SPEC-0029 §3.5, AC5; SPEC-0028 AC8 (кеш прав)
**Points:** 3
**Status:** DONE (2026-11-04; commits 042b2c4 + 3e6dc74 на `feature/TASK-0168-api-surface-registry`)

## Context

- `get_current_user` (`auth.py:65`) ходит в БД напрямую **без кеша** на
  каждый запрос — дублируя subject-проверку middleware (finding 7).
- `get_current_agent` (`agent_auth.py`) сам делает запросы + `flush`,
  дублируя логику middleware-ветки (finding 4).
- `permissions.py` (`_query_permissions`/`_cached_permissions`) содержит
  инлайново и DB-query, и Redis-кеш (finding 3-й той же формы).

## Goals

1. `get_current_user` → поверх `SubjectStateService` + `UserRepository`
   (кеш работает и в dependency-пути; ответы/исключения не меняются).
2. `get_current_agent` → поверх `AgentTokenService` (одна семантика
   touch: обе точках — либо flush внутри сервиса, либо commit —
   выбрать одну, соответствующую commit-invariant из `service.py`).
3. Кеш пар прав (`rbac:user_perms:*`) → через `AuthCacheProvider`;
   DB-query → `PermissionRepository`; логика гейта (fail-closed порядок,
   superuser bypass) не трогается.
4. После этого: ни одного прямого `db.query` в `identity/auth.py`,
   `agent_auth.py`, `permissions.py` (grep-контракт расширяется).

## Test design (совместная проработка до кода — SPEC-0029 §6 / D6)

- **Behavior:** все существующие тесты `/auth/me`, logout, password
  change, agent-зависимости, RBAC-гейты — зелёные без смены семантики.
- **Boundaries:** dependency-путь тоже получает кеш (второй вызов — 0 DB
  reads через cache-spy — этого в поведении раньше не было: это
  намеренное улучшение, фиксируется тестом как AC); disabled-юзер → 401.
- **Conditions:** Redis down → фолбэк в БД (spec-паритет AC5 SPEC-0027).
- **AC:** SPEC-0029 AC5 (дедуп), расширенный AC1 (grep: `db.query` в
  трёх файлах отсутствует), паритет-AC8.
- **Matrix:** unit — паритет-вызовы до/после (одинаковые ответы на
  входные состояния); integration — кеш-спай в dependency-пути;
  regression — RBAC suite + authz live.

## Decomposition

| # | Item | Depends |
|---|---|---|
| 1 | `get_current_user` на сервисах (red: cache-spy тест) | 0174 |
| 2 | `get_current_agent` на `AgentTokenService` (единый touch) | 0174 |
| 3 | Permission cache/Query → provider + repository | 0174 |
| 4 | Grep-контракт + полный прогон | 1-3 |

## Evidence (2026-11-04)

### Red → Green

**Red** (4 новых файла + boundary, ДО реализации): `21 failed, 53 passed`.

- `test_identity_user_dependency` (3): cache-spy `get_auth_state` = 0 ≠ 1
  (cold/warm) и `AttributeError: get_by_id` — get_current_user ещё не
  ходил в сервисы;
- `test_identity_agent_dependency` (9): `AttributeError: verify_detailed`
  ×7, commit-spy 0 ≠ 1, плюс `test_expired_token…` → 500
  `TypeError: can't compare offset-naive and offset-aware datetimes`
  (известный SQLite-баг СТАРОГО dependency-пути, чинится сервисом);
- `test_identity_permission_cache` (4): `ImportError: PermissionRepository`
  (corrupt ×3 + cache-spy);
- `test_identity_layering_contract` (5): `db.query` в auth.py /
  agent_auth.py / permissions.py, `hashlib` в agent_auth.py,
  precondition mutation-теста на permissions.py.

**Green**: targeted `74 passed`; коммит 1 проверен изолированно на своём
дереве (`git stash push --keep-index -u`): `125 passed` (новые тесты +
boundary + parity-подмножество).

### Gates (final tree, 3e6dc74)

| Gate | Result |
|---|---|
| targeted: 4 новых файла + `test_context_boundaries.py` | **74 passed** |
| parity: `test_auth_endpoints test_logout_denylist test_rbac_enforcement test_security_hardening test_auth_middleware_protection test_auth_middleware_user_check test_auth_middleware` | **77 passed** (без изменений в тестах) |
| FULL: `pytest backend/tests -q -n auto` | **1223 passed, 0 failed, coverage 89.84%** (baseline 1172 / 89.79%) |
| `ruff check backend` | All checks passed |
| `ruff format --check` (мои файлы) | clean |
| `mypy backend/app` | Success: no issues found in 119 source files |

### Deviations (зафиксированы, не против AC — обоснованы)

1. **Profile-read design**: кеш обслуживает LIVENESS-путь; профиль
   (email/is_superuser) — ОДИН прямой репозитори-чтение на валидный
   запрос (как и до rewiring). Формулировка AC «0 DB reads» отнесена к
   liveness-lookup (cache-spy на `SubjectStateService`/`get_auth_state`);
   count профиля закреплён отдельным тестом (1/запрос).
2. **Commit-timing touch**: `last_used_at` теперь COMMITS внутри сервиса
   (инвариант 0174, AC4) вместо `flush()` + teardown-commit; ни один
   существующий тест не зависел от старого тайминга (проверено:
   все agent-фикстуры коммитят сиды; `last_used_at is None`-тесты — на
   создание), новый commit-spy-тест фиксирует новый контракт.
3. **Baseline**: из `context_boundary_baseline.py` удалён РОВНО один
   ключ `("identity/permissions.py", "redis", "app.shared.redis")` в том
   же коммите; остальные записи (middleware SessionLocal/redis,
   denylist) не тронуты — exact-set gate зелёный.
4. **`verify_detailed` — аддитивный API**: `AgentPrincipal |
   AgentTokenRejection(reason: unknown|revoked|expired|agent_inactive)`;
   `verify()` — тонкая обёртка (его тесты 0174 проходят без изменений).
5. **Исправление попутно (не регрессия)**: просроченный токен на SQLite
   в старом dependency-пути давал 500 (naive/aware TypeError) — через
   сервис отвечает историческим 401 (фикс 0174, перенесён в dependency).
6. **Cache-payload hardening** в permissions: некорректная структура
   (scalar, не-пары) → фолбэк в БД вместо TypeError/мусора; валидные
   payload кодируются/декодируются байт-в-байт как раньше.
7. **Тест-сессии**: session-less liveness на общем StaticPool-соединении
   откатывает uncommitted-работу fixture-сессии (эмпирический probe:
   state-read видит flushed-row, `close()` её убирает; спасает только
   identity-map `Session.get`) → сиды в моих тестах коммитятся, профиль
   читается через `Session.get` — зафиксировано в докстрингах.

### §12 Multi-factor analysis

- **Соответствие требованиям**: AC5 (одна реализация sha256/subject
  lookup в трёх файлах — контракт-тест), расширенный AC1 (grep-контракт),
  поведенческий паритет (401/403-детали байт-в-байт, TTL 60, fail-closed
  RBAC / fail-open denylist) — все закрыты тестами; AC8 зелёный.
- **Архитектура/DDS**: presentation-модули (auth/agent_auth/permissions)
  больше не содержат raw-доступа (кроме `db.get(User…)` byte-parity
  гейта); всё через repository/provider — boundary gate exact-match.
- **Производительность**: hot-path (warm) = 1 профиль-read как раньше;
  cold-path +1 read (liveness) раз в 60с на subject; reject-path стал
  0 reads (кеш); +2 Redis-операции на запрос (get+set subject) — тот же
  паттерн, что уже работает в middleware; сессий на запрос не добавлено
  (session-injected seams).
- **Безопасность**: кеш не может обойти проверку (corrupt → БД, DB-error
  пробрасывается → fail-closed); denylist/JWT-цепочка не тронута;
  секретов нет; parameterized ORM-запросы.
- **Надёжность/наблюдаемость**: provider никогда не бросает (structured
  warnings `auth.cache_*_failed`), сервис дополнительно гвардит себя
  (`auth.subject_state_cache_unavailable`); деградация — только в БД.
- **Тестируемость/качество тестов**: сиды D3-шов (session-injected /
  session-less), unit+integration+contract+parity; новые файлы ≤300
  строк (297/275/226/106); красная фаза сохранена в коммитах.
- **Документация**: докстринги всех пяти app-файлов синхронизированы;
  known nit: проза-ссылки `permissions._cached_permissions` в
  `subject_state.py`/`test_subject_state_service.py` указывают на
  исторический прецедент (функция переехала в `_resolve_user_permissions`)
  — правка затронет чужой файл/запрещённый тест, отложена в 0169/0170.

### Риски для TASK-0169/0170

- `middleware.py` не тронут: его baseline-записи (SessionLocal, redis)
  остаются; `_fetch_user_state` дублирует `SubjectStateService` до 0169 —
  в 0169/0170 переносить на сервис + шов `_get_subject_state_service`.
- `_hash_token` после задачи остаётся в `middleware.py` (умирает в 0170),
  `agent_endpoints.py` (создание токена) и `token_service.py`
  (refresh/access-домен) — формулировка «остался только middleware»
  верна ТОЛЬКО для agent-token-верификации (agent_auth.py чист).
- 0170: middleware-ветка может вызывать `verify_detailed`, но её
  detail-строки отличаются (revoked → «Invalid agent token») — маппинг
  причин оставить на middleware.
