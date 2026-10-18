# TASK-0142 — SPEC-0024 Phase 4: Security — ZAP DAST, API fuzzer, auth tests, Kali pentest agent

**Milestone:** SPEC-0024 (Test Environment) Phase 4
**Points:** 13
**Spec:** `specs/SPEC-0024-test-environment.md` (Security: SAST + DAST
baseline/scheduled + pentest agent in Kali + ACP, frontend security as
separate suite). Design doc `docs/planning/TEST_ENVIRONMENT_SPEC.md` is
MISSING (never in git) — design decisions made task-level (mini-spec
below). SAST half already exists in CI (bandit/pip-audit/npm-audit/trivy).
**Status:** DONE (closed 2026-10-18)

## Mini-spec (design decisions)

- Suite layout mirrors `tests/chaos/` + `tests/performance/`: `runner.py`
  (`--profile/--suite/--list/--report/--host`), config YAML, `results/`
  (JSON, gitignored), `reports/` (markdown tracked, machine artifacts
  ignored), README, requirements.
- Target: `SECURITY_BASE_URL` (default `http://localhost:38082`), auth via
  `PERF_EMAIL`/`PERF_PASSWORD` → cached Bearer JWT (chaos/perf conventions).
- Shared result contract `upcp-security-result/v1` in
  `tests/security/common.py`: one JSON per suite
  (`{suite, target, checks[], findings[], summary}`); runner aggregates
  into `reports/security_<ts>.md`.
- DAST: ZAP scripted baseline on the `upcp-test` network against
  `http://app:8080` (public surface — stable scripts have no `-H` flag;
  auth-injection deferred, see Deviations).
- Kali: `Dockerfile.kali` (kalilinux/kali-rolling, non-root, minimal
  toolset) + agent scripts run on container start; host wrapper
  `kali_scan.py` converts container report to the shared schema.
- Authz suite: pytest integration tests vs LIVE stack (auth ON),
  runner invokes `pytest -o addopts=`; result JSON via conftest plugin
  keyed on `SECURITY_RESULT_OUT`.

## AC (verified against real runs — evidence inline)

- [x] ZAP DAST baseline scan against test app → report artifact —
      **2 real runs × exit 0**; artifacts
      `tests/security/reports/zap_baseline_20261018-{113020,114755}.{html,json,log}`
      + result JSONs in `results/`; 0 High/Medium, 1 info alert
- [x] API fuzzer scenario suite (auth bypass, injection, malformed) —
      **55/55 checks, exit 0** vs fixed live stack (auth_bypass 24,
      injection 16, malformed 15); 12 hermetic unit tests pass; exit 2
      on dead target verified
- [x] Auth/RBAC security test suite (automated, pytest-compatible) —
      **52 passed, 3 xfail (=documented findings), 1 skipped, exit 0**;
      result JSON plugin + junitxml via runner contract
- [x] Kali pentest agent: image builds, agent runs → findings report —
      `docker compose … build kali` exit 0; **2 real runs × exit 0**
      (`reports/kali_20261018-*.md/json`); ACP approach documented in
      `tests/security/kali/README.md`
- [x] Reports actionable (markdown + JSON, schema documented) —
      runner reports `reports/security_20261018_{093224,093329}.md`,
      schema `upcp-security-result/v1` documented in README/common.py —
      **Grafana ingestion deferred to Phase 5 (deviation below)**
- [x] `runner.py --profile baseline --report` and `--profile full
      --report` green end-to-end — **both exit 0** (final runs
      2026-10-18 09:32/09:33 UTC)

### Bonus AC (found → fixed with TDD, approved by Dmitry mid-task)

- [x] fuzz findings fixed: 500 on NUL byte + 500 on unicode/symbol-only
      project name — red **5 failed** → green **19 passed**
      (`test_project_crud.py` regressions); fixes: NUL validator in
      `ProjectCreate/Update`, deterministic fallback slug in
      `slugify()` (affects projects/structure/delivery uniformly)
- [x] auth commit-after-response race fixed — probe **2/40 rows
      uncommitted at receipt → 0/40 after fix**; red **5 failed** →
      green **5 passed** (`test_auth_commit_before_respond.py`,
      two-independent-connection visibility tests for
      login/setup/refresh/logout/change_password); explicit
      `commit-before-respond` in all 5 `AuthService` success paths

## Evidence

**Security suite (final, live stack):**
- baseline: exit **0** — authz 52/55 (+3 xfail-findings), fuzz 55/55,
  zap 2/2 → `tests/security/reports/security_20261018_093224.md`
- full: exit **0** — + kali 8/10 (2 findings < high/critical by
  contract) → `tests/security/reports/security_20261018_093329.md`
- fuzz post-fix: 55/55 (was 53/55 with 2×500), authz stable over 8+
  executions (flake root-caused + fixed), ZAP/Kali 2 runs each

**Backend:**
- full suite **972 passed** exit 0 (967 + 5 auth-commit regressions;
  +5 project regressions were in the 967)
- `ruff check` + `ruff format --check` clean (backend + tests/security),
  `mypy` clean on changed files (CI gate = `mypy backend/app` ✓)
- live probe `/tmp/probe_auth_commit.py`: pre-fix 2/40 uncommitted,
  post-fix **0/40**; immediate-refresh 401s **0/40**

**Infra:** `ghcr.io/zaproxy/zaproxy:stable` pulled; `upcp-test-kali`
built; `docker-compose.test.yml` untouched (dangling `tests/security/*`
mounts now all exist).

**Env gotcha hit & fixed:** rebuild without `--env-file .env.test` made
compose pull root `.env` dev ports → port conflict → app/db stuck
`Created`; recovered with `--env-file .env.test up -d` (data intact).

## Findings (product — none silently waived)

1. **RBAC unenforced** (xfail high): roles/permissions seeded in DB but
   no runtime guard; Member PATCH → 404 not 403; all `/api/v1` domain
   routes are "any authenticated user". → spec-level decision needed.
2. **Deleted/nonexistent-user JWT accepted** (xfail high): AuthMiddleware
   verifies only signature; no `get_current_user` dependency on many
   domain routes → token lives until exp (15 min) after user deletion.
3. **Access token alive after logout** (xfail medium): stateless, no
   denylist — only refresh is revoked (by design? → confirm).
4. **Doc-code mismatch**: `docs/security/auth-rbac.md` documents logout
   at `/api/v1/auth/logout` (actual `/auth/logout`) and claims "all
   tokens revoked on password change" (code does not revoke refresh).
5. **`PUBLIC_PATHS` dead route**: `/mcp/health` listed → 404.
6. ZAP info: storable/cacheable content on backend 404s (`/`,
   `/robots.txt`, `/sitemap.xml`).
7. Kali: `x-request-id` uncommon header (nikto, medium advisory);
   `Server: uvicorn` banner (info). nmap: only 8080/Uvicorn; sqlmap:
   not injectable; CSP/HSTS/XFO/XCTO present.

## Deviations (AC → deviation with reason)

- **Grafana-visualizable** → JSON schema `upcp-security-result/v1`
  documented as the integration point; actual Grafana ingestion belongs
  to the Phase 5 aggregate reporter (TASK-0143) — no security dashboard
  added here.
- **ZAP authenticated scan** → unauthenticated baseline only: stable
  image scripts lack `-H`; `/openapi.json`, `/docs`, `/auth/login` are
  public so the baseline covers the public surface. Auth-injection
  (JWT header) noted as future work in `tests/security/dast/README.md`.
- **`zap_config.yaml` mount**: ZAP image ignores `ZAP_CONF`; host wrapper
  `zap_scan.py` translates the YAML (daemon/rules/redact/scan) into
  `-config`/`-c` flags + post-scan redaction — documented in dast README.
- **Lockout test skipped** in authz suite (mutates shared
  `admin@example.com`; `/auth/setup` single-use) — covered by
  `backend/tests/test_auth_endpoints.py` unit suite instead.

## Multi-factor analysis (AGENTS §12)

- **Requirements:** all AC + bonus ACs verified against real runs above.
- **Architecture:** mirrors established chaos/perf suite patterns; no
  DDD boundary changes; fixes live at schema/service layer of their own
  contexts (projects/shared/identity).
- **Security:** fixes reduce attack surface (2 DoS-500s, 1 auth race);
  real gaps kept visible as xfail + Findings list rather than weakened
  assertions; no secrets in code/reports (token-redaction sweep clean).
- **Reliability:** previously-flaky gate root-caused (probe evidence)
  and fixed, not retried-around; runner exit-code contract (0/1/2)
  tested including dead-target path.
- **Performance:** ZAP baseline ~35 s, Kali ~35 s container time; no
  app-code hot-path changes (commit adds one round-trip per auth call).
- **Tests:** red→green for both bug classes; fuzz 12 unit tests; authz
  integration 56 tests; suite re-runs stable.
- **Documentation:** 5 READMEs (suite, authz, fuzz, dast, kali) +
  task/PROJECT_STATUS updated.

## Follow-ups (for Queued)

- RBAC enforcement + deleted-user JWT + logout denylist decisions
  (findings 1-3) → needs spec; `docs/security/auth-rbac.md` rewrite
  (finding 4); `/mcp/health` dead path (finding 5).
- ZAP authenticated baseline (after `-H` or API-driven scan research).
- Security results → Grafana (Phase 5 / TASK-0143).
