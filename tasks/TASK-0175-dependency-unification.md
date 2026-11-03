# TASK-0175 — Unify identity dependencies on services: get_current_user / get_current_agent / permission cache

**Source:** SPEC-0029 §3.5 (S29.5); findings 4-5-7 спецификации
**Milestone:** auth rework (SPEC-0029 batch)
**Spec:** SPEC-0029 §3.5, AC5; SPEC-0028 AC8 (кеш прав)
**Points:** 3
**Status:** PENDING (реализация не начата)

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
