# TASK-0119 — Externalize Port Configuration

**Milestone:** M20
**Sprint:** S22.5
**Points:** 3
**Spec:** SPEC-0024
**Status:** DONE (closed 2026-10-17)

## Objective

Replace hardcoded ports with environment-based configuration via `.env.*` files.

## Acceptance Criteria

- [x] `.env.dev` exists with all dev port variables (6 × `UPCP_PORT_*`)
- [x] `.env.test` exists with all test port variables (13 × `UPCP_PORT_*`)
- [x] `.env.stage` extended with port variables (preserves existing secrets)
- [x] `docker-compose.yml` uses `${UPCP_PORT_*:-default}` for all ports — *gap closed: renamed legacy `UPCP_REDIS_PORT`/`UPCP_HTTP_PORT`/`UPCP_PROMETHEUS_PORT`/`UPCP_GRAFANA_PORT` → `UPCP_PORT_*` (deviation note: legacy names were self-consistent but violated the single-prefix contract from docs/11; local gitignored `.env` and `.env.example` renamed to match)*
- [x] `docker-compose.test.yml` uses `${UPCP_PORT_*:-default}` for all ports
- [x] `docker-compose.stage.yml` uses `${UPCP_PORT_*:-default}` for all ports — *gap closed: hardcoded redis `36382` + backend `38081` replaced with `${UPCP_PORT_REDIS:-36382}` / `${UPCP_PORT_BACKEND:-38081}`*
- [x] `scripts/populate_upcp_v2.py` reads port from env (`UPCP_PORT_FRONTEND`, fallback 3070)
- [x] `scripts/populate_m17_m20.py` reads port from env (frontend + postgres)
- [x] `frontend/e2e/comprehensive-ui.spec.ts` reads port from env (`process.env.UPCP_PORT_FRONTEND || '3072'`)
- [x] `docs/ENVIRONMENTS.md` references env variables
- [x] `docs/11-docker-and-ports.md` references env variables
- [x] `mcp-setup/` files reference env variables (`UPCP_MCP_URL` in code + docs; example URLs keep stage default `:3070` as documented default)
- [x] `docker compose --env-file .env.dev config` shows correct ports (38080/35432/3072/36380) — same verified for `.env.stage` (38081/35433/3070/36382) and `.env.test` (38082/35434/3071/36383)
- [x] All existing tests still pass (backend 912 passed; frontend 336/336; tsc exit 0)

## Out of scope / follow-up

- `bootstrap_upcp.py` embedded scaffold templates still use legacy
  `UPCP_HTTP_PORT`-style names — internally consistent (its generated
  `.env.example` + compose + docs match each other), renaming is a
  separate scaffold-modernization task, not required by these ACs.
- Internal `expose: "35173"` (vite dev port) is container-internal, not a
  host-published port — intentionally left as-is.

## Implementation Steps

### Step 1: Create env files

Create `.env.dev` and `.env.test`. Extend `.env.stage`.

### Step 2: Update docker-compose files

Replace hardcoded ports with `${UPCP_PORT_*:-default}`.

### Step 3: Update scripts

Read ports from `os.environ.get()` with fallback.

### Step 4: Update e2e tests

Use `process.env.UPCP_PORT_FRONTEND || '3072'`.

### Step 5: Update documentation

Replace port numbers with variable references.

### Step 6: Verify

Run `docker compose config` for each env to validate.
