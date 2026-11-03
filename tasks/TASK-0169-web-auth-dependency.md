# TASK-0169 — Web auth dependency (JWT): default-deny + retire AuthMiddleware

**Source:** SPEC-0028 §3.2 (S28.2); Dmitry 2026-11-02 («API веба ожидает
JWT… маркировать ручки встроенным решением FastAPI»)
**Milestone:** auth rework (SPEC-0028 batch)
**Spec:** SPEC-0028 §3.2, AC1/AC2/AC4(web)/AC10/AC11; SPEC-0029 S29.3/S29.5
**Points:** 8
**Status:** PENDING (реализация не начата)

## Context

Веб-API (16 роутеров под `/api/v1`) защищается строковым гардом
`AuthMiddleware` + `PUBLIC_PATHS`; `/auth/*` вне гарда и защищён только
`Depends(get_current_user)` по памяти автора ручки (default-ALLOW).
Задача переводит аутентификацию веба на `web_auth`-зависимость
(blanket на `include_router`), убивает хардкод и выравнивает
`get_current_user` на сервисы (SPEC-0029).

## Goals

1. `web_auth` async-зависимость: Bearer → `TokenService.verify` →
   denylist → `SubjectStateService` → `request.state.user_id` +
   `api_surface="web"`; синхронный I/O через `run_in_threadpool`
   (не блокирует event loop); 401-формы идентичны текущим
   (missing / invalid / denylisted / unknown|disabled subject).
2. Blanket `dependencies=[Depends(web_auth)]` для web-группы реестра;
   `/auth`-защищённые ручки — через `get_current_user`, переписанный на
   `SubjectStateService` (SPEC-0029 S29.5).
3. `AuthMiddleware` и `PUBLIC_PATHS` удаляются; миграция тестового
   харнесса (тесты делают `add_middleware(AuthMiddleware)` — сейчас их
   десятки: `test_auth_middleware_protection.py`,
   `test_logout_denylist.py`, `test_security_hardening.py`,
   `test_rbac_enforcement.py`, `test_dashboard_security.py`,
   `test_auth_middleware_user_check.py`).
4. **Перечислительный тест AC1**: обход ВСЕХ web-ручек без кредов → не 2xx
   (401), исключения — только члены `PUBLIC_ROUTERS`. Это пропущенный
   класс сценария (SPEC-0028 finding 9).
5. `disable_auth` (hermetic) сохраняется на время миграции харнесса;
   зафиксировать как test-only (AC10).

## Test design (совместная проработка до кода — SPEC-0028 §6 / D6)

- **Behavior:** неавторизованный запрос к любой web-ручке → 401 с
  прежним body/headers; валидный JWT → поведение не меняется.
- **Boundaries:** публичные ручки (login/setup/refresh/health/docs)
  НЕ получают зависимость; `/mcp` не трогаем (это TASK-0170/0171);
  методы без тела vs с телом; CORS-OPTIONS не проходит через auth.
- **Conditions:** auth enabled (default) и `disable_auth=true`
  (hermetic); Redis up/down (denylist fail-open — SPEC-0027 AC5
  сохраняется); denylist-попадание; субъект удалён/отключён (TTL-кеш 60с).
- **AC:** SPEC-0028 AC1 (enumeration!), AC2, AC10, AC11; SPEC-0027
  регресс-база (55 authz live, 0 xfail).
- **Matrix:**
  - unit: `web_auth` — позитив (валидный JWT→CurrentUser); негатив ×4
    (нет заголовка, кривой формат, протухший, denylisted); негатив ×2
    (unknown/disabled sub); граница: `Bearer` без токена, токен с
    кривым `sub`.
  - integration: enumeration-тест по `app.routes` (негатив-класс!);
    перехват логов → нет значений заголовков (AC11).
  - parity: старые auth-тесты мигрируют на харнесс и должны остаться
    зелёными без смены семантики (SPEC-0029 AC2).
- **Red-фаза:** enumeration-тест и 401-shape тесты написать ДО удаления
  middleware (на текущем коде должны быть green — это characterization;
  после удаления — остаются green на зависимостях).

## Decomposition

| # | Item | Depends |
|---|---|---|
| 1 | `web_auth` (тесты red→green) поверх сервисов SPEC-0029 | 0174, 0175 |
| 2 | Blanket-включение в реестре + `/auth` на сервисах | 1, 0168 |
| 3 | Миграция тестового харнесса (снятие `add_middleware`) | 2 |
| 4 | Удаление `AuthMiddleware`/`PUBLIC_PATHS` + enumeration-тест AC1 | 3 |
| 5 | Evidence: полный прогон + authz live suite | 4 |

## Risks

- Объём миграции тестов — основной риск по времени; семантика 401 не
  меняется, поэтому миграция механическая (сверка форм в первом же тесте).
