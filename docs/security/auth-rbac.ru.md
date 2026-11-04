# Аутентификация и RBAC — UPCP v2

[EN](auth-rbac.md) | **RU**

> Область: `auth` | Владелец: security-team | Версия: 3.2.0
> Переписано 2026-10-24 по фактическому коду (SPEC-0027 §3.4, находки 4-5);
> auth переведён на dependency-гарды поверхностей 2026-11-04
> (SPEC-0028, TASK-0169/TASK-0170); таблица Phase-B гейтов добавлена
> 2026-11-04 (TASK-0172).
> Каждый путь ниже проверен контрактным тестом против OpenAPI-схемы
> (`backend/tests/test_auth_docs_contract.py`).

## Содержание

- [1. Обзор](#1-обзор)
- [2. Токены](#2-токены)
- [3. Эндпоинты](#3-эндпоинты)
- [4. Денайлист logout](#4-денайлист-logout)
- [5. Смена пароля](#5-смена-пароля)
- [6. RBAC](#6-rbac)
- [7. Лимиты скорости и блокировки](#7-лимиты-скорости-и-блокировки)
- [8. Известные ограничения](#8-известные-ограничения)
- [Связанные документы](#связанные-документы)

## 1. Обзор

- JWT access-токены + вращаемые refresh-токены для пользователей;
  статические API-ключи для агентской поверхности (см.
  [Agent API key](#23-agent-api-key-x-agent-token)).
- Аутентификация реализована FastAPI route-dependencies, а не
  middleware (SPEC-0028 D2). Реестр поверхностей
  (`app/api/registry.py`) вешает default-deny blanket на каждую
  поверхность: `web_auth` (Bearer JWT) — на все веб-маршруты под
  `/api/v1` и `/auth`, `agent_auth` (`X-Agent-Token`) — на агентские
  маршруты (agent self-service, claims/heartbeats workflow, всё под
  `/mcp`). Публичные маршруты (`/auth/setup`, `/auth/login`,
  `/auth/refresh`, `/health`, `/api/v1/health`, `/metrics`, docs)
  объявлены публичными в реестре — runtime-словаря путей больше нет
  (`AuthMiddleware`/`PUBLIC_PATHS` удалены в TASK-0170). Покрытие:
  `backend/tests/test_api_surface_registry.py` (классификация) и
  `backend/tests/test_auth_enumeration.py` (каждый web/agent-маршрут
  отвечает 401 без кредов).
- Агентские маршруты дополнительно проверяют scopes ключа (AC6 — см.
  [Agent API key](#23-agent-api-key-x-agent-token)).
- Авторизация: гейты уровня маршрута `require_permission(action, resource)`
  (см. [RBAC](#6-rbac)); незагейтнутые чтения требуют любого
  аутентифицированного пользователя.

## 2. Токены

### 2.1 Access-токен

- Формат: JWT (HS256, симметричный ключ из `UPCP_SECRET_KEY`).
- TTL: 15 минут.
- Claims: `sub`, `type`, `iat`, `exp`.
  **Нет claim `jti` и нет вшитых roles/scopes** — права разрешаются на
  каждый запрос из БД (кэш в Redis, 60 с).
- Хранение: только память клиента (не localStorage).

```json
{
  "sub": "9646cb69-24c3-456e-b128-6f7ac2c1140c",
  "type": "access",
  "iat": 1761334440,
  "exp": 1761335340
}
```

### 2.2 Refresh-токен

- Формат: непрозрачная случайная строка, хранится **хэшем** (SHA-256) в
  БД; TTL 7 дней.
- Возвращается **в теле JSON-ответа** (поле `refresh_token`) — сервер не
  ставит httpOnly-cookie.
- Вращение: `POST /auth/refresh` выдаёт новую пару и отзывает
  использованный refresh-токен; повторное использование отозванного
  токена → 401.
- Ревокация «цепочки» (token family) при повторном использовании
  **не реализована** — см. [Известные ограничения](#8-известные-ограничения).

### 2.3 Agent API key (`X-Agent-Token`)

- Транспорт: статический API-ключ в заголовке `X-Agent-Token`, действует
  на всей агентской поверхности (agent self-service, workflow, `/mcp`).
  Веб-JWT там отклоняется с 401 — `/mcp` обслуживается только
  агентскими ключами (SPEC-0028 D5, инвентарь вызывающих в TASK-0170).
- Хранение: SHA-256-хэш; plaintext возвращается ровно один раз в ответе
  выпускающего эндпоинта.
- Выпуск: каждый новый ключ обязан получить `expires_at` — TTL по
  умолчанию **90 дней** (`UPCP_AGENT_TOKEN_TTL_DAYS`); явный
  `expires_at` должен быть в будущем (иначе 422). Ключи, выпущенные до
  TASK-0170, могут иметь `expires_at=NULL` и действуют до отзыва
  (grandfathered).
- Отзыв: мгновенный (`revoked_at`) — протухший или отозванный ключ
  падает на самом следующем запросе с 401 (`Agent token has expired` /
  `Agent token has been revoked`).
- Scopes (AC6): список `scopes` ключа гейтит поверхность —
  `agent:self` (профиль, inbox, playbook), `agent:workflow` (claims,
  heartbeats, progress, clarifications) и `agent:mcp` (всё под `/mcp`).
  Ключу не хватает нужного scope → **403** `{"detail": "Insufficient scope"}`
  (метрика `upcp_agent_scope_denials_total`, span-атрибут
  `upcp.auth.scope_denied`). Legacy-ключи с `scopes=null` проходят все
  scope-гейты до переиздания (grandfathered).
- Hermetic-тестовый режим (`UPCP_DISABLE_AUTH=true`, только тесты):
  surface-blankets и scope-гейты отключаются — как и middleware при
  выключенном флаге (AC10).
- Эндпоинт выпуска: `POST /api/v1/agents/{agent_id}/tokens`.

## 3. Эндпоинты

Префикс монтирования `/auth` (не `/api/v1/auth`):

| Эндпоинт | Назначение | Примечания |
|----------|-----------|------------|
| `POST /auth/setup` | Создание первого владельца | 201; **409**, если пользователи уже есть |
| `POST /auth/login` | Логин → пара токенов | 200 / 401 / 423 (блокировка) / 429 (лимит) |
| `POST /auth/logout` | Отзыв refresh + денайлист access | Требуется Bearer |
| `POST /auth/refresh` | Вращение refresh-токена | 200 / 401 |
| `GET /auth/me` | Профиль текущего пользователя | 401 без живого токена |
| `POST /auth/password/change` | Смена пароля | 400 неверный текущий / 422 слабый |

Сервисные эндпоинты (публичные): `GET /health`, `GET /api/v1/health`,
`GET /metrics`.

Сброс пароля по email (`/auth/password/reset/*`) **не реализован** —
прежний документ описывал несуществующие эндпоинты.

## 4. Денайлист logout

`POST /auth/logout` делает две вещи:

1. отзывает предъявленный refresh-токен;
2. пишет в Redis `auth:deny:{sha256(access_token)}` с TTL
   `exp − now` (самоистекающий, без cleanup-джобы).

Денайлист проверяется в dependency `web_auth` (веб-маршруты) и в
`get_current_user` (`/auth/*`): денайлистнутый access-токен получает
**401** с `WWW-Authenticate` — ту же форму, что и невалидный токен
(`action=auth.token_denied`, метрика `upcp_auth_token_denials_total`).

**Деградация Redis:** если Redis недоступен, чтение деградирует
**fail-open** — запрос разрешается, пишется структуированное
предупреждение. Tradeoff: доступность поверх окна отзыва максимум
15 минут (SPEC-0027 AC5). Запись деградирует тем же образом; отзыв
refresh в БД не затрагивается.

Кроме того, после проверки подписи dependency `web_auth` проверяет, что
subject **существует и активен** (кэш `auth:user:{sub}`, 60 с) —
неизвестный или отключённый subject получает 401 даже при валидной
подписи.

## 5. Смена пароля

`POST /auth/password/change` требует текущий пароль:

- при успехе **все refresh-токены пользователя отзываются** в одной
  транзакции (реализовано в TASK-0148 — документ обещал это раньше, чем
  код выполнял);
- access-токены других сессий остаются действительными до `exp`
  (≤ 15 мин) — см. [Известные ограничения](#8-известные-ограничения);
- неверный текущий пароль → 400; новый пароль короче 8 символов → 422.

## 6. RBAC

Роли в сиде: `Owner`, `Admin`, `Member`, `Viewer`, с каталогом прав
(`Permission` / `RolePermission` / `RoleBinding`).

Runtime-гард — FastAPI dependency:

```python
from fastapi import Depends
from app.identity.permissions import require_permission

@router.post(
    "/projects",
    dependencies=[Depends(require_permission("create", "project"))],
)
def create_project(...) -> ...: ...
```

Enforced сегодня (Phase A — опасные админ-мутации):

- `POST /api/v1/projects` → `create:project`
- `PATCH /api/v1/projects/{project_id}` → `update:project`
- `DELETE /api/v1/projects/{project_id}` → `delete:project`
- мутации управления агентами (`POST /api/v1/agents`, выпуск и отзыв
  токенов под `/api/v1/agents/{agent_id}`) → `manage:agent`

Phase B (TASK-0172) — каждая опасная мутация веб-поверхности
(инвентарь по роутам и обоснования «без гейта»:
`tasks/TASK-0172-rbac-coverage.md`):

| Эндпоинт | Право |
|----------|-------|
| `POST /api/v1/projects/{project_id}/components` | `create:component` |
| `PATCH /api/v1/components/{component_id}` | `update:component` |
| `DELETE /api/v1/components/{component_id}` | `delete:component` |
| `POST /api/v1/components/{component_id}/modules` | `create:module` |
| `PATCH /api/v1/modules/{module_id}` | `update:module` |
| `DELETE /api/v1/modules/{module_id}` | `delete:module` |
| `DELETE /api/v1/features/{feature_id}` | `delete:feature` |
| `PATCH /api/v1/tasks/bulk` | `update:task` |
| `DELETE /api/v1/tasks/{task_id}` | `delete:task` |
| `DELETE /api/v1/subtasks/{subtask_id}` | `delete:subtask` |
| `POST /api/v1/tasks/{task_id}/acceptance-criteria` | `create:acceptance_criteria` |
| `PATCH`/`DELETE /api/v1/acceptance-criteria/{ac_id}` | `update`/`delete:acceptance_criteria` |
| `POST /api/v1/tasks/{task_id}/dod-items` | `create:dod_item` |
| `PATCH`/`DELETE /api/v1/dod-items/{item_id}` | `update`/`delete:dod_item` |
| `POST /api/v1/tasks/{task_id}/complete` | `update:task` |
| `POST /api/v1/tasks/{task_id}/submit-review`, `POST /api/v1/tasks/{task_id}/review-rounds` | `create:review_round` |
| `POST /api/v1/review-rounds/{round_id}/start`, `POST /api/v1/review-rounds/{round_id}/verdict` | `update:review_round` |
| `POST /api/v1/review-rounds/{round_id}/findings` | `create:review_finding` |
| `POST /api/v1/tasks/{task_id}/evidence`, `POST /api/v1/tasks/{task_id}/evidence/upload` | `create:evidence` |
| `POST /api/v1/evidence/{evidence_id}/agent-verify`, `/human-accept`, `/reject` | `update:evidence` |
| `POST /api/v1/notification-channels` | `create:notification_channel` |
| `PATCH /api/v1/notification-channels/{channel_id}` | `update:notification_channel` |
| `DELETE /api/v1/notification-channels/{channel_id}` | `delete:notification_channel` |
| `POST /api/v1/notification-channels/{channel_id}/toggle`, `/test` | `update:notification_channel` |
| `POST /api/v1/projects/{project_id}/git-providers` | `create:git_provider` |
| `PATCH`/`DELETE /api/v1/git-providers/{provider_id}` | `update`/`delete:git_provider` |
| `DELETE /api/v1/git-links/{link_id}` | `delete:git_link` |
| `POST /api/v1/internal/reaper/tick` | только супербьюзер — `require_superuser()` → 403 `{"detail": "Superuser required"}` |

Доступен также `require_role(role)` → 403 `{"detail": "Insufficient role"}`
(супербьюзеры проходят, как и в permission-гейте). Ни один прод-роут
пока не является role-семантическим — фабрика готова к первому такому
(таблица решений в `tasks/TASK-0172-rbac-coverage.md`).

Сознательно без гейтов (any-authenticated, база SPEC-0027 AC2): все
чтения; рутинные единичные create/update рабочих элементов delivery
(feature/task/subtask/comment); состояние прочтения уведомлений
(`mark-read`); генерация/суммаризация отчётов; `POST /api/v1/git-links`.
Мутации агентского workflow (claims/heartbeats/clarifications) живут на
агентской поверхности и гейтятся scope'ами API-ключа (AC6).

Семантика гейта (fail-closed, по порядку):

1. `UPCP_DISABLE_AUTH=true` → гейты инертны (hermetic-режим —
   surface-dependencies отключаются так же);
2. нет identity → **401**;
3. неизвестный или неактивный subject → **401**;
4. `is_superuser=True` → bypass (покрывает владельца `/auth/setup` и
   seeder-админов без миграции данных);
5. нет подходящего права роли → **403** (структурированный лог +
   `upcp_rbac_denials_total`).

`require_role`/`require_superuser` идут в том же порядке; их отказы —
**403** `{"detail": "Insufficient role"}` / `{"detail": "Superuser
required"}` (метрика `upcp_rbac_denials_total` с labels
`action=role`/`action=superuser`).

Разрешение прав кэшируется в Redis (`rbac:user_perms:{user_id}`, TTL 60 с).
Per-CRUD гейты опасных мутаций enforced (Phase B, TASK-0172 — таблица
выше). В backlog: scoped-биндинги org/project (колонки есть, ещё не
разрешаются) и прод-использование `require_role`.

## 7. Лимиты скорости и блокировки

- `POST /auth/login`: 5 попыток в минуту на IP → **429** с `retry_after`
  (см. [Rate Limiting](rate-limiting.md)).
- 5 неудачных попыток → блокировка аккаунта на **30 минут** → **423**.
- Действия аудита в `login_audit`: `login_success`, `login_failed`,
  `account_locked`, `logout`, `password_change`.

## 8. Известные ограничения

- **Access-токены переживают logout/смену пароля до `exp`** (≤ 15 мин)
  для сессий, отличивших от выполнившей запрос, — нет claim `jti`,
  поэтому один токен нельзя убить раньше.
- **Детекция повторного использования refresh останавливается на
  отклонении** (401); замещающая цепочка не отзывается целиком (нет
  таблицы token-family).
- **Сброс пароля по email отсутствует.**
- **Scoped-биндинги ещё не разрешаются** (колонки `RoleBinding.org_id`/
  `project_id` есть, каждый биндинг резолвится глобально). Рутинные
  единичные create/update рабочих элементов delivery, состояние
  прочтения уведомлений и мутации отчётов остаются any-authenticated
  по решению (инвентарь TASK-0172).

## Связанные документы

- [Rate Limiting](rate-limiting.md)
- [Secrets Handling](secrets-handling.md)
- [Threat Model](threat-model.md)
- [Agent Permissions](agent-permissions.md)
- [Индекс документации](../INDEX.md)
