# Runbook: Rate Limiting

> Проект: UPCP | Хранилище: Redis | Фреймворк: FastAPI

## 1. Обзор

Rate limiting защищает UPCP от abuse и перегрузки. Лимиты применяются на уровне API и агрегируются в Redis.

## 2. Как работают лимиты

### 2.1 Алгоритм
- **Sliding window** — лимиты считаются за скользящее окно
- Хранилище: Redis с TTL
- Ключ: `rate_limit:{identity}:{endpoint_group}`
- Identity: user_id (для JWT) или client_ip (для неавторизованных)

### 2.2 Конфигурация

| Endpoint Group | Лимит | Окно | Описание |
|---------------|-------|------|----------|
| `default` | 60 req | 1 min | Все обычные эндпоинты |
| `auth` | 10 req | 1 min | Login, register, refresh |
| `task_claim` | 30 req | 1 min | Claim/release операции |
| `heartbeat` | 120 req | 1 min | Heartbeat (частые вызовы) |
| `upload` | 10 req | 1 min | Evidence upload |
| `admin` | 200 req | 1 min | Admin эндпоинты |

### 2.3 Заголовки ответа

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1690454400
Retry-After: 30  # только при 429
```

## 3. Когда срабатывают лимиты

### 3.1 Признаки
- Клиент получает HTTP 429
- В логах: `Rate limit exceeded for {identity} on {endpoint}`
- Метрика: `upcp_rate_limit_hits_total` увеличивается

### 3.2 Типичные причины
- Скрипт без задержки между запросами
- Несколько агентов используют один API-ключ
- Повторные попытки при сетевых ошибках (retry storm)
- Атака brute-force на auth endpoints

## 4. Как проверить текущие лимиты

### 4.1 Через Redis

```bash
# Текущее значение для пользователя
docker compose exec redis redis-cli GET "rate_limit:user:USER_ID:default"

# Все ключи rate limit
docker compose exec redis redis-cli KEYS "rate_limit:*"

# TTL конкретного ключа
docker compose exec redis redis-cli TTL "rate_limit:user:USER_ID:default"
```

### 4.2 Через API

```bash
# Отправить запрос и посмотреть заголовки
curl -sI -H "Authorization: Bearer TOKEN" http://localhost:38080/api/v1/tasks | grep -i ratelimit
```

### 4.3 Через Grafana

Dashboard: **Auth & Security** → Панель: **Rate Limit Hits**

## 5. Как изменить лимиты

### 5.1 Глобально

```bash
# .env
RATE_LIMIT_DEFAULT=120        # было 60
RATE_LIMIT_AUTH=20            # было 10
RATE_LIMIT_HEARTBEAT=300      # было 120

# Перезапустить
docker compose restart app
```

### 5.2 Для конкретного endpoint group

```python
# src/upcp/api/rate_limit.py
RATE_LIMITS = {
    "default": {"limit": 60, "window": 60},
    "auth": {"limit": 10, "window": 60},
    "task_claim": {"limit": 30, "window": 60},
    "heartbeat": {"limit": 120, "window": 60},
    "upload": {"limit": 10, "window": 60},
    "admin": {"limit": 200, "window": 60},
}
```

### 5.3 Временно (без перезапуска)

```bash
# Увеличить лимит для конкретного пользователя через Redis
docker compose exec redis redis-cli SET "rate_limit:user:USER_ID:default" 0
# Это сбросит счётчик; TTL перезапустится при следующем запросе
```

## 6. Как добавить whitelist

### 6.1 По IP

```bash
# .env
RATE_LIMIT_WHITELIST=10.0.0.0/8,192.168.1.0/24

# Или конкретные IP
RATE_LIMIT_WHITELIST=10.0.0.5,10.0.0.6
```

### 6.2 По пользователю (VIP)

```python
# В БД: добавить поле is_rate_limit_exempt
# В middleware: пропускать лимиты для exempt пользователей
```

### 6.3 Internal сервисы

```bash
# Internal health checks и мониторинг не должны лимитироваться
RATE_LIMIT_WHITELIST_PATHS=/health,/metrics,/ready
```

## 7. Мониторинг

### 7.1 Алёрты

```yaml
# alerting-rules.yml
groups:
  - name: rate-limiting
    rules:
      - alert: HighRateLimitHits
        expr: sum(rate(upcp_rate_limit_hits_total[5m])) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Rate limit hits > 10/min"

      - alert: RateLimitSpike
        expr: sum(rate(upcp_rate_limit_hits_total[1m])) > 50
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Rate limit spike: > 50 hits in 1 min"
```

### 7.2 Dashboard

Dashboard: **Auth & Security** → Panels:
- Rate Limit Hits by endpoint
- Rate Limit Hits by IP
- Top rate-limited users

## 8. Emergency Procedures

### 8.1 Отключить rate limiting (аварийно)

```bash
# .env
RATE_LIMIT_ENABLED=false

# Перезапустить
docker compose restart app
```

⚠️ **ОПАСНО**: открывает систему для abuse. Использовать только при критических проблемах.

### 8.2 Заблокировать IP (ручной бан)

```bash
# Добавить IP в blacklist через Redis
docker compose exec redis redis-cli SET "blocked_ip:ATTACKER_IP" "1" EX 3600

# В приложении проверять blacklist перед rate limit
```

### 8.3 Сбросить все лимиты

```bash
# Удалить все ключи rate limit
docker compose exec redis redis-cli KEYS "rate_limit:*" | xargs -r docker compose exec redis redis-cli DEL
```

⚠️ Только при необходимости. Все пользователи получат полные лимиты.

## 9. Предотвращение

1. **Exponential backoff** — клиенты должны использовать backoff при 429
2. **API key rotation** — регулярная ротация ключей агентов
3. **Monitoring** — алерты на аномальные паттерны
4. **Load testing** — проверять лимиты перед релизом
