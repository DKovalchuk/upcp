# DAST — OWASP ZAP baseline/full scan (TASK-0142 / SPEC-0024 Phase 4)

## What runs

`zap_scan.py` drives the ZAP scripted scan (`zap-baseline.py` or
`zap-full-scan.py` from `ghcr.io/zaproxy/zaproxy:stable`) inside the `zap`
service of `docker-compose.test.yml` (profile `security`) against
`http://app:8080` on the test compose network, converts the ZAP JSON report
into the shared `upcp-security-result/v1` schema, and redacts tokens.

```bash
# from repo root, live test stack must be up
.venv/bin/python -m tests.security.dast.zap_scan \
    --out tests/security/results/zap_baseline_<ts>.json \
    [--mode baseline|full] [--report-dir tests/security/reports]
```

Exit codes: `0` = no High/Medium alerts (Low/Informational tolerated),
`1` = findings, `2` = infra failure (scan did not produce a report).

## How (mechanics)

- `docker compose -f docker-compose.test.yml --profile security run --rm -T
  --no-deps -v <report-dir>:/zap/wrk zap sh -c 'zap-baseline.py -t http://app:8080 ...'`
  — the extra `-v` is required because ZAP's scripts refuse file options
  unless `/zap/wrk` exists; `stdin=DEVNULL` is required because
  `docker compose run` hangs on an open stdin after container exit.
- `zap_config.yaml` (mounted by compose at `/zap/config/zap-config.yaml`)
  is consumed host-side by `zap_scan.py` — verified, the ZAP image itself
  has no `ZAP_CONF`/`zap-config` handling. Sections: `daemon` → `-z
  "-config key=value"`, `rules` → ZAP's native tab-separated `-c` file
  (generated per run), `redact` → report post-processing, `scan` → flag
  defaults. See the comments in `zap_config.yaml`.

## Auth

The stable ZAP automation scripts have **no `-H` flag** (their getopt
string is `t:c:u:g:m:n:r:J:w:x:l:hdaijp:sz:P:D:T:IU:`), and bearer-token
auth for a JSON API is not expressible in a ZAP context file without
script add-ons. The scan therefore runs **unauthenticated on the public
surface**: `/docs`, `/openapi.json`, `/health`, `/auth/login`, static app
pages. Authenticated API DAST is a follow-up (needs a context file +
auth script mount). JWTs are never persisted: `redact.patterns` replace
any captured token with `REDACTED` in the JSON/HTML reports and the result.

## Expected duration

Baseline ≈ 3–7 min (add-on install + 1 min spider + passive-scan wait);
wrapper hard-caps at 10 min (600 s). `--mode full` adds active scanning
(default cap 900 s).

## Output artifacts

| File | Content |
|---|---|
| `tests/security/reports/zap_<mode>_<ts>.html` | ZAP traditional HTML report (tracked-ignore: `*.html`) |
| `tests/security/reports/zap_<mode>_<ts>.json` | ZAP traditional JSON report (source for checks) |
| `tests/security/reports/zap_<mode>_<ts>.log` | redacted scan console output (evidence) |
| `tests/security/reports/zap.yaml` | last generated Automation-Framework plan (ZAP copies it to `/zap/wrk`) |
| `tests/security/reports/zap_rules_<ts>.conf` | generated `-c` rules file (when `rules:` non-empty) |
| `tests/security/results/zap_<...>.json` | shared result doc `upcp-security-result/v1`, suite `zap` |

One check per ZAP alert: High/Medium → fail (severity high/medium),
Low/Informational → pass (tolerance), plus a "ZAP scan executed" check.
ZAP script exit codes: `0`=pass, `1`=fail-level alerts, `2`=warn-level
alerts, `3`=usage error — the wrapper keys infra success off the JSON
report, not the exit code.

## Rule tuning

`rules:` in `zap_config.yaml` starts empty on purpose — plugin ids are
added only from evidence of a real run (`pluginid` is in every check),
e.g. `10020: IGNORE`. Never guess ids.

## Notes

- Stack contract: `SECURITY_BASE_URL=http://localhost:38082` (host), scan
  target `http://app:8080` (compose network). Never restart the stack.
- SAST (bandit/pip-audit/trivy) lives in CI — out of scope here.
