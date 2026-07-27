# Аутентификация и RBAC — UPCP v2

> Область: `auth` | Владелец: security-team | Версия: 2.0.0

## 1. Обзор

UPCP использует JWT access tokens + rotating refresh tokens для аутентификации.
RBAC реализован на трёх уровнях: global, organization, project.

## 2. Токены

### 2.1 Access Token

- Формат: JWT (RS256)
- TTL: 15 минут
- Claims: `sub`, `roles`, `scopes`, `iat`, `exp`, `jti`
- Хранение: только в памяти клиента (не localStorage)

```json
{
  "sub": "usr_a1b2c3",
  "roles": ["org:admin", "proj:member"],
  "scopes": ["projects:read", "tasks:write"],
  "iat": 1721980800,
  "exp": 1721981700,
  "jti": "tok_x1y2z3"
}
```

### 2.2 Refresh Token

- Формат: opaque rotating token
- TTL: 7 дней
- Rotation: каждый refresh инвалидирует предыдущий токен и выдаёт новую пару
- Хранение: httpOnly, Secure, SameSite=Strict cookie
- Reuse detection: если использован уже инвалидированный refresh token — отзывается вся цепочка

### 2.3 Token Lifecycle

```
Login → (access + refresh)
  ↓ (15 min)
Refresh → (new access + new refresh, старый refresh инвалидирован)
  ↓ (7 days max)
Re-login required
```

## 3. Аутентификация

### 3.1 First-Run Setup

```
POST /api/v1/auth/setup
```

- Вызывается только когда в системе нет ни одного пользователя
- Создаёт первого Owner глобального уровня
- Требует: `email`, `password`, `display_name`
- После создания первого пользователя эндпоинт возвращает `410 Gone`

### 3.2 Login

```
POST /api/v1/auth/login
Body: { "email": "...", "password": "..." }
Response: { "access_token": "...", "refresh_token": "...", "expires_in": 900 }
```

- Rate limit: 5 попыток/мин/IP, блокировка на 15 мин после 5 неудачных
- Логирует: `auth.login.success` / `auth.login.failed`
- Запрещён для деактивированных аккаунтов

### 3.3 Logout

```
POST /api/v1/auth/logout
Authorization: Bearer <access_token>
```

- Инвалидирует текущий refresh token
- Логирует: `auth.logout`

### 3.4 Password Change

```
POST /api/v1/auth/password/change
Body: { "current_password": "...", "new_password": "..." }
```

- Требует текущий пароль
- Инвалидирует все refresh tokens пользователя
- Логирует: `auth.password.changed`

### 3.5 Password Reset

```
POST /api/v1/auth/password/reset/request   — отправка email
POST /api/v1/auth/password/reset/confirm   — сброс по токену
```

- Токен сброса: одноразовый, TTL 1 час
- Rate limit: 3 запроса/час/email

## 4. RBAC

### 4.1 Уровни (Scopes)

| Уровень         | Описание                     | Контекст          |
|----------------|------------------------------|-------------------|
| `global`        | Глобальные права админа      | Вся система       |
| `organization`  | Права в рамках организации   | `org_{id}`        |
| `project`       | Права в рамках проекта       | `proj_{id}`       |

### 4.2 Роли

| Роль       | Описание                                      |
|-----------|----------------------------------------------|
| `Owner`    | Полный контроль, включая удаление            |
| `Admin`    | Управление участниками, настройками           |
| `Member`   | Работа с задачами, агентами, файлами          |
| `Viewer`   | Только чтение                                 |

### 4.3 Матрица разрешений

| Действие                          | Owner | Admin | Member | Viewer |
|-----------------------------------|:-----:|:-----:|:------:|:------:|
| Просмотр проектов                | ✅    | ✅    | ✅     | ✅     |
| Создание/редактирование задач    | ✅    | ✅    | ✅     | ❌     |
| Управление агентами              | ✅    | ✅    | ✅     | ❌     |
| Просмотр аудита                  | ✅    | ✅    | ❌     | ❌     |
| Управление участниками           | ✅    | ✅    | ❌     | ❌     |
| Настройки проекта                | ✅    | ✅    | ❌     | ❌     |
| Удаление проекта                 | ✅    | ❌    | ❌     | ❌     |
| Управление организацией          | ✅    | ❌    | ❌     | ❌     |
| Глобальные настройки             | ✅*   | ❌    | ❌     | ❌     |

\* Только для глобального Owner

### 4.4 Разрешение доступа

1. Проверка аутентификации (валидный access token)
2. Определение контекста (global/org/project)
3. Проверка роли в контексте
4. Проверка конкретного разрешения для роли
5. Если нет разрешения → `403 Forbidden`

### 4.5 Наследование

```
global:Owner → все права на всё
global:Admin → управление организациями (не удаление)
org:Owner → все права в организации
org:Admin → управление участниками организации
proj:Owner → все права в проекте
proj:Member → CRUD задач, работа с агентами
proj:Viewer → только чтение
```

Права не наследуются автоматически между уровнями.
Owner организации не имеет прав в проектах, где не добавлен.

## 5. Безопасность

- Пароли: bcrypt, min 12 символов
- JWT подпись: RS256, ключи хранятся в SecretProvider
- Refresh tokens хранятся в БД с хешем (не plaintext)
- Все эндпоинты аутентификации — HTTPS only
- Account lockout: 5 неудачных попыток → блокировка 15 мин
- Отзыв всех токенов при смене пароля / деактивации
