# Rate Limiting — UPCP v2

## Обзор

UPCP использует Redis sliding window rate limiter для защиты API от злоупотреблений и обеспечения fair use. Лимиты различаются по классам маршрутов и типам пользователей.

---

## Алгоритм: Sliding Window

### Реализация

```python
import time
from redis.asyncio import Redis

class SlidingWindowRateLimiter:
    """Redis-based sliding window rate limiter."""

    def __init__(self, redis: Redis):
        self.redis = redis

    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> RateLimitResult:
        now = time.time()
        window_start = now - window_seconds

        pipe = self.redis.pipeline(transaction=True)
        # Удаляем записи вне окна
        pipe.zremrangebyscore(key, 0, window_start)
        # Считаем оставшиеся
        pipe.zcard(key)
        # Добавляем текущий запрос
        pipe.zadd(key, {f"{now}": now})
        # Устанавливаем TTL
        pipe.expire(key, window_seconds + 1)

        results = await pipe.execute()
        current_count = results[1]

        remaining = max(0, limit - current_count - 1)
        reset_at = int(now + window_seconds)

        if current_count >= limit:
            return RateLimitResult(
                allowed=False,
                limit=limit,
                remaining=0,
                reset_at=reset_at,
                retry_after=window_seconds,
            )

        return RateLimitResult(
            allowed=True,
            limit=limit,
            remaining=remaining,
            reset_at=reset_at,
            retry_after=0,
        )
```

### Почему Sliding Window

- **Fixed window** — проблема «границы окна» (burst в конце + начало следующего)
- **Token bucket** — сложнее контролировать burst
- **Sliding window** — плавное ограничение, нет проблем с границами

---

## Классы маршрутов

### Определение

| Класс | Описание | Примеры маршрутов |
|-------|----------|-------------------|
| `auth` | Аутентификация | `/auth/login`, `/auth/register`, `/auth/refresh` |
| `read` | GET-запросы, чтение | `/projects`, `/tasks`, `/agents` |
| `write` | POST/PUT/PATCH, запись | `/tasks`, `/evidence`, `/reviews` |
| `admin` | Административные | `/admin/*`, `/settings` |
| `mcp` | MCP tool calls | MCP protocol |
| `health` | Health checks | `/health`, `/ready` |

### Лимиты

| Класс | Default Limit | Window | Burst Limit | Burst Window |
|-------|--------------|--------|-------------|-------------|
| `auth` | 10 | 60 сек | 5 | 10 сек |
| `read` | 100 | 60 сек | 30 | 10 сек |
| `write` | 30 | 60 сек | 10 | 10 сек |
| `admin` | 20 | 60 сек | 5 | 10 сек |
| `mcp` | 60 | 60 сек | 20 | 10 сек |
| `health` | 300 | 60 сек | — | — |

### Лимиты по типу пользователя

| Тип | Множитель |
|-----|----------|
| Owner (authenticated) | ×1.0 (base) |
| Agent (token) | ×2.0 (удвоенный лимит) |
| API Key | ×1.0 |
| Anonymous | ×0.2 (пятая часть) |

---

## Rate Limit Keys

### Формат

```
ratelimit:{class}:{identifier}:{window}
```

### Identifier

| Идентификатор | Используется для |
|---------------|-----------------|
| `user:{user_id}` | Authenticated users |
| `agent:{agent_id}` | MCP agents |
| `api_key:{key_prefix}` | API key clients |
| `ip:{ip_address}` | Anonymous / fallback |

### Примеры ключей

```
ratelimit:read:user:01934b1f-...:60
ratelimit:write:agent:01934b2a-...:60
ratelimit:auth:ip:192.168.1.1:60
ratelimit:mcp:agent:01934b2a-...:60
```

---

## HTTP Headers

### При каждом ответе

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1699999999
```

| Header | Описание |
|--------|----------|
| `X-RateLimit-Limit` | Максимум запросов в окне |
| `X-RateLimit-Remaining` | Оставшиеся запросы |
| `X-RateLimit-Reset` | Unix timestamp когда окно сбрасывается |

### При превышении (429)

```http
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1699999999
Retry-After: 30
Content-Type: application/json
```

```json
{
    "error": {
        "error_code": "RATE_LIMITED",
        "message": "Rate limit exceeded for this endpoint",
        "hint": "Retry after 30 seconds",
        "details": {
            "limit": 100,
            "window_seconds": 60,
            "retry_after_seconds": 30,
            "class": "read"
        }
    }
}
```

---

## FastAPI Integration

### Middleware

```python
from starlette.middleware.base import BaseHTTPMiddleware

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware для FastAPI."""

    def __init__(self, app, limiter: SlidingWindowRateLimiter):
        super().__init__(app)
        self.limiter = limiter

    async def dispatch(self, request, call_next):
        # Определяем класс маршрута
        route_class = self._get_route_class(request)

        # Пропускаем health checks
        if route_class == "health":
            return await call_next(request)

        # Определяем идентификатор
        identifier = self._get_identifier(request)

        # Получаем лимит
        limit, window = self._get_limits(route_class, request)

        # Проверяем
        result = await self.limiter.check_rate_limit(
            key=f"ratelimit:{route_class}:{identifier}:{window}",
            limit=limit,
            window_seconds=window,
        )

        response = await call_next(request) if result.allowed else self._too_many_requests(result)

        # Добавляем заголовки
        response.headers["X-RateLimit-Limit"] = str(result.limit)
        response.headers["X-RateLimit-Remaining"] = str(result.remaining)
        response.headers["X-RateLimit-Reset"] = str(result.reset_at)

        if not result.allowed:
            response.headers["Retry-After"] = str(result.retry_after)

        return response
```

### Route Class Detection

```python
def _get_route_class(self, request) -> str:
    path = request.url.path

    if path.startswith("/health"):
        return "health"
    elif path.startswith("/auth"):
        return "auth"
    elif path.startswith("/admin"):
        return "admin"
    elif request.method in ("GET", "HEAD", "OPTIONS"):
        return "read"
    else:
        return "write"
```

### MCP Integration

```python
# Для MCP transport — rate limiting на уровне tool dispatcher
class MCPRateLimiter:
    """Rate limiter для MCP tool calls."""

    async def check_tool_rate_limit(
        self,
        agent_id: str,
        tool_name: str,
    ) -> RateLimitResult:
        # Общий лимит агента
        general = await self.limiter.check_rate_limit(
            key=f"ratelimit:mcp:agent:{agent_id}:60",
            limit=60,
            window_seconds=60,
        )
        if not general.allowed:
            return general

        # Per-tool лимит для дорогих операций
        if tool_name in ("create_task", "submit_task_for_review"):
            return await self.limiter.check_rate_limit(
                key=f"ratelimit:mcp_tool:{tool_name}:agent:{agent_id}:60",
                limit=10,
                window_seconds=60,
            )

        return general
```

---

## Конфигурация

### Environment Variables

```env
# Global
RATE_LIMIT_ENABLED=true
RATE_LIMIT_STORAGE=redis

# Per-class overrides
RATE_LIMIT_AUTH=10/60          # 10 requests per 60 seconds
RATE_LIMIT_READ=100/60
RATE_LIMIT_WRITE=30/60
RATE_LIMIT_ADMIN=20/60
RATE_LIMIT_MCP=60/60
RATE_LIMIT_HEALTH=300/60

# Multipliers
RATE_LIMIT_AGENT_MULTIPLIER=2.0
RATE_LIMIT_ANONYMOUS_MULTIPLIER=0.2
```

### Per-Endpoint Override

```python
@router.post(
    "/tasks/{task_id}/claim",
    rate_limit={"limit": 5, "window": 60},  # Stricter for claim
)
async def claim_task(task_id: UUID, ...):
    ...
```

---

## Bypass

### IP Whitelist

```python
RATE_LIMIT_WHITELIST_IPS=127.0.0.1,10.0.0.0/8
```

### Internal Services

```python
# Health checks and internal monitoring не лимитируются
# Запросы с X-Internal-Service: true header пропускаются
```

---

## Monitoring

### Metrics

| Метрика | Тип | Labels | Описание |
|---------|-----|--------|----------|
| `rate_limit_checks_total` | counter | class, allowed | Проверки лимитов |
| `rate_limit_rejected_total` | counter | class | Отклонённые запросы |
| `rate_limit_usage_ratio` | histogram | class | Использование (remaining/limit) |

### Alerts

| Alert | Condition | Severity |
|-------|-----------|----------|
| High rejection rate | `rate(rate_limit_rejected_total[5m]) > 0.1` | warning |
| Near limit | `rate_limit_usage_ratio < 0.1` | info |
