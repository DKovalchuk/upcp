# Docker and Ports

External ports are intentionally non-standard and configured via `.env.*` files.

## Port Variables

All external-facing ports use `UPCP_PORT_*` prefix:

| Variable | Dev | Test | Stage | Default |
|----------|-----|------|-------|---------|
| `UPCP_PORT_FRONTEND` | 3072 | 3071 | 3070 | 3070 |
| `UPCP_PORT_BACKEND` | 38080 | 38082 | 38081 | 38081 |
| `UPCP_PORT_POSTGRES` | 35432 | 35434 | 35433 | 35433 |
| `UPCP_PORT_REDIS` | 36380 | — | 36382 | 36380 |
| `UPCP_PORT_PROMETHEUS` | 39090 | 39091 | — | 39090 |
| `UPCP_PORT_PUSHGATEWAY` | — | 39092 | — | — |
| `UPCP_PORT_GRAFANA` | 33000 | 33001 | — | 33000 |

## Environment Files

| File | Purpose |
|------|---------|
| `.env.dev` | Dev environment ports |
| `.env.test` | Test environment ports |
| `.env.stage` | Stage environment ports + secrets |

**To change a port:** edit the `.env.*` file. Docker Compose picks it up on next `up`.

## Usage

```bash
# Start with specific env file
docker compose --env-file .env.dev up -d

# Override individual port
UPCP_PORT_FRONTEND=4000 docker compose --env-file .env.dev up -d

# Verify resolved ports
docker compose --env-file .env.dev config
```

## Dev Environment Ports (Reference)

| Service | Internal Port | External Default | Env Variable |
|---|---:|---:|---|
| App/API/UI | 8080 | 38080 | `UPCP_PORT_BACKEND` |
| PostgreSQL | 5432 | 35432 | `UPCP_PORT_POSTGRES` |
| Redis | 6379 | 36380 | `UPCP_PORT_REDIS` |
| Prometheus | 9090 | 39090 | `UPCP_PORT_PROMETHEUS` |
| Grafana | 3000 | 33000 | `UPCP_PORT_GRAFANA` |
| Frontend (nginx) | 80 | 3072 | `UPCP_PORT_FRONTEND` |

## Rules

- External services bind to `127.0.0.1` by default;
- Do not expose services to LAN unless explicitly needed;
- Internal container ports may remain standard;
- If a port conflicts, change only the external port in `.env.*`.

## Credentials

See [ENVIRONMENTS.md](./ENVIRONMENTS.md) for login/password for each environment.

## Observability

Observability services are optional and use Docker profile:

```bash
docker compose --env-file .env.dev --profile observability up
```
