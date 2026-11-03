# TASK-0170 — Agent auth dependency (API key): TTL, scopes, единая верификация

**Source:** SPEC-0028 §3.3 (S28.3), решение D1 (Dmitry 2026-11-02: остаёмся
на статическом API-ключе + TTL + отзыв + hardening)
**Milestone:** auth rework (SPEC-0028 batch)
**Spec:** SPEC-0028 §3.3, AC4/AC6/AC7; SPEC-0029 S29.4
**Points:** 5
**Status:** PENDING (реализация не начата)

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
