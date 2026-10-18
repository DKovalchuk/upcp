# CI Quality Gates — Running, Interpreting, Versioning (SPEC-0024 Phase 5, TASK-0143)

> Project: UPCP | Pipeline: `.gitlab-ci.yml` (`quality:gate`) | Updated: 2026-10-18

The quality gate runs the heavy suites (e2e, chaos, security, performance)
against an ephemeral hermetic stack (`upcp-test-ci`, see
`ops/environments.md`) and aggregates everything into one report. Stage
ordering: `lint → test → quality → build → deploy` — the pipeline stops at
the first failed stage.

## 1. What runs where

| Tier | Trigger | Content |
|------|---------|---------|
| MR | `merge_request_event` | Unchanged: lint / typecheck / unit (pytest, vitest) / migrations / SAST (bandit, pip-audit, npm audit, trivy). No heavy stacks — `quality:gate` does **not** run on MRs (its rules are `develop` + `schedule` only). |
| develop | push to `develop` | `quality:gate`, `QUALITY_PROFILE=quick`: e2e (root + frontend), chaos quick, security baseline, perf smoke — ephemeral stack. Sits before `build`, so once Phase B makes it a hard gate it blocks deploys. |
| Nightly | pipeline schedule on `develop` (~03:00) | `quality:gate`, `QUALITY_PROFILE=full`: chaos full, security full (ZAP + Kali), perf load, e2e. |
| On demand | — | No dedicated manual job today: run the schedule from the GitLab UI, or run the suites locally (§6). |

Job shape: `stage: quality`, image `python:3.12-slim` (docker CLI +
compose plugin installed in `before_script`), `needs: backend:test,
backend:migrations`, `timeout: 1h30`, `resource_group: quality-gate`.

## 2. Failure policy (two phases)

- **Phase A (current):** `quality:gate` runs with `allow_failure: true` —
  first observations in CI; a red gate does not fail the pipeline yet.
- **Phase B (follow-up commit, TASK-0143):** after **≥2 green develop +
  ≥1 green schedule** runs are observed, verified-green jobs flip to a
  hard gate. Not implemented yet — until then Phase A stands.
- **`perf load` never gates**, permanently: the nightly 50-user load
  profile is a known honest-red SLO (TASK-0140 throughput findings) — it
  is report-only by construction (see exit logic below), and stays
  `allow_failure` even after the Phase B flip.

What counts toward the gate exit (the script's RC logic):

- **always:** root e2e, frontend e2e, chaos, security;
- **quick profile only:** perf smoke (`RC_PERF` joins the max only when
  `QUALITY_PROFILE=quick` — smoke must pass; on `full` perf is excluded).

## 3. What `quality:gate` does, step by step

1. **Reporter unit tests + config sanity** — `pytest tests/quality_gate`;
   `docker compose --env-file .env.ci config --quiet`.
2. **Ephemeral stack from this commit** — `build app frontend nginx`;
   `up -d db redis app frontend nginx`; health-wait loop (40 × 3 s)
   probing `/health` **inside** the app container.
3. **Join the gate network** — `docker network connect
   upcp-test-ci_default $(cat /etc/hostname)`: the job container sits on
   the runner's `gitlab-local_default` network and cannot reach host
   loopback (the deploy-probe incident), so it joins the gate network,
   re-checks `http://app:8080/health`, then seeds via
   `--profile tools run --rm seeder` (clean slate: the seeder drops and
   recreates the DB by default).
4. **Suites** — profiles chosen by `QUALITY_PROFILE` (`quick` → chaos
   quick / security baseline / perf smoke; `full` → chaos full / security
   full / perf load). Root e2e runs with `E2E_API_BASE=http://app:8080`
   (nginx does not proxy `/openapi.json`, `/metrics`); frontend e2e runs
   with `PLAYWRIGHT_BASE_URL=http://localhost:5173` (its own vite) and
   `VITE_API_URL=http://app:8080`. Each suite's RC is captured with
   `|| RC_X=$?` so one failure never skips the rest.
5. **Aggregate + verdict** — `tests/quality_gate/aggregate.py
   --results-root tests --out-dir .` writes `quality-report.{md,json}`
   (always runs), then `GATE = max(RC_e2e, RC_e2e_fe, RC_chaos,
   RC_sec)` + `RC_perf` on quick only; the job exits with `GATE`.
6. **Teardown** (`after_script`, runs even on failure) —
   `docker compose --env-file .env.ci --profile tools --profile ci
   --profile security down -v --remove-orphans`.

`COMPOSE_FILE=docker-compose.test.yml` and
`COMPOSE_PROJECT_NAME=upcp-test-ci` are job variables: without them any
compose invocation would fall back to `docker-compose.yml` (the dev
stack) from the repo root.

## 4. Artifacts and results versioning

CI artifacts (`when: always`, `expire_in: 30 days`): `quality-report.md`,
`quality-report.json`, `tests/{chaos,security,performance}/results/`, and
`tests/*/reports/*.md`.

Versioning convention:

| Data | Where it lives | Tracked in git? |
|------|----------------|-----------------|
| Suite markdown reports `tests/*/reports/*.md` | git + CI artifacts | **yes** — the durable history |
| Perf baselines `results/baseline.json`, `results/trend_history.json` | git | **yes** — the tracked exception; regression comparison needs them |
| Raw suite JSON/CSV/XML in `results/` | local + CI artifacts (30 d) | no (gitignored) |
| `quality-report.{md,json}` (repo root) | CI artifact | no (gitignored) |

This deviates from SPEC-0024's "JSON results in repo" decision — raw JSON
is ephemeral (CI artifact), markdown is the versioned record; recorded as
a deviation in TASK-0143.

## 5. Interpreting `quality-report.md`

- **Summary table** — `Suite | Checks | Passed | Failed | Findings |
  Status` (`status: ok | missing`; a `missing` suite means its runner
  never produced a result — check §3 step 4).
- **Findings** — severity-sorted security findings (`[CRITICAL]` …
  `[INFO]`), chaos failures with their MTTR, perf-vs-baseline deviation
  count.
- **Regression vs baseline** — `Metric | Baseline | Current | Change`
  table: **informational only, no automatic thresholds — a human decides**
  (SPEC-0024 decision). "No baseline" means first run in a new
  environment, not a failure.
- **Exit codes** — the gate aggregates suite RCs as a max:

| Component | 0 | 1 | 2 |
|-----------|---|---|---|
| security runner | all checks passed | findings / failed checks | infra (target down, no result, container failure) |
| chaos runner | all experiments passed | any experiment failed, or usage error | — |
| performance runner | scenarios completed | profile/scenario/health failure | — |
| aggregate.py | report written (findings do not affect it) | — | internal error |

The gate verdict is `max(e2e, e2e_fe, chaos, security)` plus `perf` on the
quick profile only (§2).

## 6. Running the same gate locally

Host prerequisites: python deps for the suites (`pip install -r
tests/{security,chaos,performance}/requirements.txt locust`) and, for
host-run e2e, `npm ci` + Playwright browsers.

```bash
export COMPOSE_FILE=docker-compose.test.yml
export COMPOSE_PROJECT_NAME=upcp-test-ci

docker compose --env-file .env.ci config --quiet
docker compose --env-file .env.ci build app frontend nginx
docker compose --env-file .env.ci up -d db redis app frontend nginx
# wait for health (same probe as CI):
docker compose --env-file .env.ci exec -T app python -c \
  "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=3)"
docker compose --env-file .env.ci --profile tools run --rm seeder

# suites from the host — localhost env (see the two sets below):
python tests/chaos/runner.py        --profile quick    --report
python tests/security/runner.py     --profile baseline --report
python tests/performance/runner.py  --profile smoke    --report

# aggregate + teardown:
python tests/quality_gate/aggregate.py --results-root tests --out-dir . --profile quick
docker compose --env-file .env.ci --profile tools --profile ci --profile security \
  down -v --remove-orphans
```

Why `--env-file .env.ci` is mandatory: without it, compose interpolates
from the root `.env` (dev ports) — see `ops/environments.md` §6.

Env sets — CI suites run **inside** the gate network (the job joined it,
§3.3); local suites run on the host and use published ports:

| Variable | CI (in-network) | Local (host) |
|----------|-----------------|--------------|
| `SECURITY_BASE_URL` | `http://app:8080` | `http://localhost:38084` |
| `CHAOS_BASE_URL` | `http://app:8080` | `http://localhost:38084` |
| `LOCUST_HOST` | `http://app:8080` | `http://localhost:38084` |
| Root e2e base URL (`E2E_BASE_URL` → `PLAYWRIGHT_BASE_URL`) | `http://nginx` | `http://localhost:3074` |
| Root e2e direct API (`E2E_API_BASE`) | `http://app:8080` | `http://localhost:38084` |
| Frontend e2e vite origin (`PLAYWRIGHT_BASE_URL`) | `http://localhost:5173` | `http://localhost:5173` |
| Frontend e2e proxy target (`VITE_API_URL`) | `http://app:8080` | `http://localhost:38084` |
| `CHAOS_COMPOSE_PROJECT` | `upcp-test-ci` | `upcp-test-ci` |
| `SECURITY_DB_HOST` / `SECURITY_DB_PORT` (authz DB fixture) | `db:5432` | `127.0.0.1:35436` |

Notes for local runs:

- **Precedence gotcha:** compose lets OS environment beat `--env-file` —
  if your shell inherited root-`.env` vars (`UPCP_PORT_POSTGRES=35432`
  etc.), `--env-file .env.ci` silently resolves to dev ports and the
  stack collides with the dev environment. Prefix local commands with
  `set -a; . ./.env.ci; set +a` — sourcing puts the correct values into
  OS env so they win (this recovered a broken half-stack on 2026-10-18).
- **Don't overlap a CI gate:** CI gate teardown removes the whole
  `upcp-test-ci` project on the shared daemon — a local rehearsal stack
  of the same name is torn down with it. Run the local gate only while
  no CI `quality:gate` job is in flight.
- The frontend vite dev server is `localhost:5173` in **both** columns: in
  CI it starts inside the e2e container (Playwright `webServer`), locally
  on your host.
- e2e may also run through the gate network exactly as CI does — the e2e
  container joins it, so the CI commands work verbatim:
  `docker compose --env-file .env.ci --profile ci run --rm -e
  E2E_API_BASE=http://app:8080 e2e sh -c "npm ci --no-audit --no-fund &&
  npx playwright test"`.
- `zap`/`kali` (security profile) always scan the in-network target
  `http://app:8080` from `tests/security/dast/zap_config.yaml` — keep
  `COMPOSE_PROJECT_NAME=upcp-test-ci` exported so they join the gate
  network instead of the local `upcp-test` stack.

## 7. Nightly schedule

`workflow.rules` accepts `$CI_PIPELINE_SOURCE == "schedule"` and the
`quality:gate` rule maps schedule → `QUALITY_PROFILE=full`. The schedule
is a project setting, not part of `.gitlab-ci.yml` — it exists as
pipeline schedule **id 1** (branch `develop`, daily **03:00
Europe/Moscow**, `QUALITY_PROFILE=full`), created 2026-10-18 via the
pipeline-schedules API. Trigger it on demand with
`POST /api/v4/projects/:id/pipeline_schedules/1/play` (or the ▶ button
in Settings → CI/CD → Schedules) — that manual trigger doubles as the
"manual tier" of §1.
