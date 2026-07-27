# Безопасное развёртывание — UPCP v2

> Область: `security` / `devops` | Версия: 2.0.0

## 1. Чеклист безопасности

**Pre-deployment:**
- [ ] Секреты через SecretProvider (не env файлы)
- [ ] JWT ключи (RS256, 2048+ bit) и `ENCRYPTION_KEY` (AES-256) сгенерированы
- [ ] Database user с минимальными привилегиями
- [ ] CORS на конкретные домены, security headers, rate limiting, audit logging
- [ ] TLS termination, debug endpoints отключены

**Post-deployment:**
- [ ] Healthcheck, login, rate limiting (429), audit events работают
- [ ] Логи не содержат секретов, API не возвращает секреты, backup работает

## 2. Docker Security

```dockerfile
FROM python:3.12-slim AS base
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev curl && rm -rf /var/lib/apt/lists/*
# ...
RUN addgroup -S upcp && adduser -S upcp -G upcp
USER upcp
```

```yaml
# docker-compose.yml (ключевые параметры)
services:
  app:
    read_only: true
    tmpfs: [/tmp:size=100M]
    security_opt: [no-new-privileges:true]
    cap_drop: [ALL]
    cap_add: [NET_BIND_SERVICE]
    deploy:
      resources:
        limits: { cpus: '2.0', memory: 2G }
        reservations: { cpus: '0.5', memory: 512M }
```

Правила: только official/pinned образы, сканирование `docker scout cves`, multi-stage builds.

## 3. Environment Variables

```bash
APP_ENV=production          # обязательно
APP_DEBUG=false             # обязательно
CORS_ORIGINS=https://app.example.com
# Остальные (DATABASE_URL, REDIS_URL, JWT_*, ENCRYPTION_KEY) — через SecretProvider
```

Запрещено в production: `APP_DEBUG=true`, `PYTHONDEVMODE=1`, hardcoded credentials.

## 4. Secret Management

**HashiCorp Vault (production):**
```bash
vault secrets enable -path=upcp kv-v2
vault kv put upcp/production/database url="postgresql://..."
vault kv put upcp/production/jwt private_key="..." public_key="..."
vault kv put upcp/production/encryption key="..."
```

**Encrypted file (self-hosted):**
```bash
openssl rand -base64 32 > /etc/upcp/master.key && chmod 600 /etc/upcp/master.key
openssl enc -aes-256-cbc -salt -in secrets.env -out secrets.enc -pass file:/etc/upcp/master.key
```

**Docker secrets:** external secrets referenced in compose, mounted as files in container.

## 5. Network Isolation

```yaml
networks:
  frontend: { driver: bridge }
  backend: { driver: bridge, internal: true }

services:
  app:      { networks: [frontend, backend] }
  postgres: { networks: [backend] }    # только внутренняя сеть
  redis:    { networks: [backend] }    # только внутренняя сеть
```

PostgreSQL и Redis доступны **только** из backend сети. Нет прямого доступа к БД извне. Reverse proxy (nginx/Caddy) → App.

## 6. TLS Termination (Nginx)

```nginx
server {
    listen 443 ssl http2;
    server_name app.example.com;
    ssl_certificate     /etc/ssl/certs/app.crt;
    ssl_certificate_key /etc/ssl/private/app.key;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
    ssl_prefer_server_ciphers on;
    ssl_session_cache   shared:SSL:10m;
    ssl_session_timeout 10m;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    location / {
        proxy_pass http://app:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
server {
    listen 80;
    server_name app.example.com;
    return 301 https://$host$request_uri;
}
```

## 7. CORS

```python
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "").split(",")
CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
CORS_ALLOW_HEADERS = ["Authorization", "Content-Type", "X-Request-ID", "X-Agent-Token"]
CORS_EXPOSE_HEADERS = ["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"]
CORS_ALLOW_CREDENTIALS = True
CORS_MAX_AGE = 600
```

## 8. Security Headers

```python
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "0",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "accelerometer=(), camera=(), geolocation=(), microphone=(), payment=()",
    "Content-Security-Policy": (
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; font-src 'self' https://fonts.gstatic.com; "
        "connect-src 'self' wss:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    ),
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
    "Cross-Origin-Embedder-Policy": "require-corp",
}
```

## 9. Database Security (PostgreSQL)

```sql
-- Отдельный пользователь с минимальными правами
CREATE USER upcp_app WITH PASSWORD '...';
GRANT CONNECT ON DATABASE upcp TO upcp_app;
GRANT USAGE ON SCHEMA public TO upcp_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO upcp_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO upcp_app;
REVOKE CREATE ON SCHEMA public FROM upcp_app;  -- миграции отдельным пользователем
```

Подключение:
```python
engine = create_async_engine(
    DATABASE_URL, pool_size=10, max_overflow=5, pool_timeout=30,
    pool_recycle=1800, echo=False,
    connect_args={"sslmode": "verify-full",
                  "sslrootcert": "/etc/ssl/certs/ca-certificates.crt"},
)
```

## 10. Redis Security

```conf
# redis.conf
bind 0.0.0.0
protected-mode yes
requirepass <from SecretProvider>
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command DEBUG ""
rename-command CONFIG "CONFIG_b82a3f..."
```

Подключение в приложении: SSL, password, таймауты 5 сек, `retry_on_timeout=True`.

## 11. Monitoring и Alerting

| Метрика                    | Порог              | Действие           |
|---------------------------|--------------------|--------------------|
| Failed login attempts     | > 50/min           | Alert + auto-block |
| 5xx error rate            | > 1%               | Alert on-call      |
| Disk / Memory usage       | > 80% / > 85%      | Alert              |
| Audit event count drop    | > 50% от baseline  | Alert              |
| Certificate expiry        | < 30 days          | Alert              |
| Dependency CVE             | Critical           | Alert              |

**Healthcheck** (`GET /health`): не раскрывает конфигурацию, не требует аутентификации, rate limit 60 req/min.
