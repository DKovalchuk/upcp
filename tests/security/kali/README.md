# Kali pentest agent (TASK-0142 / SPEC-0024 Phase 4)

## What runs

`Dockerfile.kali` (repo root, `kalilinux/kali-rolling` + minimal toolset:
nmap, nikto, sqlmap, curl, python3 — non-root user `kali`, uid 1000) runs
the mounted agent `run.sh` on container start:

| Check | Command | Budget |
|---|---|---|
| service scan | `nmap -Pn -sT -sV --top-ports 100` on host `app` | 150 s (`timeout`) |
| web scan | `nikto -h $KALI_TARGET -Tuning 123b -maxtime` | 200 s |
| SQLi smoke | `sqlmap -u .../api/v1/search?q=... --batch --crawl=0 --level=1 --risk=1` | 170 s (`timeout`) |
| header audit | `curl -D` on `/health` → CSP, HSTS, XFO, XCTO, Server banner | 10 s |

`-sT` (TCP connect) is mandatory: the agent runs non-root (uid 1000) and
raw sockets / ARP probes are rejected in the container — verified empirically
(default `-sV` invocation QUITTED with "Couldn't open a raw socket").

Total: ~4–8 minutes, never hours — every tool is hard-capped.

## How to run

```bash
# host wrapper (recommended — normalizes into the shared result schema)
.venv/bin/python -m tests.security.kali.kali_scan \
    --out tests/security/results/kali_<ts>.json

# or the container directly (what runner.py / CI can do)
docker compose -f docker-compose.test.yml --profile security run --rm -T --no-deps kali
```

Exit codes (`kali_scan.py`): `0` = no high/critical findings (low/medium
tolerated), `1` = high/critical findings, `2` = infra failure.
`run.sh` itself exits `0` when reports were written, `2` on formatter failure.

## Auth

`run.sh` logs into the live stack (`POST /auth/login`, test-only default
credentials `admin@example.com` / `TestAdmin123!`, overridable via
`KALI_EMAIL`/`KALI_PASSWORD`) and passes the 15-minute JWT to sqlmap via
`-H` so the smoke test hits a real authenticated query parameter
(`/api/v1/search?q=`). The token lives only in a shell variable: it is
never echoed, never written to reports, and `format_result.py` re-redacts
JWT/bearer patterns from both outputs as a second line of defense.

## Output artifacts (tests/security/reports/)

| File | Content |
|---|---|
| `kali_<ts>.json` | result doc `upcp-security-result/v1`, suite `kali` |
| `kali_<ts>.md` | human-readable findings + check table |

Severity mapping: sqlmap injection → critical, risky exposed service
(telnet/redis/docker/…) → high, nikto advisory → medium, missing security
header → low, server banner / scan-budget notes → info.
`format_result.py` duplicates the `common.py` schema helpers because
`common.py` (host-only) is not mounted into the container.

## ACP approach

The spec's "pentest agent in Kali Docker + ACP" is served by this layout:
`run.sh` is deterministic, non-interactive and single-shot, so an
ACP (Agent Client Protocol) host can treat it as a tool command —
`docker compose ... run --rm -T --no-deps kali` — and consume
`tests/security/reports/kali_*.json` (stable schema, token-redacted) as
the structured tool result instead of scraping logs. Interactive follow-up
(expanded nmap ports, deeper nikto tuning, sqlmap on other params) would
be additional `docker exec`/`run` commands against the same image, each
re-emitting `kali_<ts>.json` for the host to parse; the wrapper
`kali_scan.py` is the reference for invocation + normalization.

## Notes

- Stack contract: `KALI_TARGET=http://app:8080` (compose network), never
  restart the stack; build: `docker compose -f docker-compose.test.yml
  --profile security build kali`.
- sqlmap budget cut (< 170 s) is reported as an `info` finding
  ("inconclusive, scope reduced") — never silently swallowed.
