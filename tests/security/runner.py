"""Security test runner — orchestrate security suites with profiles.

Runs the security suites (authz, fuzz, zap, kali) against the live test
stack, collects per-suite result JSONs, and optionally generates a
consolidated markdown report.

Usage:
    python tests/security/runner.py --list
    python tests/security/runner.py --profile baseline --report
    python tests/security/runner.py --profile full --report
    python tests/security/runner.py --suite fuzz
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

import yaml

# repo root so `tests.security.*` imports and module invocations resolve
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tests.security.common import health_ok  # noqa: E402

RESULTS_DIR = Path(__file__).parent / "results"
REPORTS_DIR = Path(__file__).parent / "reports"
PROFILES_FILE = Path(__file__).parent / "config" / "security_profiles.yaml"

# suite -> (argv template; {out} = result JSON path; run from repo root)
SUITES: dict[str, dict] = {
    "authz": {
        "desc": "Auth/RBAC integration suite (pytest) vs live stack",
        "argv": [
            sys.executable,
            "-m",
            "pytest",
            "tests/security/authz",
            "-o",
            "addopts=",
            "-q",
            "--junitxml",
            "{junit}",
        ],
        "junit": True,
    },
    "fuzz": {
        "desc": "API fuzzer: auth bypass, injection, malformed input",
        "argv": [sys.executable, "-m", "tests.security.fuzz", "--out", "{out}"],
        "junit": False,
    },
    "zap": {
        "desc": "ZAP DAST baseline scan (docker compose, security profile)",
        "argv": [
            sys.executable,
            "-m",
            "tests.security.dast.zap_scan",
            "--out",
            "{out}",
            "--mode",
            "baseline",
        ],
        "junit": False,
    },
    "kali": {
        "desc": "Kali pentest agent (docker compose, security profile)",
        "argv": [sys.executable, "-m", "tests.security.kali.kali_scan", "--out", "{out}"],
        "junit": False,
    },
}


def load_config() -> dict:
    try:
        with open(PROFILES_FILE) as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {"profiles": {}}


def load_result(path: Path) -> dict | None:
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def run_suite(name: str, base_url: str) -> tuple[int, dict | None]:
    """Run one suite; return (exit code, result document or None)."""
    spec = SUITES[name]
    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    out_path = RESULTS_DIR / f"{name}_{ts}.json"
    junit_path = RESULTS_DIR / f"{name}_{ts}.xml"
    env = {**os.environ, "SECURITY_RESULT_OUT": str(out_path), "SECURITY_BASE_URL": base_url}
    argv = [a.format(out=out_path, junit=junit_path) for a in spec["argv"]]

    print(f"\n{'=' * 60}\nSuite: {name} — {spec['desc']}\n{'=' * 60}")
    try:
        proc = subprocess.run(argv, cwd=str(REPO_ROOT), env=env)
        code = proc.returncode
    except OSError as exc:
        print(f"Suite {name} could not be started: {exc}")
        code = 2

    result = load_result(out_path)
    if result is None and code in (0, 1):
        # suite claimed to run but produced no result file — infra failure
        code = 2
    return code, result


def print_summary(results: list[dict]) -> None:
    print(f"\n{'=' * 60}\nSummary\n{'=' * 60}")
    for r in results:
        s = r["summary"]
        print(
            f"  {r['suite']:8} {s['passed']}/{s['total']} checks passed, "
            f"{len(r.get('findings', []))} findings"
        )


def write_report(results: list[dict], profile: str) -> Path:
    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / f"security_{ts}.md"
    lines = [
        f"# Security report — profile `{profile}`",
        "",
        f"Generated: {ts} (UTC) · schema: `upcp-security-result/v1`",
        "",
        "| Suite | Checks | Passed | Failed | Findings |",
        "|-------|--------|--------|--------|----------|",
    ]
    for r in results:
        s = r["summary"]
        lines.append(
            f"| {r['suite']} | {s['total']} | {s['passed']} | {s['failed']} | "
            f"{len(r.get('findings', []))} |"
        )
    lines.append("")
    for r in results:
        findings = r.get("findings", [])
        if not findings:
            continue
        lines.append(f"## Findings — {r['suite']}")
        lines.append("")
        for f_ in findings:
            lines.append(f"- **[{f_['severity'].upper()}] {f_['title']}** ({f_['category']})")
            if f_.get("detail"):
                lines.append(f"  - {f_['detail']}")
        lines.append("")
    if not any(r.get("findings") for r in results):
        lines.append("No findings.")
        lines.append("")
    path.write_text("\n".join(lines))
    return path


# Pushgateway (TASK-0158 — backlog §8-B, "Sec→Grafana"): best-effort publish
# of run results as Prometheus gauges; an unreachable gateway never changes
# the suite exit code (observability must not break the gate).
DEFAULT_PUSHGATEWAY_URL = "http://127.0.0.1:39092"
PUSH_SEVERITIES = ("high", "medium", "low", "info")


def build_push_body(result: dict) -> str:
    """Prometheus text exposition for one upcp-security-result/v1 document."""
    suite = str(result.get("suite") or "unknown")
    failed = int((result.get("summary") or {}).get("failed", 1))
    counts = {sev: 0 for sev in PUSH_SEVERITIES}
    for f_ in result.get("findings", []):
        sev = str(f_.get("severity") or "medium")
        counts[sev if sev in counts else "medium"] += 1
    lines = [
        "# TYPE upcp_security_pass gauge",
        f'upcp_security_pass{{suite="{suite}"}} {1 if failed == 0 else 0}',
        "# TYPE upcp_security_findings gauge",
    ]
    lines.extend(
        f'upcp_security_findings{{suite="{suite}",severity="{sev}"}} {counts[sev]}'
        for sev in PUSH_SEVERITIES
    )
    if "duration_seconds" in result:
        lines.extend(
            [
                "# TYPE upcp_security_duration_seconds gauge",
                f'upcp_security_duration_seconds{{suite="{suite}"}} '
                f"{float(result['duration_seconds']):g}",
            ]
        )
    lines.extend(
        [
            "# TYPE upcp_security_timestamp gauge",
            f'upcp_security_timestamp{{suite="{suite}"}} {int(datetime.now(UTC).timestamp())}',
        ]
    )
    return "\n".join(lines) + "\n"


def push_metrics(results: list[dict], *, url: str | None = None) -> bool:
    """PUT every result to Pushgateway (grouping key: suite). Best-effort."""
    base = (url or os.getenv("PUSHGATEWAY_URL", DEFAULT_PUSHGATEWAY_URL)).rstrip("/")
    ok = True
    for r in results:
        suite = str(r.get("suite") or "unknown")
        target = f"{base}/metrics/job/upcp_security/suite/{suite}"
        try:
            # PUT replaces the whole metric set for the grouping key (stale
            # series like a dropped duration disappear); POST would only
            # replace same-name metrics.
            req = urllib.request.Request(
                target, data=build_push_body(r).encode("utf-8"), method="PUT"
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                resp.read()
            print(f"pushgateway: published suite={suite}")
        except (OSError, ValueError) as exc:
            ok = False
            print(f"pushgateway: security metrics not published ({exc})", file=sys.stderr)
    return ok


def main() -> None:
    parser = argparse.ArgumentParser(description="UPCP Security Test Runner")
    parser.add_argument("--profile", "-p", help="Profile from security_profiles.yaml")
    parser.add_argument("--suite", "-s", help="Run a single suite by name")
    parser.add_argument("--list", "-l", action="store_true", help="List profiles and suites")
    parser.add_argument("--report", "-r", action="store_true", help="Write markdown report")
    parser.add_argument(
        "--host",
        default=os.getenv("SECURITY_BASE_URL", "http://localhost:38082"),
        help="Target backend URL (default: test app on localhost:38082)",
    )
    args = parser.parse_args()
    config = load_config()

    if args.list:
        print("Profiles:")
        for name, prof in (config.get("profiles") or {}).items():
            print(
                f"  {name:10} {prof.get('description', '')} — suites: {', '.join(prof.get('suites', []))}"
            )
        print("Suites:")
        for name, spec in SUITES.items():
            print(f"  {name:10} {spec['desc']}")
        return

    if args.suite:
        suites = [args.suite]
    elif args.profile:
        prof = (config.get("profiles") or {}).get(args.profile)
        if not prof:
            print(f"Profile not found: {args.profile}")
            sys.exit(2)
        suites = prof.get("suites", [])
    else:
        print("Specify --profile or --suite. Use --list for options.")
        sys.exit(2)

    unknown = [s for s in suites if s not in SUITES]
    if unknown:
        print(f"Unknown suites: {', '.join(unknown)}")
        sys.exit(2)

    if not health_ok(args.host):
        print(f"ERROR: Target {args.host} is not healthy. Aborting.")
        sys.exit(2)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    exit_codes: dict[str, int] = {}
    results: list[dict] = []
    for suite in suites:
        code, result = run_suite(suite, args.host)
        exit_codes[suite] = code
        if result is not None:
            results.append(result)
        else:
            results.append(
                {
                    "suite": suite,
                    "target": args.host,
                    "checks": [],
                    "findings": [],
                    "summary": {"total": 0, "passed": 0, "failed": 1},
                    "infra_error": True,
                }
            )

    if results:
        print_summary(results)
        # TASK-0158 (backlog §8-B): publish results — best-effort, an
        # unreachable gateway must not change the suite exit code.
        push_metrics(results)
    if args.report and results:
        report_path = write_report(results, args.profile or args.suite or "custom")
        print(f"\nReport saved to: {report_path}")

    # 2 (infra) outranks 1 (findings); authz maps pytest exit directly
    sys.exit(max(exit_codes.values(), default=0))


if __name__ == "__main__":
    main()
