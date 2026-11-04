# TASK-0179 — Quality-gate fallout после SPEC-0028/0029 батча

**Source:** red quality:gate на develop (pipeline 536, job 4156) после
слияния MR !105 — первый запуск hard-gate на коде батча (MR-пайплайны
gate не запускают).
**Milestone:** auth rework (post-merge gate repair)
**Spec:** SPEC-0028 (§7/AC6/AC11 + D5 amendment) + SPEC-0029 AC1
**Points:** 4
**Status:** DONE (решение владельца + фиксы применены; gate-верификация —
зелёный develop-пайплайн)

## Context

Gate 536: `RCs: e2e=0 e2e_fe=1 chaos=0 security=1 perf=1`, fuzz 46/55.
До мержа !105 gate на develop был зелёный (pipeline 532).

## Items

| # | Кластер | Корень | Фикс |
|---|---------|--------|------|
| 1 | security authz ×2 | фикстуры чеканят agent-токены **без scopes** → FIX-1 дефолт `[]` → 403 (`/mcp/tools` требует `agent:mcp`, `/agent/me` — `agent:self`) | явные scopes в фикстурах (test-side) |
| 2 | fuzz auth_bypass ×9 | D2-семантика: auth = route-dependency → фантомные пути (`audit/logs`, `tasks`, `dashboard`) → 404, несуществующие методы → 405, `/mcp` → 307 **до** auth; раньше AuthMiddleware отвечал 401 pre-routing | реальные пути в NO_AUTH_GET; для method-tricks принять отказ `401\|405` (оба ≠ успех; `/openapi.json` и так публичен → утечки нет) |
| 3 | perf scenario_mixed ×25 | locust `_ensure_agent_token` mint без scopes → 403 на `agent:self`/`agent:workflow` роутах — **ровно TASK-0178 item 5** (product-impact FIX-1) | scopes `["agent:self","agent:workflow"]` при монтировании |
| 4 | e2e_fe ×2 (3.2/3.4) | **продуктовая регрессия D5**: workflow-чтения (claims/heartbeats/clarifications) и answer/release используются UI с JWT, но отнесены к agent-surface → 401 → refresh-каскад (`addInitScript` перезаписывает localStorage старыми cached-токенами при каждой навигации → ротированный refresh 401 → `clearTokens` → redirect `/login`) → вкладка исчезает → `locator.click` 5-мин таймаут | **Решение владельца (Dmitry, 2026-11-04): split, минимальный** — только 3 GET-чтения → web surface (`workflow_read_router` + registry WEB); writes (claim/release/heartbeat/progress/create/answer) остаются agent-only. D5 amendment в спеке. Отклонение от первоначального option-текста («+ answer + release»): факты показали, что answer/release требуют agent identity в домене (`get_current_agent`, `claim.agent_id == agent_id`) и **не работали с JWT и до батча** (UI не шлёт X-Agent-Token никогда) — это не регрессия и не блокер gate |

## Item 4 — факты для решения

UI-потребители workflow-роутов (grep по `frontend/src`, потребители вне
`lib/api/tasks`):

- `GET /tasks/{id}/claims`, `GET /tasks/{id}/heartbeats`,
  `GET /tasks/{id}/clarifications` — Execution tab (`use-task-execution`)
- `POST /clarifications/{id}/answer` — ClarificationsTab
- `POST /tasks/{id}/release` — `use-task-detail`, `use-task-execution`

UI **не** использует: `claim`, `heartbeat`, `progress`,
`create-clarification`, `agent/me|inbox|playbook` (в `tasks.ts` — мёртвый
код без потребителей).

Другие HTTP-потребители: locust (claim/heartbeat/release/agent-* — шлёт
**оба** заголовка: `auth_headers()` включает и JWT, и X-Agent-Token),
будущие REST-агенты (только ключ; «агенты в будущем не только через MCP»).

До батча: AuthMiddleware принимал JWT на всех `/api/v1/*` — UI работал.
После: D5 → workflow = agent-key-only → UI сломан (регрессия, поймана
e2e gate).

## Test design

- **Item 1:** red в gate (authz 2 failed) → фикстуры со scopes → green;
  negative: токен без scope всё ещё 403 (покрыто в
  `test_agent_surface_auth`).
- **Item 2:** red в gate (fuzz 9 failed) → реальные пути дают строгий
  401; method-tricks: `401|405`, никогда 2xx/5xx; `/mcp/` (slash) → 401.
  Прогнать fuzz unit (`test_fuzz_unit`) локально.
- **Item 3:** red в gate (perf RC=1, failures.csv 403) → scopes →
  locust smoke против test-stack.
- **Item 4:** спека-решение → по нему red→green e2e; ручной прогон
  frontend suite в gate.

## Decomposition

| # | Item | Depends |
|---|------|---------|
| 1 | authz-fикстуры scopes | — |
| 2 | fuzz-expectations под D2 | — |
| 3 | locust scopes (TASK-0178 item 5) | — |
| 4 | workflow surface решение + фикс | владелец (D5 amendment) ✅ решено 2026-11-04 |

## Evidence (2026-11-04)

- Gate job 4156 artifacts: `authz_*json` (2 FAIL403 scope),
  `fuzz_*json` (9 FAIL 404/405/307), `smoke_*_failures.csv`
  (`LocustBadStatusCode(code=403)` ×25), playwright `Test timeout of
  300000ms exceeded` + `401 .../claims|heartbeats` + `401 /auth/refresh`.
- Item 4 решение: AskUserQuestion → «Разделить по UI/агент» → уточнение
  «только чтения» (минимальный). Реализация: `workflow_read_router`,
  registry WEB-группа, пины `test_api_surface_registry`
  (reads=web/writes=agent) + `test_agent_surface_auth`
  (web JWT → 404 ≠ 401 через production composition).
- Локальные гейты: backend **1568 passed** (coverage 91.44%),
  ruff/format/mypy clean, fuzz unit 12 passed.

## Follow-ups (не блокеры)

- **UI-кнопки release/answer не работают с JWT** — истинное поведение и до
  батча (handler-level `get_current_agent` требует X-Agent-Token; UI его
  никогда не шлёт). Нужен доменный дизайн: force-release c RBAC? или
  `answered_by=user_id`? — отдельная задача после develop→main релиза.
