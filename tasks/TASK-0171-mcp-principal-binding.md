# TASK-0171 — MCP principal binding: agent_id из контекста, не из аргументов

**Source:** SPEC-0028 §3.4 (S28.4), finding 4 (critical); Dmitry
2026-11-02 («Для чего мы делали аутентификацию?»)
**Milestone:** auth rework (SPEC-0028 batch)
**Spec:** SPEC-0028 §3.4, AC5 (+D5 inventory)
**Points:** 5
**Status:** PENDING (реализация не начата)

## Context

`AuthMiddleware` выставляет `request.state.agent_id`, но
`handle_jsonrpc` (`mcp/server.py`) вообще не получает Starlette
`Request` — состояние теряется на границе. MCP-инструменты принимают
`agent_id` **из аргументов вызова** (`mcp/tools.py:591+`): любой
аутентифицированный агент может claim/release/heartbeat от имени
другого агента. Аутентификация есть, привязки принципала → действие нет.

## Goals

1. Принципал из agent_auth (SPEC-0028 S28.3) провайдится в JSON-RPC
   dispatch: роут `/mcp` получает `Request`, `call_tool(...)` принимает
   principal явно (передача контекста — не глобальные mutable-переменные).
2. `agent_id` в аргументах инструмента сверяется с принципалом:
   несовпадение → отказ (403-эквивалент JSON-RPC error + structured
   warning + span attrs); совпадение → работает. Для user-JWT-вызовов
   (если D5 оставит dual-accept) — политика: только явные admin-инструменты.
3. Инвентаризация вызывающих `/mcp` (Bearer vs X-Agent-Token) — решение
   D5 (tighten до agent-only либо временный dual-accept с tracked-задачей).
4. Убрать попутные `SessionLocal`-фолбэки в `mcp/tools.py`/`context_pack.py`
   в пользу сессии запроса (перекликается с SPEC-0029 §8).

## Test design (совместная проработка до кода — SPEC-0028 §6 / D6)

- **Behavior:** tools/call от агента A с `agent_id=A` — успех; с
  `agent_id=B` — отказ; без аутентификации — 401 ещё на входе в `/mcp`;
  действия агента пишутся в аудит от имени А.
- **Boundaries:** инструменты без `agent_id` в аргументах (profile, list);
  инструменты, требующие user-контекст (если есть); двойной вызов
  параллельно (контекст не «протекает» между запросами — проверка
  contextvar-изоляции).
- **Conditions:** auth enabled; agent active/revoked на входе; D5-режим
  (только ключ / dual-accept).
- **AC:** SPEC-0028 AC5 (spoofing-отказ), AC4 для `/mcp` (enumeration
  включает MCP-ручки).
- **Matrix:**
  - unit: сверка принципала vs аргумента (позитив/негатив/равенство);
    JSON-RPC error-shape.
  - integration: настоящий `POST /mcp` двумя агентами (A пытается быть
    B → отказ; A корректно → success); изоляция контекста между
    параллельными запросами.
  - negative-класс (прежний пропуск): «аутентифицированный, но чужой
    принципал» — покрыть ВСЕ инструменты, принимающие `agent_id`
    (параметризация по списку инструментов).

## Decomposition

| # | Item | Depends |
|---|---|---|
| 1 | Инвентаризация вызывающих `/mcp` + инструментов с `agent_id` (red-тесты spoofing) | 0170 |
| 2 | Провижининг принципала в dispatch + сверка `agent_id` | 1 |
| 3 | Session-fallback cleanup в mcp | 2 |
| 4 | Evidence: spoofing-матрица зелёная, полный прогон | 3 |
