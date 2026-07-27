# API Design — UPCP v2

## Обзор

UPCP предоставляет REST API для Web UI и внешних интеграций, а также MCP tools для ИИ-агентов. Документ описывает конвенции REST API.

---

## Базовый URL и версионирование

```
https://{host}/api/v1/{resource}
```

- Версия в URL: `/api/v1`
- При breaking change — новая версия `/api/v2`, старая поддерживается минимум 6 месяцев
- MCP tools не версионируются (версия = версия сервера)

---

## HTTP-методы

| Метод | Назначение | Idempotent | Тело ответа |
|-------|-----------|------------|-------------|
| `GET` | Чтение ресурса/коллекции | Да | Ресурс или массив |
| `POST` | Создание ресурса | Нет* | Созданный ресурс |
| `PUT` | Полная замена | Да | Обновлённый ресурс |
| `PATCH` | Частичное обновление | Да | Обновлённый ресурс |
| `DELETE` | Удаление (soft) | Да | `204 No Content` |

*POST идемпотентен при наличии `Idempotency-Key` заголовка.

---

## Именование ресурсов

```
/api/v1/projects                           # коллекция
/api/v1/projects/{project_id}              # конкретный ресурс
/api/v1/projects/{project_id}/tasks        # вложенная коллекция
/api/v1/projects/{project_id}/tasks/{task_id}
```

**Правила:**
- Имена в kebab-case: `review-rounds`, `acceptance-criteria`
- Множественное число для коллекций
- UUID v7 в качестве идентификаторов
- Вложенность максимум 2 уровня

---

## Аутентификация

### Web API (JWT)

```http
Authorization: Bearer eyJhbGciOiJSUzI1NiIs...
```

- Access token: 15 минут
- Refresh token: 7 дней (хранится в httpOnly cookie)
- Ротация refresh token при каждом использовании

### Agent API (MCP Token)

```http
Authorization: Bearer mcp_{token_prefix}_{random}
```

- Токен привязан к Agent + scope
- Автоматический expiry (настраивается)

### API Key (CLI/CI)

```http
X-API-Key: upcp_{key_prefix}_{random}
```

- Для CLI и автоматизации
- Привязан к пользователю + организация

---

## Пагинация

### Запрос

```http
GET /api/v1/projects?offset=0&limit=20
```

| Параметр | Тип | Default | Max |
|----------|-----|---------|-----|
| `offset` | int | 0 | — |
| `limit` | int | 20 | 100 |

### Ответ

```json
{
  "data": [...],
  "meta": {
    "total": 142,
    "offset": 0,
    "limit": 20,
    "has_more": true
  }
}
```

---

## Фильтрация

### Синтаксис

```http
GET /api/v1/tasks?filter[state]=in_progress&filter[priority]=high
```

### Операторы

```http
filter[field]=value           # exact match
filter[field_gt]=value        # greater than
filter[field_gte]=value       # greater than or equal
filter[field_lt]=value        # less than
filter[field_lte]=value       # less than or equal
filter[field_like]=value      # LIKE (подстрока)
filter[field_in]=a,b,c        # IN (список)
filter[field_null]=true       # IS NULL
```

### Правила

- Фильтрация только по whitelist полей (ограничена per-endpoint)
- Нет произвольных SQL-выражений
- Максимум 5 фильтров на запрос

---

## Сортировка

```http
GET /api/v1/tasks?sort=-created_at,title
```

- Префикс `-` = DESC, без префикса = ASC
- Множественные поля через запятую
- Whitelist допустимых полей per-endpoint

**Default:** `-created_at` (новые первые)

---

## Формат ошибок

### Структура

```json
{
  "error": {
    "error_code": "VALIDATION_ERROR",
    "message": "Поле 'title' обязательно",
    "hint": "Укажите заголовок задачи",
    "entity": "task",
    "entity_id": null,
    "details": [
      {
        "field": "title",
        "code": "required",
        "message": "This field is required"
      }
    ]
  }
}
```

### Стандартные error codes

| HTTP | error_code | Описание |
|------|-----------|----------|
| 400 | `VALIDATION_ERROR` | Ошибка валидации входных данных |
| 400 | `MALFORMED_REQUEST` | Невалидный JSON / формат |
| 401 | `AUTHENTICATION_REQUIRED` | Нет токена |
| 401 | `TOKEN_EXPIRED` | Токен истёк |
| 403 | `PERMISSION_DENIED` | Нет прав |
| 404 | `NOT_FOUND` | Ресурс не найден |
| 409 | `CONFLICT` | Конфлик состояний (duplicate, state machine) |
| 409 | `ALREADY_EXISTS` | Ресурс уже существует |
| 422 | `UNPROCESSABLE_ENTITY` | Бизнес-валидация не пройдена |
| 429 | `RATE_LIMITED` | Превышен лимит |
| 500 | `INTERNAL_ERROR` | Внутренняя ошибка |
| 503 | `SERVICE_UNAVAILABLE` | Зависимость недоступна |

### Правила

- `message` — человекочитаемое описание (может быть на языке пользователя)
- `error_code` — machine-readable, стабильный
- `details` — массив ошибок полей (для validation)
- `entity` + `entity_id` — контекст ошибки
- Никогда не раскрывать внутренние детали (stack trace, SQL)

---

## Rate Limiting

### Заголовки ответа

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1699999999
Retry-After: 30
```

### При превышении (429)

```json
{
  "error": {
    "error_code": "RATE_LIMITED",
    "message": "Rate limit exceeded",
    "hint": "Retry after 30 seconds",
    "details": {
      "limit": 100,
      "window_seconds": 60,
      "retry_after_seconds": 30
    }
  }
}
```

---

## Идемпотентность

### Заголовок

```http
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
```

### Правила

- Обязателен для `POST` запросов (создание)
- Опционален для `PUT`/`PATCH`/`DELETE`
- UUID v4, клиент генерирует
- Ключ живёт 24 часа в Redis
- При повторном запросе с тем же ключом — возвращается кэшированный ответ
- При конфликте (другое тело) — `409 CONFLICT`

---

## Типичные ответы

### Успешное создание (201)

```http
HTTP/1.1 201 Created
Location: /api/v1/projects/01934b2a-...
Content-Type: application/json

{
  "data": {
    "id": "01934b2a-...",
    "name": "My Project",
    ...
  }
}
```

### Успешное чтение (200)

```json
{
  "data": { ... }
}
```

### Успешный список (200)

```json
{
  "data": [ ... ],
  "meta": { "total": 42, "offset": 0, "limit": 20, "has_more": true }
}
```

### Успешное удаление (204)

```http
HTTP/1.1 204 No Content
```

---

## CORS

```
Access-Control-Allow-Origin: {configured_origin}
Access-Control-Allow-Methods: GET, POST, PUT, PATCH, DELETE, OPTIONS
Access-Control-Allow-Headers: Authorization, Content-Type, Idempotency-Key, X-API-Key
Access-Control-Max-Age: 86400
```

---

## Content-Type

- Запросы: `application/json`
- Ответы: `application/json; charset=utf-8`
- Загрузки: `multipart/form-data`
- Экспорты: `application/octet-stream` (PDF, CSV)

---

## OpenAPI

- Спецификация автоматически генерируется из FastAPI
- Доступна по `/api/v1/openapi.json`
- Swagger UI: `/api/v1/docs` (только в dev/staging)
- ReDoc: `/api/v1/redoc` (только в dev/staging)
