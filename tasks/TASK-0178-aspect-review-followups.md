# TASK-0178 — Aspect-review follow-ups (SPEC-0028/0029 batch)

**Source:** aspect-review ветки `feature/TASK-0168-api-surface-registry`
(независимый read-only агент, 2026-11-04) — находки, согласованные как
«зафиксировать задачей до done» (AC/medium-low) вместо правок в батче.
**Milestone:** auth rework (SPEC-0028/0029 batch, post-review)
**Spec:** SPEC-0029 AC1 (amended scope) + SPEC-0028 §7/AC4/AC11 leftovers
**Points:** 5
**Status:** PENDING (реализация не начата)

## Context

Основной aspect-review пачки дал вердикт «merge after fixing high» —
фиксы #1/#2/#3/#6/#8/#9/#10/#12 вошли отдельным коммитом
`fix(review): …`. Ниже — находки, которые по соглашению закрываются
задачей (DoD §12: medium/low — фикс или задача).

## Items

| # | Sev | Находка | Суть |
|---|-----|---------|------|
| 1 | medium | SPEC-0029 AC1 ↔ scanner scope | Контракт `test_identity_layering_contract.py` сканирует 3 файла hot-path; `db.query` остаётся в `token_service.py`, `agent_endpoints.py`, `seed.py`. AC1 переформулирован (scoped) — здесь: расширить сканер на весь `identity/` с baseline-исключениями и снять исключения по мере выноса. |
| 2 | medium | `denylist.py` вне cache-provider | `identity/denylist.py:34,47` импортирует `app.shared.redis` напрямую (baseline-запись с владельцем `TASK-0174` — уже DONE → передать владельцу `backlog`). Перенос на `AuthCacheProvider` НЕ тривиален: провайдер никогда не бросает → denylist теряет различение «outage vs miss» для своего `action=auth.denylist_unavailable`-лога (caplog-контракт) — нужен явный дизайн (напр., провайдер-вариант с `ok`-флагом или перенос лога с сохранением контракта). |
| 3 | medium | RBAC: `db.get(User, …)` в presentation | `identity/permissions.py:146` — гейт читает юзера напрямую (дедуп-контракт его не ловит: scanner-список). Через `SubjectStateService`/репозиторий + кеш — убирает DB-read на каждую гейт-мутацию и закрывает D1 полностью. |
| 4 | low | MCP: sync SQLAlchemy на event loop | `mcp/tools.py:882,899` — `async def call_tool` вызывает sync-хендлер инлайново (pre-existing, но это agent hot path, переработанный пачкой). `await run_in_threadpool(handler, sess, arguments)` + замер. |
| 5 | — | FIX-1 product-impact | Уточнено по отчёту фикс-агента 2026-11-04: `tests/performance/locustfiles/common.py:127` создаёт ключ **без `scopes`** → после FIX-1 (дефолт `[]`) locust-флоу на scope-гейтованных ручках (MCP/workflow) получат 403 — фикстуре нужны явные scopes. Frontend: token-issuance вызова в `frontend/src` НЕТ вовсе (UI «Generate Token → select scope» не реализован) — при появлении фичи обязателен выбор scopes. `docs/agent/agent-onboarding.md` уже шлёт scopes ✓. |

## Test design (перед реализацией — SPEC-0028 §6/D6)

- **Behavior:** каждый пункт — поведение/границы/условия/AC/матрицу
  до кода (red→green).
- **Границы:** пункты 1-3 не должны менять внешнее поведение
  (паритет-сьюты зелёные); пункт 4 — поведение инструментов не меняется
  (только планировщик).
- **AC:** расширенный сканер ловит синтетический `db.query` в новом
  модуле identity (mutation); denylist-parity: outage → allow + warning
  с прежним `action`; RBAC-gate: кеш-спай (повторный гейт без DB);
  MCP: инструменты отвечают идентично после threadpool.

## Decomposition

| # | Item | Depends |
|---|------|---------|
| 1 | Сканер db.query на весь identity + baseline | — |
| 2 | Denylist → cache provider (с сохранением лог-контракта) | 1 |
| 3 | RBAC subject → сервис/репозиторий + кеш | — |
| 4 | MCP tools → run_in_threadpool + замер | — |
| 5 | FIX-1 callers ↔ UI scopes-флоу | отчёт фикс-агента |
