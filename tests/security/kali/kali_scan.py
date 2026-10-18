"""Kali pentest host wrapper — TASK-0142 / SPEC-0024 Phase 4.

Usage:
    python -m tests.security.kali.kali_scan --out results/kali_<ts>.json

Runs the `kali` compose service (its run.sh agent executes nmap/nikto/sqlmap/
curl checks against http://app:8080), waits for exit, then converts the
container-generated JSON report in tests/security/reports/ into the shared
``upcp-security-result/v1`` document at --out via tests.security.common.
The container console output is saved (redacted) next to the reports.

Exit codes: 0 = no high/critical findings, 1 = high/critical findings,
2 = infra failure (container error or missing report).

Note: ``stdin=DEVNULL`` is required — ``docker compose run`` hangs after the
container exits when its stdin stays open (verified empirically).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

from tests.security.common import summarize

REPO_ROOT = Path(__file__).resolve().parents[3]
COMPOSE_FILE = REPO_ROOT / "docker-compose.test.yml"
DEFAULT_REPORT_DIR = REPO_ROOT / "tests" / "security" / "reports"

REDACT_PATTERNS = [
    (re.compile(r"eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]*"), "REDACTED"),
    (re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/=-]{15,}"), "Bearer REDACTED"),
]


def redact_text(text: str) -> str:
    for pat, repl in REDACT_PATTERNS:
        text = pat.sub(repl, text)
    return text


def redact_file(path: Path) -> None:
    if path.is_file():
        raw = path.read_text(encoding="utf-8", errors="replace")
        cleaned = redact_text(raw)
        if cleaned != raw:
            path.write_text(cleaned, encoding="utf-8")


def newest_report(report_dir: Path, since: float) -> Path | None:
    candidates = [
        p for p in report_dir.glob("kali_*.json") if p.is_file() and p.stat().st_mtime >= since - 1
    ]
    return max(candidates, key=lambda p: p.stat().st_mtime) if candidates else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="kali_scan", description="Kali pentest agent via docker compose"
    )
    parser.add_argument("--out", required=True, help="result JSON path (upcp-security-result/v1)")
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument(
        "--timeout",
        type=int,
        default=900,
        help="max seconds to wait for the container (default 900)",
    )
    args = parser.parse_args(argv)

    report_dir = Path(args.report_dir)
    if not report_dir.is_absolute():
        report_dir = (Path.cwd() / report_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "docker",
        "compose",
        "-f",
        str(COMPOSE_FILE),
        "--profile",
        "security",
        "run",
        "--rm",
        "-T",
        "--no-deps",
        "kali",
    ]
    start = time.time()
    print(f"kali_scan: starting container (timeout={args.timeout}s)")
    try:
        proc = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=args.timeout,
        )
    except subprocess.TimeoutExpired:
        print("kali_scan: container timed out (infra failure)", file=sys.stderr)
        return 2
    duration = int(time.time() - start)

    report_json = newest_report(report_dir, start)
    if proc.returncode != 0 or report_json is None:
        tail = "\n".join((proc.stdout + proc.stderr).splitlines()[-15:])
        print(
            f"kali_scan: run failed rc={proc.returncode} "
            f"report={'found' if report_json else 'missing'}\n{tail}",
            file=sys.stderr,
        )
        return 2

    # Evidence: full container console (run.sh echoes; tokens redacted).
    console_log = report_json.with_suffix(".console.log")
    console_text = redact_text((proc.stdout or "") + (proc.stderr or ""))
    if console_text.strip():
        console_log.write_text(console_text, encoding="utf-8")

    report_md = report_json.with_suffix(".md")
    redact_file(report_json)
    redact_file(report_md)
    try:
        data = json.loads(report_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"kali_scan: cannot parse {report_json}: {exc}", file=sys.stderr)
        return 2
    if data.get("schema") != "upcp-security-result/v1" or data.get("suite") != "kali":
        print(
            f"kali_scan: unexpected schema in {report_json}: "
            f"{data.get('schema')}/{data.get('suite')}",
            file=sys.stderr,
        )
        return 2

    result = summarize(
        "kali",
        str(data.get("target", "http://app:8080")),
        list(data.get("checks", [])),
        report_json=str(report_json),
        report_md=str(report_md),
        console_log=str(console_log),
        duration_seconds=data.get("duration_seconds", duration),
        host_wrapper_duration_seconds=duration,
        tool_budgets=data.get("tool_budgets", {}),
        auth_used_for_sqlmap=data.get("auth_used_for_sqlmap", "no"),
    )
    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = Path.cwd() / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        redact_text(json.dumps(result, indent=2, ensure_ascii=False)) + "\n", encoding="utf-8"
    )

    high = [f for f in result["findings"] if f["severity"] in ("high", "critical")]
    summary = result["summary"]
    print(
        f"kali_scan: {summary['total']} checks, {summary['failed']} findings "
        f"({len(high)} high/critical) -> {out_path}"
    )
    return 1 if high else 0


if __name__ == "__main__":
    sys.exit(main())
