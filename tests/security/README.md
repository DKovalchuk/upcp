# UPCP Security Suite — SPEC-0024 Phase 4 (TASK-0142)

Security quality gate for the live test stack: auth/RBAC integration
tests, API fuzzer, ZAP DAST baseline, Kali pentest agent.

SAST (bandit, pip-audit, npm audit, trivy) already runs in CI — see
`.gitlab-ci.yml` (`backend:security`, `dependency:scan:*`,
`container:scan:backend`). This suite covers the DAST/runtime half.

## Quick start

```bash
# 1. Test stack up + seeded (once)
docker compose -f docker-compose.test.yml up -d
docker compose -f docker-compose.test.yml --profile tools run --rm seeder

# 2. Host-side deps (venv)
pip install -r tests/security/requirements.txt

# 3. Run
.venv/bin/python tests/security/runner.py --list
.venv/bin/python tests/security/runner.py --profile baseline --report
.venv/bin/python tests/security/runner.py --profile full --report   # + Kali
```

Profiles (config/security_profiles.yaml):

| Profile   | Suites                    | Notes |
|-----------|---------------------------|-------|
| `baseline`| authz, fuzz, zap          | fast gate, minutes |
| `full`    | baseline + kali           | + image build + nmap/nikto/sqlmap |

Exit codes: `0` all passed · `1` findings/failed checks · `2` infra
(target down, suite produced no result, container failure).

## Layout

```text
tests/security/
├── runner.py                 # profile orchestration + report
├── common.py                 # shared contract: login, check, summarize (schema upcp-security-result/v1)
├── config/security_profiles.yaml
├── authz/                    # pytest auth/RBAC integration suite (live stack, auth ON)
├── fuzz/                     # API fuzzer: auth bypass, injection, malformed input
├── dast/                     # ZAP config + scan wrapper
├── kali/                     # Kali pentest agent scripts (+ Dockerfile.kali at repo root)
├── results/                  # *.json (gitignored), *.xml (gitignored)
└── reports/                  # *.md tracked; *.html/ZAP artifacts gitignored
```

## Conventions

- Target: `SECURITY_BASE_URL` (default `http://localhost:38082`).
- Auth: `PERF_EMAIL` / `PERF_PASSWORD` → cached JWT (same as chaos/perf).
- Every suite emits exactly one result JSON, schema
  `upcp-security-result/v1` (`{suite, target, checks[], findings[],
  summary}`) — the runner aggregates those into `reports/security_<ts>.md`.
- Reports are actionable: markdown for humans, JSON for tooling.

## Known limitations (recorded in TASK-0142)

- ZAP/Kali need the `security` compose profile; they are **not** wired
  into CI yet (Phase 5 — TASK-0143 — owns CI/CD triggers).
- Grafana ingestion of security results is deferred to the Phase 5
  aggregate reporter; the JSON schema is the integration point.
