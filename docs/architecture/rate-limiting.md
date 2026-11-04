# Rate Limiting — UPCP v2

## Overview

UPCP uses a Redis sliding window rate limiter to protect the API from abuse and ensure fair use. Limits vary by route class and user type.

### Two-layer design (SPEC-0028 / TASK-0173)

1. **IP floor** (`RateLimitMiddleware`) — applies to every path except an
   exact public skip set (`/health`, `/api/v1/health`, `/metrics`,
   `/docs`, `/redoc`, `/openapi.json`, `/docs/oauth2-redirect`).
   There is **no prefix matching**: unknown/future paths are limited by
   default (default-deny).
2. **Per-surface policy** (`SurfaceRateLimit`, attached after the auth
   dependency in `include_surfaces`) — keyed `user:{id}` / `agent:{id}`
   with IP fallback; limits from `UPCP_RATE_LIMIT_WEB_MAX/_WINDOW` and
   `UPCP_RATE_LIMIT_AGENT_MAX/_WINDOW` (defaults 100 req / 60 s).
   `UPCP_DISABLE_RATE_LIMIT` disables both layers.

---

## Algorithm: Sliding Window

### Implementation

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
        # Remove records outside the window
        pipe.zremrangebyscore(key, 0, window_start)
        # Count remaining entries
        pipe.zcard(key)
        # Add the current request
        pipe.zadd(key, {f"{now}": now})
        # Set TTL
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

### Why Sliding Window

- **Fixed window** — the "boundary problem" (burst at end + start of next window)
- **Token bucket** — harder to control burst
- **Sliding window** — smooth limiting, no boundary issues

---

## Route Classes

> **Note (TASK-0173):** enforcement no longer classifies paths by
> `startswith` — the rate-limit modules contain zero path-prefix strings
> (pinned by `test_rate_limit_modules_contain_no_path_hardcodes`). The
> classes below remain as conceptual granularity; the enforced scheme is
> the two-layer design from the Overview.

### Definition

| Class | Description | Route Examples |
|-------|-------------|---------------|
| `auth` | Authentication | `/auth/login`, `/auth/register`, `/auth/refresh` |
| `read` | GET requests, reads | `/projects`, `/tasks`, `/agents` |
| `write` | POST/PUT/PATCH, writes | `/tasks`, `/evidence`, `/reviews` |
| `admin` | Administrative | `/admin/*`, `/settings` |
| `mcp` | MCP tool calls | MCP protocol |
| `health` | Health checks | `/health`, `/ready` |

### Limits

| Class | Default Limit | Window | Burst Limit | Burst Window |
|-------|--------------|--------|-------------|-------------|
| `auth` | 10 | 60 sec | 5 | 10 sec |
| `read` | 100 | 60 sec | 30 | 10 sec |
| `write` | 30 | 60 sec | 10 | 10 sec |
| `admin` | 20 | 60 sec | 5 | 10 sec |
| `mcp` | 60 | 60 sec | 20 | 10 sec |
| `health` | 300 | 60 sec | — | — |

### Limits by User Type

| Type | Multiplier |
|------|-----------|
| Owner (authenticated) | ×1.0 (base) |
| Agent (token) | ×2.0 (doubled limit) |
| API Key | ×1.0 |
| Anonymous | ×0.2 (one-fifth) |

---

## Rate Limit Keys

### Format

```
ratelimit:{class}:{identifier}:{window}
```

### Identifier

| Identifier | Used For |
|------------|----------|
| `user:{user_id}` | Authenticated users |
| `agent:{agent_id}` | MCP agents |
| `api_key:{key_prefix}` | API key clients |
| `ip:{ip_address}` | Anonymous / fallback |

### Key Examples

```
ratelimit:read:user:01934b1f-...:60
ratelimit:write:agent:01934b2a-...:60
ratelimit:auth:ip:192.168.1.1:60
ratelimit:mcp:agent:01934b2a-...:60
```

---

## HTTP Headers

### On Every Response

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1699999999
```

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Maximum requests in the window |
| `X-RateLimit-Remaining` | Remaining requests |
| `X-RateLimit-Reset` | Unix timestamp when the window resets |

### On Exceeding (429)

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
    """Rate limiting middleware for FastAPI."""

    def __init__(self, app, limiter: SlidingWindowRateLimiter):
        super().__init__(app)
        self.limiter = limiter

    async def dispatch(self, request, call_next):
        # Determine the route class
        route_class = self._get_route_class(request)

        # Skip health checks
        if route_class == "health":
            return await call_next(request)

        # Determine the identifier
        identifier = self._get_identifier(request)

        # Get limits
        limit, window = self._get_limits(route_class, request)

        # Check
        result = await self.limiter.check_rate_limit(
            key=f"ratelimit:{route_class}:{identifier}:{window}",
            limit=limit,
            window_seconds=window,
        )

        response = await call_next(request) if result.allowed else self._too_many_requests(result)

        # Add headers
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
# For MCP transport — rate limiting at the tool dispatcher level
class MCPRateLimiter:
    """Rate limiter for MCP tool calls."""

    async def check_tool_rate_limit(
        self,
        agent_id: str,
        tool_name: str,
    ) -> RateLimitResult:
        # General agent limit
        general = await self.limiter.check_rate_limit(
            key=f"ratelimit:mcp:agent:{agent_id}:60",
            limit=60,
            window_seconds=60,
        )
        if not general.allowed:
            return general

        # Per-tool limit for expensive operations
        if tool_name in ("create_task", "submit_task_for_review"):
            return await self.limiter.check_rate_limit(
                key=f"ratelimit:mcp_tool:{tool_name}:agent:{agent_id}:60",
                limit=10,
                window_seconds=60,
            )

        return general
```

---

## Configuration

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
# Health checks and internal monitoring are not rate-limited
# Requests with X-Internal-Service: true header are bypassed
```

---

## Monitoring

### Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `rate_limit_checks_total` | counter | class, allowed | Limit checks |
| `rate_limit_rejected_total` | counter | class | Rejected requests |
| `rate_limit_usage_ratio` | histogram | class | Usage ratio (remaining/limit) |

### Alerts

| Alert | Condition | Severity |
|-------|-----------|----------|
| High rejection rate | `rate(rate_limit_rejected_total[5m]) > 0.1` | warning |
| Near limit | `rate_limit_usage_ratio < 0.1` | info |
