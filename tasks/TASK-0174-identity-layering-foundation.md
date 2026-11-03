# TASK-0174 — Identity layering foundation: repositories + cache provider + сервисы

**Source:** SPEC-0029 §3.1-S29.4; Dmitry 2026-11-02 («middleware сам
запрашивает БД… нужен сервис, внутри — repository, кеш — отдельным
провайдером»)
**Milestone:** auth rework (SPEC-0029 batch)
**Spec:** SPEC-0029 §3.1-3.4, AC1-AC4, AC6
**Points:** 8
**Status:** PENDING (реализация не начата)

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
