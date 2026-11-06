# Environments — Model and Topology (SPEC-0024 Phase 5, TASK-0143)

> Project: UPCP | Compose projects: `upcp`, `upcp-dev`, `upcp-stage`, `upcp-test`, `upcp-test-ci` | Updated: 2026-10-18

UPCP runs every environment as a Docker Compose project with a **unique
project name, port namespace, and data directory**, so several stacks can
coexist on the shared runner host without stealing each other's ports or
database files. All published ports bind to `127.0.0.1` only.

## 1. Environment matrix

| Env | Role | Compose project · file | Ports FE / BE / PG / Redis | Deployed by | URL |
|-----|------|------------------------|---------------------------|-------------|-----|
| dev (local) | developer machine, bind-mounted source | `upcp` · `docker-compose.yml` | 3072 / 38080 / 35432 / 36380 | developer, manual `docker compose up -d` | http://localhost:3072 |
| dev (CI) | fresh `develop`, clickable | `upcp-dev` · `docker-compose.stage.yml` | 3073 / 38083 / 35435 / 36384 | `deploy:dev` — automatic on push to `develop` | http://localhost:3073 |
| test (local) | persistent suite runs | `upcp-test` · `docker-compose.test.yml` + `--env-file .env.test` | 3071 / 38082 / 35434 / 36383 | developer, manual | http://localhost:3071 |
| test (CI gate) | ephemeral quality-gate stack | `upcp-test-ci` · `docker-compose.test.yml` + `--env-file .env.ci` | 3074 / 38084 / 35436 / 36386 | `quality:gate` — one per pipeline, `down` in `after_script` | http://localhost:3074 |
| stage | pre-prod acceptance | `upcp-stage` · `docker-compose.stage.yml` | 3070 / 38081 / 35433 / 36382 | `deploy:stage` — **manual** on `main` (`stop:stage` to stop) | http://localhost:3070 |
| prod | — | **not present in this repository** (see §4) | — | — | — |

Notes:

- `dev (CI)` deliberately reuses the *stage* compose file under its own
  project and ports (`COMPOSE_PROJECT_NAME=upcp-dev` + `UPCP_PORT_*` job
  variables), so `deploy:dev` and `deploy:stage` never overwrite each
  other's containers or data.
- `deploy:dev` / `deploy:stage` declare a GitLab `environment:` (`dev` /
  `stage`) with an honest `environment.url` — dev → `:3073`, stage →
  `:3070`; both were a stale `:3080` until TASK-0143 corrected them.
- The gate stack declares **no** `environment:` — it is a per-pipeline
  fixture, not a live environment.
- `.env.ci` also reserves non-overlapping profile ports for the gate
  (ZAP 38096, Kali 38097, Locust 38095, observability 39093 / 33003 /
  3103 / 3203 / 4323 / 4324); its header comment explains the full
  port-namespace rationale.

## 2. Data directories (persistence)

| Env | Postgres | Redis | Where the paths come from |
|-----|----------|-------|---------------------------|
| dev (local) | `./data/postgres` | `./data/redis` | hard-coded in `docker-compose.yml` |
| dev (CI) | `./data/postgres-dev` | `./data/redis-dev` | `UPCP_DATA_*` job variables in `deploy:dev` |
| test (local) | `./data/postgres-test` | `./data/redis-test` | defaults in `docker-compose.test.yml` |
| test (CI gate) | `./data/ci-postgres` | `./data/ci-redis` | `.env.ci` — inside the invoking workspace (`data/` is gitignored): scratch postgres/redis per run, cleaned with the workspace |
| stage | `./data/postgres-stage` | `./data/redis-stage` | defaults in `docker-compose.stage.yml` |

`UPCP_DATA_POSTGRES` / `UPCP_DATA_REDIS` are environment-driven precisely
so `deploy:dev` (own directories) and `deploy:stage` (compose defaults)
can run the **same** compose file against fully separate database state —
the dev/stage data split of TASK-0143.

## 3. Images and tags

- Registry: `registry.gitlab.local:5050/dmitry.kovalchuk/upcp/{backend,frontend}`.
- Floating tags: `:dev` (pushed from `develop`), `:stage` (pushed from
  `main`); per-commit SHA tags are pushed too and pruned locally — the
  registry keeps the last 10 SHA tags per repo and never deletes the
  floating tags (retention rules: `ops/ci-retention.md`).
- `deploy:dev` pulls `:dev`, `deploy:stage` pulls `:stage`; both export
  `UPCP_BACKEND_IMAGE` / `UPCP_FRONTEND_IMAGE` so compose runs exactly the
  image the pipeline just built.
- The gate stack builds `app` / `frontend` / `nginx` **inside the job from
  the checked-out commit** — it never pulls registry images, so a gate run
  always tests the code that triggered it.
- Local stacks (`upcp`, `upcp-test`) build locally via `docker compose build`.

## 4. History: dev/stage split (TASK-0143, 2026-10-18)

Until TASK-0143, `deploy:dev` and `deploy:stage` both ran
`docker-compose.stage.yml` under the **same** `upcp-stage` compose project
— whichever job ran last owned the stack — and both `environment.url`s
pointed at a stale `:3080`. TASK-0143 gave `deploy:dev` its own project
(`upcp-dev`), port set, data directories, `resource_group`, and an honest
URL; `deploy:stage` is now the sole owner of `upcp-stage`.

## 5. Production — future model only

There is **no** production environment in this repository: no prod compose
file, no prod env file, no prod CI jobs, no `:prod` registry tags (checked
against the compose files, `.env.*` files, and `.gitlab-ci.yml`). The
agreed future model, documented here only: a separate host (not the
runner laptop), `:prod` registry tags, and a manual deploy behind an
approval gate — out of scope until a real host exists.

## 6. Running a stack manually

Local test stack (persistent, for manual suite runs):

```bash
docker compose -f docker-compose.test.yml --env-file .env.test up -d
docker compose -f docker-compose.test.yml --env-file .env.test \
  --profile tools run --rm seeder
```

**`--env-file .env.test` is mandatory.** Without it, compose substitutes
variables from the root `.env`, which carries the **dev** ports
(`UPCP_PORT_BACKEND=38080`, `UPCP_PORT_POSTGRES=35432`): the test stack
would bind the dev stack's backend/postgres ports, and every suite default
(`http://localhost:38082`, …) would point at nothing. `--env-file`
replaces `.env` for interpolation — `.env.ci` uses the same mechanism for
the gate stack (`COMPOSE_PROJECT_NAME=upcp-test-ci docker compose
--env-file .env.ci …`; see the header of `.env.ci` for the rationale).

Suite commands live in `tests/*/README.md`; running the full gate locally
is described in `ops/ci-quality-gates.md` §6.
