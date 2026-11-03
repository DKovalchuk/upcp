# TASK-0172 — RBAC coverage: require_permission на все опасные мутации + require_role

**Source:** SPEC-0028 §3.5 (S28.5), решение D4 (Dmitry 2026-11-02:
«расширить require_permission»)
**Milestone:** auth rework (SPEC-0028 batch)
**Spec:** SPEC-0028 §3.5, AC8; SPEC-0027 §3.1 (Phase A закрыта, Phase B — здесь)
**Points:** 5
**Status:** PENDING (реализация не начата)

## Context

`require_permission` (SPEC-0027, TASK-0145) покрывает только Phase A:
CRUD проектов и управление агентами. Остальные опасные мутации
(delivery/quality/structure/delete-операции, notification-channels,
gitread-мутации) — «any-authenticated». Гейт читает
`request.state.user_id` из middleware — после TASK-0169 источник
принципала меняется на web_auth-зависимость.

## Goals

1. Инвентарь мутаций (POST/PATCH/DELETE всех web-роутеров) → таблица
   `action:resource` per route; расставить `require_permission` на
   опасные операции (минимум: delete-мутации всех контекстов,
   create/update структуры/quality-гейтов).
2. Добавить `require_role(role)` / `require_superuser()` для
   admin-only операций (роль как семантика, не пара permission).
3. Гейты читают принципал из нового контекста (web_auth); кеш пар
   прав через `AuthCacheProvider` (SPEC-0029 S29.5) — инлайн-Redis в
   `permissions.py` уходит.
4. Обратная совместимость: порядок fail-closed-проверок и superuser
   bypass не меняются (SPEC-0027 §3.1 amendment); reads не получают
   новых гейтов без явного решения.

## Test design (совместная проработка до кода — SPEC-0028 §6 / D6)

- **Behavior:** мутация без права → 403 (не 404/500); с правом → 2xx;
  superuser → всегда; роль-gate: не та роль → 403.
- **Boundaries:** право есть, но пользователь disabled (→ 401, не 403 —
  существующий порядок); гейт при `disable_auth` (инертен — hermetic);
  супербьюзер без RoleBinding (существующий AC9-кейс не должен упасть).
- **Conditions:** Redis up/down (кеш пар → фолбэк в БД — SPEC-0029 AC3);
  пары прав закешированы до выдачи нового права (TTL 60с — негативный
  кейс: после grant запрос в течение TTL может 403 — зафиксировать
  поведение документацией, как сейчас).
- **AC:** SPEC-0028 AC8; регресс SPEC-0027 AC1/AC2/AC9.
- **Matrix:**
  - unit: каждый новый гейт — позитив (право есть) / негатив (нет
    права → 403) / негатив (нет принципала → 401) / граница
    (superuser, disabled-юзер); `require_role` — 4 ручных кейса.
  - integration: параметризация по таблице инвентаря — «мутация X без
    права → 403» для КАЖДОЙ покрытой ручки (не одна выборочная).
  - regression: ungated reads baseline (SPEC-0027 AC2) — статусы не
    изменились.
- **Red-фаза:** на каждый новый гейт — сначала тест «без права → 403»
  (падает до расстановки Depends), затем green.

## Decomposition

| # | Item | Depends |
|---|---|---|
| 1 | Инвентарь мутаций + таблица прав (в файл задачи) | 0169 |
| 2 | Расстановка require_permission + require_role/red→green по таблице | 1, 0175 |
| 3 | Кеш пар через AuthCacheProvider | 0174 |
| 4 | Regression: полный прогон + authz live suite | 2-3 |
