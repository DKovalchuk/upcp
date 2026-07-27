# Runbook: Rate Limiting

> Project: UPCP | Storage: Redis | Framework: FastAPI

## 1. Overview

Rate limiting protects UPCP from abuse and overload. Limits are applied at the API level and aggregated in Redis.

## 2. How Limits Work

### 2.1 Algorithm
- **Sliding window** — limits are calculated over a sliding window
- Storage: Redis with TTL
- Key: `rate_limit:{identity}:{endpoint_group}`
- Identity: user_id (for JWT) or client_ip (for unauthenticated)

### 2.2 Configuration

| Endpoint Group | Limit | Window | Description |
|---------------|-------|------|----------|
| `default` | 60 req | 1 min | All standard endpoints |
| `auth` | 10 req | 1 min | Login, register, refresh |
| `task_claim` | 30 req | 1 min | Claim/release operations |
| `heartbeat` | 120 req | 1 min | Heartbeat (frequent calls) |
| `upload` | 10 req | 1 min | Evidence upload |
| `admin` | 200 req | 1 min | Admin endpoints |

### 2.3 Response Headers

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1690454400
Retry-After: 30  # only on 429
```

## 3. When Limits Trigger

### 3.1 Signs
- Client receives HTTP 429
- In logs: `Rate limit exceeded for {identity} on {endpoint}`
- Metric: `upcp_rate_limit_hits_total` is increasing

### 3.2 Common Causes
- Script with no delay between requests
- Multiple agents using the same API key
- Repeated retries on network errors (retry storm)
- Brute-force attack on auth endpoints

## 4. How to Check Current Limits

### 4.1 Via Redis

```bash
# Current value for a user
docker compose exec redis redis-cli GET "rate_limit:user:USER_ID:default"

# All rate limit keys
docker compose exec redis redis-cli KEYS "rate_limit:*"

# TTL of a specific key
docker compose exec redis redis-cli TTL "rate_limit:user:USER_ID:default"
```

### 4.2 Via API

```bash
# Send a request and inspect headers
curl -sI -H "Authorization: Bearer TOKEN" http://localhost:38080/api/v1/tasks | grep -i ratelimit
```

### 4.3 Via Grafana

Dashboard: **Auth & Security** → Panel: **Rate Limit Hits**

## 5. How to Change Limits

### 5.1 Globally

```bash
# .env
RATE_LIMIT_DEFAULT=120        # was 60
RATE_LIMIT_AUTH=20            # was 10
RATE_LIMIT_HEARTBEAT=300      # was 120

# Restart
docker compose restart app
```

### 5.2 For a specific endpoint group

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

### 5.3 Temporarily (without restart)

```bash
# Increase the limit for a specific user via Redis
docker compose exec redis redis-cli SET "rate_limit:user:USER_ID:default" 0
# This resets the counter; TTL will restart on the next request
```

## 6. How to Add a Whitelist

### 6.1 By IP

```bash
# .env
RATE_LIMIT_WHITELIST=10.0.0.0/8,192.168.1.0/24

# Or specific IPs
RATE_LIMIT_WHITELIST=10.0.0.5,10.0.0.6
```

### 6.2 By User (VIP)

```python
# In DB: add field is_rate_limit_exempt
# In middleware: skip limits for exempt users
```

### 6.3 Internal Services

```bash
# Internal health checks and monitoring should not be rate limited
RATE_LIMIT_WHITELIST_PATHS=/health,/metrics,/ready
```

## 7. Monitoring

### 7.1 Alerts

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

### 8.1 Disable Rate Limiting (Emergency)

```bash
# .env
RATE_LIMIT_ENABLED=false

# Restart
docker compose restart app
```

⚠️ **DANGER**: exposes the system to abuse. Use only during critical incidents.

### 8.2 Block an IP (Manual Ban)

```bash
# Add IP to blacklist via Redis
docker compose exec redis redis-cli SET "blocked_ip:ATTACKER_IP" "1" EX 3600

# Check blacklist in the application before rate limit
```

### 8.3 Reset All Limits

```bash
# Delete all rate limit keys
docker compose exec redis redis-cli KEYS "rate_limit:*" | xargs -r docker compose exec redis redis-cli DEL
```

⚠️ Only when necessary. All users will receive full limits.

## 9. Prevention

1. **Exponential backoff** — clients must use backoff on 429
2. **API key rotation** — regular rotation of agent keys
3. **Monitoring** — alerts on anomalous patterns
4. **Load testing** — verify limits before release
