# Docker and Ports

External ports are intentionally non-standard.

## All Environments

| Environment | Frontend | Backend | DB | Redis | Compose |
|-------------|----------|---------|-----|-------|---------|
| **Stage** | 3080 | 38081 | 35433 | 36382 | `docker-compose.stage.yml` |
| **Dev** | 3082 | 38080 | 35432 | 36380 | `docker-compose.yml` |
| **Test** | 3081 | 38082 | 35434 | — | `docker-compose.test.yml` |

## Dev Environment Ports

| Service | Internal Port | External Default | Env Variable |
|---|---:|---:|---|
| App/API/UI | 8080 | 38080 | `UPCP_HTTP_PORT` |
| PostgreSQL | 5432 | 35432 | `UPCP_POSTGRES_PORT` |
| Prometheus | 9090 | 39090 | `UPCP_PROMETHEUS_PORT` |
| Grafana | 3000 | 33000 | `UPCP_GRAFANA_PORT` |
| Frontend dev | 5173 | 35173 | `UPCP_FRONTEND_DEV_PORT` |

## Rules

- external services bind to `127.0.0.1` by default;
- do not expose services to LAN unless explicitly needed;
- internal container ports may remain standard;
- if a port conflicts, change only the external port in `.env`.

## Credentials

See [ENVIRONMENTS.md](./ENVIRONMENTS.md) for login/password for each environment.

## Observability

Observability services are optional and use Docker profile:

```bash
docker compose --profile observability up
```
