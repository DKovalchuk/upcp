# Rate Limiting — UPCP v2

> Scope: `security` | Version: 2.0.0

## 1. Overview

Rate limiting is implemented at the middleware level using Redis for distributed counter storage. Limits are applied per IP, user, agent, and token.

## 2. Architecture

```
Request → RateLimitMiddleware → Sliding Window Counter (Redis) → Handler
                                    ↓
                              429 Too Many Requests
```

- Algorithm: Sliding Window Counter
- Storage: Redis with TTL
- Response headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`, `Retry-After`

## 3. Limits

### 3.1 Public Endpoints (no authentication)

| Endpoint                      | Limit           | Key        | Lockout                |
|-------------------------------|-----------------|------------|------------------------|
| `POST /auth/login`            | 5 req/min       | IP         | 15 min after 5 fails   |
| `POST /auth/register`         | 3 req/min       | IP         | 30 min after 3 fails   |
| `POST /auth/setup`            | 3 req/min       | IP         | Permanent after 3      |
| `POST /auth/password/reset`   | 3 req/hour      | Email      | 1 hour after 3         |
| `GET /health`                 | 60 req/min      | IP         | —                      |

### 3.2 Authenticated Requests

| Category               | Limit           | Key               |
|------------------------|-----------------|--------------------|
| General requests       | 1000 req/min    | User ID           |
| Task creation          | 30 req/min      | User ID           |
| File uploads           | 50 req/min      | User ID           |
| Audit log (read)       | 100 req/min     | User ID           |
| Admin endpoints        | 100 req/min     | User ID           |

### 3.3 Agent Tokens

| Category               | Limit           | Key               |
|------------------------|-----------------|--------------------|
| General requests       | 500 req/min     | Agent Token ID    |
| Heartbeat              | 120 req/min     | Agent Token ID    |
| File operations        | 50 req/min      | Agent Token ID    |
| MCP tool calls         | 200 req/min     | Agent Token ID    |
| Task submissions       | 30 req/min      | Agent Token ID    |

### 3.4 MCP Endpoints

| Category               | Limit           | Key               |
|------------------------|-----------------|--------------------|
| MCP requests           | 200 req/min     | Token ID          |
| MCP tool discovery     | 30 req/min      | Token ID          |
| MCP resource read      | 100 req/min     | Token ID          |

### 3.5 Webhook / Callbacks

| Category               | Limit           | Key                    |
|------------------------|-----------------|-------------------------|
| GitLab webhook         | 100 req/min     | IP + Project ID        |
| Git webhook            | 100 req/min     | IP + Project ID        |

## 4. Response Headers

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 847
X-RateLimit-Reset: 1721981700
Retry-After: 30          # only on 429
```

## 5. Exceeded Handling

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

## 6. Sliding Window — Details

```python
# Redis key pattern
rate_limit:{key_type}:{key_value}:{window_start}

# Example
rate_limit:ip:192.168.1.1:1721980800

# Algorithm:
# 1. Compute current window (floor timestamp / window_size)
# 2. Count requests in current + previous window
# 3. Weighted sum: prev_count * overlap_ratio + current_count
# 4. If >= limit → 429
```

## 7. Abuse Detection

### 7.1 Detectable Patterns

| Pattern                                | Action                               |
|----------------------------------------|---------------------------------------|
| Brute-force login                      | Block IP for 15 min                  |
| Credential stuffing                    | Block IP + email for 1 hour          |
| Token enumeration                      | Block IP + audit event               |
| API scraping                           | Throttle to 10 req/min               |
| Burst requests (>80% limit in 10 sec)  | Soft throttle to 50% of limit        |

### 7.2 Escalation

```
First violation → 429 + headers
Repeated (3x in 10 min) → 429 + audit event
Systematic (10x in 1 hour) → 429 + IP block + admin notification
```

### 7.3 Audit Events

| Event                              | Severity   |
|------------------------------------|-----------|
| `rate_limit.exceeded`              | warning   |
| `rate_limit.abuse_detected`        | critical  |
| `rate_limit.ip_blocked`            | critical  |
| `rate_limit.throttle_applied`      | info      |

## 8. Bypasses and Exceptions

### 8.1 Not Subject to Rate Limiting

- `GET /health` — healthcheck
- `GET /api/v1/auth/jwks` — JWKS endpoint

### 8.2 Increased Limits

- Global Owner/Admin: 2x the standard limit
- Internal service accounts: configurable limit

### 8.3 Configuration

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

## 9. Monitoring

- Metrics: `rate_limit_total`, `rate_limit_blocked_total`, `rate_limit_abuse_total`
- Dashboard: top blocked IPs, violation frequency by endpoint
- Alert: if abuse rate > 100/hour → notification
