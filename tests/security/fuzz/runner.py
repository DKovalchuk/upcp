"""API fuzzer suite runner — TASK-0142 / SPEC-0024 Phase 4.

Discovers fuzz scenarios via a registry (mirrors tests/chaos/runner.py),
executes them against the live test stack, and writes ONE result document
(schema "upcp-security-result/v1") to the --out path.

Usage:
    python -m tests.security.fuzz --out /tmp/fuzz.json
    SECURITY_RESULT_OUT=/tmp/fuzz.json python -m tests.security.fuzz
    python -m tests.security.fuzz --list
    python -m tests.security.fuzz --scenario injection --out /tmp/inj.json

Exit codes:
    0 — all checks passed
    1 — some checks failed (see "findings" in the result document)
    2 — could not run (target down / login failed)
"""

from __future__ import annotations

import argparse
import importlib
import json
import logging
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

# repo root on sys.path so absolute `tests.security.*` imports resolve when the
# suite is invoked as `python -m tests.security.fuzz` from anywhere
if str(Path(__file__).resolve().parents[3]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from tests.security.common import (  # noqa: E402
    SECURITY_BASE_URL,
    check,
    health_ok,
    login,
    summarize,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s [%(name)s] %(message)s")
logger = logging.getLogger("fuzz.runner")

DEFAULT_OUT_DIR = Path(__file__).resolve().parents[1] / "results"

# Scenario registry — module path is imported dynamically, like tests/chaos.
SCENARIOS: dict[str, dict[str, str]] = {
    "auth_bypass": {
        "module": "tests.security.fuzz.scenarios.auth_bypass",
        "description": "No-token / malformed / tampered credential probes on protected endpoints",
    },
    "injection": {
        "module": "tests.security.fuzz.scenarios.injection",
        "description": "SQLi in params and path segments, path traversal, XSS reflection probes",
    },
    "malformed": {
        "module": "tests.security.fuzz.scenarios.malformed",
        "description": "Oversized, wrong-type, null-byte, unicode, nested and huge-pagination payloads",
    },
}


def run_suite(scenario_names: list[str]) -> tuple[list[dict], dict[str, dict[str, object]]]:
    """Run selected scenarios; return (all checks, per-scenario counts)."""
    all_checks: list[dict] = []
    counts: dict[str, dict[str, object]] = {}
    for name in scenario_names:
        meta = SCENARIOS[name]
        started = time.monotonic()
        try:
            module = importlib.import_module(meta["module"])
            results = module.run(SECURITY_BASE_URL)
        except Exception as exc:  # a crashing scenario must still yield a result doc
            logger.exception("scenario %s crashed", name)
            results = [
                check(
                    f"{name}: scenario crashed",
                    name,
                    False,
                    expected="scenario runs without exceptions",
                    actual=type(exc).__name__,
                    detail=str(exc),
                    severity="medium",
                )
            ]
        failed = sum(1 for r in results if r["status"] == "fail")
        counts[name] = {
            "total": len(results),
            "passed": len(results) - failed,
            "failed": failed,
            "duration_seconds": round(time.monotonic() - started, 2),
        }
        logger.info(
            "scenario %s: %d checks, %d failed (%.2fs)",
            name,
            len(results),
            failed,
            counts[name]["duration_seconds"],
        )
        all_checks.extend(results)
    return all_checks, counts


def _default_out() -> Path:
    ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    return DEFAULT_OUT_DIR / f"fuzz_{ts}.json"


def _write_result(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    logger.info("result written to %s", path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tests.security.fuzz", description="UPCP API fuzzer"
    )
    parser.add_argument(
        "--out",
        help="result JSON path (default: $SECURITY_RESULT_OUT or tests/security/results/fuzz_<ts>.json)",
    )
    parser.add_argument(
        "--scenario",
        action="append",
        choices=sorted(SCENARIOS),
        help="run only this scenario (repeatable; default: all)",
    )
    parser.add_argument("--list", action="store_true", help="list available scenarios and exit")
    args = parser.parse_args(argv)

    if args.list:
        for name, meta in SCENARIOS.items():
            print(f"  {name:14s} {meta['description']}")
        return 0

    out = Path(args.out or os.getenv("SECURITY_RESULT_OUT") or _default_out())
    scenario_names = args.scenario or list(SCENARIOS)

    if not health_ok(SECURITY_BASE_URL):
        logger.error("target %s is down (/health not OK)", SECURITY_BASE_URL)
        _write_result(
            out,
            summarize(
                suite="fuzz",
                target=SECURITY_BASE_URL,
                checks=[],
                error="target down: /health not OK",
            ),
        )
        return 2
    try:
        login()
    except Exception as exc:
        logger.error("login failed: %s", exc)
        _write_result(
            out,
            summarize(
                suite="fuzz", target=SECURITY_BASE_URL, checks=[], error=f"login failed: {exc}"
            ),
        )
        return 2

    started = time.monotonic()
    checks, counts = run_suite(scenario_names)
    doc = summarize(
        suite="fuzz",
        target=SECURITY_BASE_URL,
        checks=checks,
        scenario_counts=counts,
        duration_seconds=round(time.monotonic() - started, 2),
    )
    _write_result(out, doc)

    summary = doc["summary"]
    print(f"fuzz: {summary['passed']}/{summary['total']} checks passed, {summary['failed']} failed")
    for name, c in counts.items():
        status = "PASS" if c["failed"] == 0 else "FAIL"
        print(f"  [{status}] {name:14s} {c['passed']}/{c['total']}")
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
