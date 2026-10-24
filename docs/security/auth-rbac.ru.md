# Аутентификация и RBAC — UPCP v2

[EN](auth-rbac.md) | **RU**

> Область: `auth` | Владелец: security-team | Версия: 3.0.0
> Переписано 2026-10-24 по фактическому коду (SPEC-0027 §3.4, находки 4-5).
> Каждый путь ниже проверен контрактным тестом против OpenAPI-схемы
> (`backend/tests/test_public_paths.py`).

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

- JWT access-токены + вращаемые refresh-токены.
- `AuthMiddleware` аутентифицирует каждый запрос `/api/v1/*` и `/mcp/*`,
  кроме `PUBLIC_PATHS`; маршруты `/auth/*` полагаются на dependency
  `get_current_user`.
- `PUBLIC_PATHS`: `/health`, `/api/v1/health`, `/auth/setup`,
  `/auth/login`, `/auth/refresh`, `/docs`, `/redoc`, `/openapi.json` —
  каждый пункт регрессионно проверен на наличие зарегистрированного
  маршрута (мёртвая запись `/mcp/health` удалена в TASK-0148).
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

Денайлист проверяется в `AuthMiddleware` (доменные маршруты) и в
`get_current_user` (`/auth/*`): денайлистнутый access-токен получает
**401** с `WWW-Authenticate` — ту же форму, что и невалидный токен
(`action=auth.token_denied`, метрика `upcp_auth_token_denials_total`).

**Деградация Redis:** если Redis недоступен, чтение деградирует
**fail-open** — запрос разрешается, пишется структуированное
предупреждение. Tradeoff: доступность поверх окна отзыва максимум
15 минут (SPEC-0027 AC5). Запись деградирует тем же образом; отзыв
refresh в БД не затрагивается.

Кроме того, после проверки подписи middleware проверяет, что subject
**существует и активен** (кэш `auth:user:{sub}`, 60 с) — неизвестный или
отключённый subject получает 401 даже при валидной подписи.

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

Семантика гейта (fail-closed, по порядку):

1. `UPCP_DISABLE_AUTH=true` → гейты инертны (hermetic-режим; middleware
   тогда вообще не монтируется);
2. нет identity → **401**;
3. неизвестный или неактивный subject → **401**;
4. `is_superuser=True` → bypass (покрывает владельца `/auth/setup` и
   seeder-админов без миграции данных);
5. нет подходящего права роли → **403** (структурированный лог +
   `upcp_rbac_denials_total`).

Разрешение прав кэшируется в Redis (`rbac:user_perms:{user_id}`, TTL 60 с).
Phase B (per-CRUD гейты для structure/delivery/quality, scoped-биндинги
org/project) — backlog: колонки scoped-биндингов есть, но ещё не
разрешаются.

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
- **Phase B гейты** (CRUD structure/delivery/quality, scoped-биндинги)
  ещё не enforced.

## Связанные документы

- [Rate Limiting](rate-limiting.md)
- [Secrets Handling](secrets-handling.md)
- [Threat Model](threat-model.md)
- [Agent Permissions](agent-permissions.md)
- [Индекс документации](../INDEX.md)
