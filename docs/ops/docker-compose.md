# Docker Compose — Configuration

> Project: UPCP | Stack: PostgreSQL 16, FastAPI, Redis 7, React 19, Nginx

## 1. Deployment Architecture

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│  nginx   │────▶│   app   │────▶│   db    │
│ :38080   │     │ :8000   │     │ :35432  │
└─────────┘     └────┬────┘     └─────────┘
                     │
┌─────────┐     ┌────▼────┐
│frontend │     │  redis  │
│ :35173  │     │ :36379  │
└─────────┘     └─────────┘
```

## 2. Services

### 2.1 db (PostgreSQL 16)

```yaml
db:
  image: postgres:16-alpine
  ports:
    - "35432:5432"
  environment:
    POSTGRES_DB: upcp
    POSTGRES_USER: upcp
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
  volumes:
    - pgdata:/var/lib/postgresql/data
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U upcp"]
    interval: 10s
    timeout: 5s
    retries: 5
```

### 2.2 app (FastAPI)

```yaml
app:
  build:
    context: .
    dockerfile: Dockerfile
  ports:
    - "8000:8000"
  environment:
    DATABASE_URL: postgresql+asyncpg://upcp:${POSTGRES_PASSWORD}@db:5432/upcp
    REDIS_URL: redis://redis:6379/0
    JWT_SECRET: ${JWT_SECRET}
    API_KEY_SALT: ${API_KEY_SALT}
    ENVIRONMENT: production
    LOG_LEVEL: INFO
  depends_on:
    db:
      condition: service_healthy
    redis:
      condition: service_healthy
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    interval: 15s
    timeout: 5s
    retries: 3
```

### 2.3 redis

```yaml
redis:
  image: redis:7-alpine
  ports:
    - "36379:6379"
  volumes:
    - redisdata:/data
  command: redis-server --appendonly yes
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 10s
    timeout: 3s
    retries: 5
```

### 2.4 frontend (Vite dev)

```yaml
frontend:
  build:
    context: ./frontend
    dockerfile: Dockerfile
  ports:
    - "35173:5173"
  environment:
    VITE_API_URL: http://localhost:38080/api/v1
  volumes:
    - ./frontend/src:/app/src
```

### 2.5 nginx

```yaml
nginx:
  image: nginx:alpine
  ports:
    - "38080:80"
  volumes:
    - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
  depends_on:
    - app
    - frontend
```

### 2.6 prometheus (profile: observability)

```yaml
prometheus:
  image: prom/prometheus:latest
  ports:
    - "39090:9090"
  volumes:
    - ./observability/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    - promdata:/prometheus
  profiles:
    - observability
```

### 2.7 grafana (profile: observability)

```yaml
grafana:
  image: grafana/grafana:latest
  ports:
    - "33000:3000"
  environment:
    GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD:-admin}
  volumes:
    - ./observability/grafana/provisioning:/etc/grafana/provisioning:ro
    - grafanadata:/var/lib/grafana
  profiles:
    - observability
```

## 3. Ports

| Service | Host | Container | Purpose |
|--------|------|-----------|-----------|
| nginx | 38080 | 80 | Reverse proxy (API + frontend) |
| db | 35432 | 5432 | PostgreSQL (debug access) |
| frontend | 35173 | 5173 | Vite dev server (HMR) |
| redis | 36379 | 6379 | Redis (debug access) |
| prometheus | 39090 | 9090 | Prometheus UI |
| grafana | 33000 | 3000 | Grafana UI |

## 4. Environment Variables

### .env.example

```bash
# Required
POSTGRES_PASSWORD=changeme_use_strong_password
JWT_SECRET=changeme_32_chars_minimum_random
API_KEY_SALT=changeme_random_salt

# Optional
GRAFANA_PASSWORD=admin
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### Application Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | — |
| `REDIS_URL` | Redis connection string | — |
| `JWT_SECRET` | Secret for signing JWT | — |
| `API_KEY_SALT` | Salt for hashing API keys | — |
| `ENVIRONMENT` | `production` / `development` / `testing` | `production` |
| `LOG_LEVEL` | `DEBUG` / `INFO` / `WARNING` / `ERROR` | `INFO` |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:35173` |
| `RATE_LIMIT_DEFAULT` | Request limit per minute | `60` |

## 5. Volumes

| Volume | Service | Purpose |
|--------|--------|-----------|
| `pgdata` | db | PostgreSQL data |
| `redisdata` | redis | Redis AOF persistence |
| `promdata` | prometheus | Metrics storage |
| `grafanadata` | grafana | Dashboard config |

## 6. Launch Commands

```bash
# Production
docker compose up -d

# Development (with hot-reload)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up

# With monitoring
docker compose --profile observability up -d

# Tests
docker compose -f docker-compose.test.yml up --abort-on-container-exit

# Staging
docker compose -f docker-compose.stage.yml up -d
```

## 7. Health Checks

All services have health checks. Startup order:

1. `db` (PostgreSQL) — waits for `pg_isready`
2. `redis` — waits for `redis-cli ping`
3. `app` (FastAPI) — waits for `/health` endpoint (depends on db, redis)
4. `frontend` — starts in parallel
5. `nginx` — starts after app and frontend

## 8. Networks

```yaml
networks:
  upcp-network:
    driver: bridge
```

All services are in a single bridge network. DNS resolution by service name.

## 9. Resource Limits (production)

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 1G
    reservations:
      memory: 512M
```
