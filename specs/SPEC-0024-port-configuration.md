# SPEC-0024 — Externalize Port Configuration

**Milestone:** M20
**Version:** 0.22.0
**Status:** ACCEPTED
**Created:** 2026-08-17

## 1. Problem

Ports are hardcoded in docker-compose files, scripts, and documentation. When ports need to change (e.g., conflict with DeepSeek Harness), every file must be updated manually — error-prone and verbose.

## 2. Solution

Use per-environment `.env` files as single source of truth for all external-facing ports.

### 2.1 File Structure

```
.env                — base config (secrets, DB creds, app settings)
.env.dev            — dev environment ports
.env.test           — test environment ports
.env.stage          — stage environment ports (exists, extend)
```

### 2.2 Port Variables

All ports exposed to host use `UPCP_PORT_*` prefix:

| Variable | Dev | Test | Stage | Default |
|----------|-----|------|-------|---------|
| `UPCP_PORT_FRONTEND` | 3072 | 3071 | 3070 | 3070 |
| `UPCP_PORT_BACKEND` | 38080 | 38082 | 38081 | 38081 |
| `UPCP_PORT_POSTGRES` | 35432 | 35434 | 35433 | 35433 |
| `UPCP_PORT_REDIS` | 36380 | — | 36382 | 36380 |
| `UPCP_PORT_PROMETHEUS` | 39090 | — | — | 39090 |
| `UPCP_PORT_GRAFANA` | 33000 | — | — | 33000 |

### 2.3 Docker Compose

Each compose file uses variables with fallback defaults:

```yaml
ports:
  - "127.0.0.1:${UPCP_PORT_FRONTEND:-3070}:80"
```

Override via CLI:
```bash
docker compose --env-file .env.dev up -d
```

### 2.4 Scripts

Scripts read from environment with defaults:

```python
PORT = os.environ.get("UPCP_PORT_FRONTEND", "3070")
```

### 2.5 MCP Bridge

Bridge uses env or CLI arg (already works):
```bash
python3 mcp-bridge.py --upcp-url http://localhost:${UPCP_PORT_FRONTEND}/mcp/
```

### 2.6 Documentation

- `docs/ENVIRONMENTS.md` — reference to `.env.*` files, not hardcoded values
- `docs/11-docker-and-ports.md` — table with variable names, not port numbers
- README — mention `--env-file` flag

## 3. Migration

1. Create `.env.dev` and `.env.test` with port variables
2. Extend `.env.stage` with port variables
3. Update all 3 docker-compose files to use `${UPCP_PORT_*}` with defaults
4. Update scripts to read from env
5. Update documentation to reference variables
6. Verify with `docker compose config`

## 4. Breaking Changes

None — defaults match current hardcoded values.

## 5. Out of Scope

- Runtime port reconfiguration (requires restart)
- Port auto-discovery / conflict detection
- CI/CD pipeline changes (GitLab CI uses docker-compose directly)
