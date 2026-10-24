# TASK-0152 — Grafana provisioning dirs + admin password truth (TASK-0140 finding)

**Spec:** SPEC-0024 observability follow-up — finding: `dashboards/production` missing-dir walk error + admin password doc mismatch (`admin_change_me` volume-init vs `.env.test` `admin_test`)
**Milestone:** Этап 1 perf-расследования
**Points:** 3
**Status:** DONE (closed 2026-10-25)

## Investigation (2026-10-24/25, empirical)

**1. Missing-dir walk error — reproduced then fixed:**
- Provisioning yml defines two providers: `UPCUP Test` →
  `/etc/grafana/dashboards/test` (exists) and `UPCUP Production` →
  `/etc/grafana/dashboards/production` (**host dir never existed**);
- live grafana logs (broken state): `Cannot read directory` /
  `Failed to read content of symlinked path` /
  `failed to walk provisioned dashboards` —
  `stat /etc/grafana/dashboards/production: no such file or directory`,
  repeating every 30s (updateInterval). Same class errors for
  `provisioning/plugins` and `provisioning/alerting` (referenced by
  Grafana defaults, never created).
- Fix: `.gitkeep` placeholders in all three dirs → restart → **startup
  dir-error count = 0** (fresh volume start also 0).

**2. Admin password "mismatch" — root cause is compose env precedence:**
- Existing volume: `admin_change_me` → 200, `admin_test` → 401.
- `SHELL_GRAFANA_ADMIN_PASSWORD=admin_change_me` — the shell carries
  the root-`.env` value (launcher dotEnv); compose interpolation order
  is **process env > `--env-file` > default**, so `.env.test`'s
  `admin_test` never reaches the container → volume seeded with
  `admin_change_me` (the "volume initialized from root .env" finding).
- Volume reset WITHOUT unsetting the leak → seeds `admin_change_me`
  again (200/401 pair reproduced) — proving the leak, not the volume,
  is decisive.
- Clean env: `env -u GRAFANA_ADMIN_PASSWORD … up -d` + fresh volume →
  **`admin_test` 200 / `admin_change_me` 401** — `.env.test` semantics
  hold when the shell doesn't define the variable.

## Objective

Create the provisioned dashboard dirs (kill the walk error), pin the
paths with a contract test, and make the docs tell the truth about the
init-once password and compose precedence (the actual mismatch
mechanism).

## Acceptance Criteria (verified 2026-10-25)

- [x] **Red first:** `test_grafana_provisioning_dashboard_paths_exist`
      red (production dir missing) → **green 3/3** after `.gitkeep` fix
- [x] Live grafana: walk errors every 30s (broken state, captured) →
      **0 dir errors** after fix (restart + fresh-volume start)
- [x] Password semantics verified both ways: leak-seeded →
      `admin_change_me` 200; clean env + reset → `admin_test` 200
- [x] Docs synced: `docker-compose.md` §2.7 example (wrong var
      `GRAFANA_PASSWORD`/`admin` → `GRAFANA_ADMIN_PASSWORD` + init-once/
      precedence note) and §4 example; `observability-stack.md` §4.2
      (real two-provider yml + existence rule) + new §4.3 Admin access
      (precedence + both probe results + reset); `.env.test` init-once
      comment; `observability-stack.md` §2.1 collector example synced to
      the TASK-0151 `otlphttp/loki` fix (lagging doc-code drift)
- [x] Stack torn down (`compose down`), volume left removed (fresh state)
- [x] ruff check/format clean; PROJECT_STATUS updated

## Evidence

- Contract tests: `1 failed → 3 passed` (TASK-0151 pair stays green)
- Broken-state log capture + post-fix `--since` grep = 0 hits
- Probe matrix: `{admin_test: 401, admin_change_me: 200}` (leak) vs
  `{admin_test: 200, admin_change_me: 401}` (clean env) — docs §4.3
  states exactly this
- `SHELL_GRAFANA_ADMIN_PASSWORD=admin_change_me` — leak source proven

## Deviations (recorded per §7)

1. Fixed the same-class `provisioning/plugins` + `provisioning/alerting`
   missing dirs too (their errors appeared in the very evidence being
   collected — leaving them would make "closed missing-dir findings"
   dishonest); the contract test pins only OUR yml's paths (the other
   two are Grafana defaults).
2. Synced the lagging collector example in `observability-stack.md`
   §2.1 (TASK-0151) inside this task's docs commit — same doc file,
   same docs↔config-sync concern; noted in the commit body.
3. Local volume reset performed (test-stack-only state; dashboards
   re-provision from files) to leave the stack on the `.env.test`
   value.

## Files

| File | Action |
|------|--------|
| `observability/grafana/dashboards/production/.gitkeep` | CREATE (walk fix) |
| `observability/grafana/provisioning/plugins/.gitkeep` | CREATE (same class) |
| `observability/grafana/provisioning/alerting/.gitkeep` | CREATE (same class) |
| `backend/tests/test_observability_configs.py` | MODIFY — paths contract |
| `docs/ops/docker-compose.md` | MODIFY — §2.7/§4 grafana truth |
| `docs/ops/observability-stack.md` | MODIFY — §2.1 sync + §4.2/§4.3 |
| `.env.test` | MODIFY — init-once/precedence comment |
