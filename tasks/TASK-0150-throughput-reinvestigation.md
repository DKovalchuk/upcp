# TASK-0150 — 50-user throughput reinvestigation (TASK-0140 finding #2)

**Spec:** SPEC-0024 Phase 2 finding (TASK-0140 #2) — Spec Flow: investigation → evidence → conclusion
**Milestone:** Этап 1 perf-расследования
**Points:** 3
**Status:** DONE (closed 2026-10-24)

## Investigation (2026-10-24)

Finding #2 (TASK-0140): "Throughput collapse at 50 users — 5.1 req/s,
p50 1.1s, p90 34s; suspects: anyio threadpool saturation (default 40) and
finding #1." Re-measured the canonical `load` profile (50 users, 5m,
scenario_mixed) against the test stack in three conditions:

| metric | TASK-0140 (old code) | stale image (run1) | **rebuilt image w/ TASK-0149 (run2)** |
|---|---|---|---|
| requests / failed | 1521 / 119 (7.82%) | 5611 / 0 | **14003 / 0 (0.00%)** |
| throughput | 5.1 rps | 18.7 rps | **46.7 rps (×9.2)** |
| p50 / p90 / p95 / p99 | 1.1s / 34s / ceiling | 410ms / 1.2s / 16s / 22s | **120ms / 430ms / 550ms / 1000ms** |
| `/dashboard/stats` p50 | 117/119 timeouts | **16000ms** | **170ms** (max 930ms) |
| SLO verdict | 1114/1491 | 2103/2106 | **2154/2154 (100%)** |

### Conclusions

1. **Finding #2 = symptom of finding #1 (closed by TASK-0149).**
   The N+1 `/dashboard/stats` (up-to-60s client-ceiling timeouts) starved
   the closed-loop load generation: with the fix live (verified in-container
   via `hasattr(..., "get_average_health")`), failures 7.82% → 0%, throughput
   5.1 → 46.7 rps, dashboard/stats 16s-median-under-load → 170ms.
2. **anyio-threadpool hypothesis NOT confirmed** — no saturation signature
   (0 failures, p99 1s at 46.7 rps; test env pool 40+20 per
   docker-compose.test.yml). No production change required → finding #2
   closes without code.
3. **Stale-image trap (run1 evidence kept):** `docker-compose.test.yml`
   app BAKES the image (no bind-mount) — a load run before `--build`
   measured the OLD code (dashboard/stats p50 16s under load = live N+1).
   Fix: `up -d --build` + in-container symbol check after every code change.

### Residual notes (queue, non-blocking)

- Throughput SLO ">50 rps under normal load" vs scenario offered load ≈49
  rps (50 users × wait 0.3–1.5s): achieved 46.7 ≈ 95% of offered — the
  target is only reachable via higher efficiency or a bigger profile
  (stress: 200 users); SLO-design note for the perf gate.
- CI containers (`upcp-test-ci-*`, separate ports/data-dir) ran
  concurrently during run2 — minor contention caveat, results far from
  thresholds.
- `/auth/login` p50 400ms (bcrypt) and agent-read p50 ~500ms under load —
  soft spots, below SLO targets; watch in future trends.

## Acceptance Criteria (verified 2026-10-24)

- [x] Re-measure under load with the TASK-0149 fix actually live
      (`fix_in_image: True` check after `--build`)
- [x] Attribution documented with three-way numbers; threadpool hypothesis
      assessed (not binding) — no prod change needed
- [x] SLO verdict: **2154/2154** (load profile: error ≤2%, p95 ≤1s,
      p99 ≤2s — all met)
- [x] Post-fix baseline saved (run2 CSV → `results/baseline.json`),
      `trend_history.json` carries both runs; reports committed
- [x] Test stack torn down (`compose down`, env lifecycle)
- [x] PROJECT_STATUS updated

## Evidence

- run2 report: `tests/performance/reports/load_20261024_232349.md`
  (14003 req, 0 fail, 46.7 rps, SLO 2154/2154)
- run1 report (stale-image trap): `tests/performance/reports/load_20261024_231404.md`
  (dashboard/stats p50 16000ms — old N+1 code under load)
- baseline.json refreshed from run2; CSVs gitignored by design

## Env gotchas (recorded)

1. **Test compose bakes the image** — always `up -d --build` after code
   changes; verify with an in-container `hasattr` check.
2. **`docker compose run` config-drift:** running seeder WITHOUT the same
   explicit `UPCP_PORT_*` env recreated db/app to shell-port values
   (app 38082→38080) → host health-check broke. Export the override vars
   for the ENTIRE compose flow.
3. PEP 668 blocks system pip → locust/PyYAML installed into `.venv`;
   run the runner via `.venv/bin/python`.
4. This compose version rejects `run --profile` flag form → `run --rm seeder`.

## Files

| File | Action |
|------|--------|
| `tasks/TASK-0150-throughput-reinvestigation.md` | CREATE |
| `tests/performance/results/baseline.json` | MODIFY — post-fix reference (run2) |
| `tests/performance/results/trend_history.json` | MODIFY — both runs appended |
| `tests/performance/reports/load_20261024_231404.md` | CREATE — stale-image run (evidence) |
| `tests/performance/reports/load_20261024_232349.md` | CREATE — true post-fix verification |
