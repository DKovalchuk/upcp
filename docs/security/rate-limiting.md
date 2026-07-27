# Rate Limiting — UPCP v2

> Область: `security` | Версия: 2.0.0

## 1. Обзор

Rate limiting реализован на уровне middleware с использованием Redis для распределённого хранения счётчиков. Лимиты применяются по IP, пользователю, агенту и токену.

## 2. Архитектура

```
Request → RateLimitMiddleware → Sliding Window Counter (Redis) → Handler
                                    ↓
                              429 Too Many Requests
```

- Алгоритм: Sliding Window Counter
- Хранение: Redis с TTL
- Возврат заголовков: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`, `Retry-After`

## 3. Лимиты

### 3.1 Публичные эндпоинты (без аутентификации)

| Эндпоинт                    | Лимит           | Ключ       | Блокировка           |
|----------------------------|----------------|-----------|---------------------|
| `POST /auth/login`          | 5 req/min      | IP        | 15 мин после 5 fail |
| `POST /auth/register`      | 3 req/min      | IP        | 30 мин после 3 fail |
| `POST /auth/setup`         | 3 req/min      | IP        | Навсегда после 3    |
| `POST /auth/password/reset`| 3 req/hour     | Email     | 1 час после 3       |
| `GET /health`               | 60 req/min     | IP        | —                   |

### 3.2 Аутентифицированные запросы

| Категория              | Лимит           | Ключ              |
|-----------------------|----------------|-------------------|
| Общие запросы          | 1000 req/min   | User ID           |
| Создание задач         | 30 req/min     | User ID           |
| Загрузка файлов        | 50 req/min     | User ID           |
| Аудит-лог (чтение)    | 100 req/min    | User ID           |
| Админ-эндпоинты        | 100 req/min    | User ID           |

### 3.3 Агентские токены

| Категория              | Лимит           | Ключ              |
|-----------------------|----------------|-------------------|
| Общие запросы          | 500 req/min    | Agent Token ID    |
| Heartbeat              | 120 req/min    | Agent Token ID    |
| File operations        | 50 req/min     | Agent Token ID    |
| MCP tool calls         | 200 req/min    | Agent Token ID    |
| Task submissions       | 30 req/min     | Agent Token ID    |

### 3.4 MCP эндпоинты

| Категория              | Лимит           | Ключ              |
|-----------------------|----------------|-------------------|
| MCP requests           | 200 req/min    | Token ID          |
| MCP tool discovery     | 30 req/min     | Token ID          |
| MCP resource read      | 100 req/min    | Token ID          |

### 3.5 Webhook / Callbacks

| Категория              | Лимит           | Ключ              |
|-----------------------|----------------|-------------------|
| GitLab webhook         | 100 req/min    | IP + Project ID   |
| Git webhook            | 100 req/min    | IP + Project ID   |

## 4. Заголовки ответа

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 847
X-RateLimit-Reset: 1721981700
Retry-After: 30          # только при 429
```

## 5. Обработка превышения

```json
// 429 Too Many Requests
{
  "error": "rate_limit_exceeded",
  "message": "Rate limit exceeded. Try again in 30 seconds.",
  "retry_after": 30,
  "limit": 1000,
  "window": "60s"
}
```

## 6. Sliding Window — детали

```python
# Redis key pattern
rate_limit:{key_type}:{key_value}:{window_start}

# Пример
rate_limit:ip:192.168.1.1:1721980800

# Алгоритм:
# 1. Вычисляем текущее окно (floor timestamp / window_size)
# 2. Считаем запросы в текущем + предыдущем окне
# 3. Взвешенная сумма: prev_count * overlap_ratio + current_count
# 4. Если >= limit → 429
```

## 7. Злоупотребления (Abuse Detection)

### 7.1 Детектируемые паттерны

| Паттерн                          | Действие                              |
|---------------------------------|---------------------------------------|
| Brute-force login               | Блокировка IP на 15 мин              |
| Credential stuffing             | Блокировка IP + email на 1 час       |
| Token enumeration               | Блокировка IP + audit event          |
| API scraping                    | Throttle до 10 req/min               |
| Burst requests (>80% limit за 10 сек) | Soft throttle до 50% лимита    |

### 7.2 Эскалация

```
Первое нарушение → 429 + заголовки
Повторное (3x за 10 мин) → 429 + audit event
Систематическое (10x за 1 час) → 429 + IP block + уведомление админу
```

### 7.3 Audit Events

| Событие                          | Уровень    |
|---------------------------------|-----------|
| `rate_limit.exceeded`           | warning   |
| `rate_limit.abuse_detected`     | critical  |
| `rate_limit.ip_blocked`         | critical  |
| `rate_limit.throttle_applied`   | info      |

## 8. Bypass и исключения

### 8.1 Не подлежат rate limiting

- `GET /health` — healthcheck
- `GET /api/v1/auth/jwks` — JWKS endpoint

### 8.2 Повышенные лимиты

- Глобальные Owner/Admin: 2x стандартного лимита
- Internal service accounts: настраиваемый лимит

### 8.3 Конфигурация

```python
# app/rate_limit_config.py
RATE_LIMITS = {
    "login": {"limit": 5, "window": 60, "key": "ip"},
    "register": {"limit": 3, "window": 60, "key": "ip"},
    "authenticated": {"limit": 1000, "window": 60, "key": "user_id"},
    "agent": {"limit": 500, "window": 60, "key": "token_id"},
    "mcp": {"limit": 200, "window": 60, "key": "token_id"},
}
```

## 9. Мониторинг

- Метрики: `rate_limit_total`, `rate_limit_blocked_total`, `rate_limit_abuse_total`
- Дашборд: топ заблокированных IP, частота превышений по эндпоинтам
- Алёрт: если abuse rate > 100/час → уведомление
