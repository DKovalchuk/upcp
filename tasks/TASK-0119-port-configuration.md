# TASK-0119 — Externalize Port Configuration

**Milestone:** M20
**Sprint:** S22.5
**Points:** 3
**Spec:** SPEC-0024
**Status:** IN_PROGRESS

## Objective

Replace hardcoded ports with environment-based configuration via `.env.*` files.

## Acceptance Criteria

- [ ] `.env.dev` exists with all dev port variables
- [ ] `.env.test` exists with all test port variables
- [ ] `.env.stage` extended with port variables (preserves existing secrets)
- [ ] `docker-compose.yml` uses `${UPCP_PORT_*:-default}` for all ports
- [ ] `docker-compose.test.yml` uses `${UPCP_PORT_*:-default}` for all ports
- [ ] `docker-compose.stage.yml` uses `${UPCP_PORT_*:-default}` for all ports
- [ ] `scripts/populate_upcp_v2.py` reads port from env
- [ ] `scripts/populate_m17_m20.py` reads port from env
- [ ] `frontend/e2e/comprehensive-ui.spec.ts` reads port from env (or const with default)
- [ ] `docs/ENVIRONMENTS.md` references env variables
- [ ] `docs/11-docker-and-ports.md` references env variables
- [ ] `mcp-setup/` files reference env variables
- [ ] `docker compose --env-file .env.dev config` shows correct ports
- [ ] All existing tests still pass

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
