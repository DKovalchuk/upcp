"""Aggregate quality-gate suite results into one Markdown + JSON report.

SPEC-0024 Phase 5 / TASK-0143. Discovers the newest run result of each
suite under <results-root>/{performance,chaos,security}/results/, reuses
tests/performance/analyzer.py for stats parsing and baseline comparison,
and writes quality-report.md + quality-report.json.

Usage:
    python tests/quality_gate/aggregate.py --results-root tests --out-dir . [--profile quick|full]

Exit codes: 0 = report written (findings/failures do NOT affect it — the
CI gate job decides pass/fail from suite exit codes); 2 = internal error
(missing/unreadable required input, unexpected exception).
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tests.performance import analyzer  # noqa: E402
from tests.quality_gate.markdown_report import render_markdown  # noqa: E402

SCHEMA = "upcp-quality-report/v1"
SECURITY_SUITES = ("authz", "fuzz", "zap", "kali")
SUITE_NAMES = ("performance", "chaos", "security")


def _newest(paths: list[Path]) -> Path | None:
    """Pick the file with the newest mtime (mtime, not name, decides recency)."""
    return max(paths, key=lambda p: p.stat().st_mtime) if paths else None


def _rel(path: Path, results_root: Path) -> str:
    """Report path relative to the parent of --results-root (tests/… in CI)."""
    try:
        return str(path.resolve().relative_to(results_root.resolve().parent))
    except ValueError:
        return str(path)


def _missing(suite: str, results_root: Path) -> dict:
    return {
        "status": "missing",
        "source_file": None,
        "summary": {"results_dir": _rel(results_root / suite / "results", results_root)},
        "passed": None,
    }


def _load_performance(results_root: Path) -> tuple[dict, list[dict]]:
    res_dir = results_root / "performance" / "results"
    stats = _newest(list(res_dir.glob("*_stats.csv")))
    if stats is None:
        return _missing("performance", results_root), []
    all_rows = analyzer.parse_locust_csv(str(stats))
    scenarios = [r for r in all_rows if r.name and r.name != "Aggregated"]
    slo = analyzer.check_slo(all_rows)
    baseline = res_dir / "baseline.json"
    regressions: list[dict] = []
    if baseline.exists():
        regressions = [asdict(r) for r in analyzer.compare_with_baseline(all_rows, str(baseline))]
    entry = {
        "status": "ok",
        "source_file": _rel(stats, results_root),
        "summary": {
            "results_dir": _rel(res_dir, results_root),
            "checks": len(slo),
            "passed": sum(1 for c in slo if c.passed),
            "failed": sum(1 for c in slo if not c.passed),
            "findings": len(regressions),
            "scenarios": len(scenarios),
            "total_requests": sum(r.total_requests for r in scenarios),
            "failed_requests": sum(r.failed_requests for r in scenarios),
            "baseline_present": baseline.exists(),
            "regressions": len(regressions),
        },
        "passed": all(c.passed for c in slo) if slo else None,
    }
    return entry, regressions


def _load_chaos(results_root: Path) -> tuple[dict, list[dict]]:
    res_dir = results_root / "chaos" / "results"
    newest = _newest(list(res_dir.glob("chaos_*.json")))
    if newest is None:
        return _missing("chaos", results_root), []
    data = json.loads(newest.read_text())
    experiments = data.get("experiments", [])
    failures: list[dict] = []
    failed_assertions = 0
    for exp in experiments:
        if exp.get("passed"):
            continue
        bad = [a for a in exp.get("assertions", []) if not a.get("passed")]
        failed_assertions += len(bad) or 1  # a failed exp without recorded assertions still counts
        failures.append(
            {
                "experiment": exp.get("experiment", ""),
                "mttr_seconds": exp.get("mttr_seconds"),
                "failed_assertions": bad,
                "summary": exp.get("summary", ""),
            }
        )
    passed = sum(1 for e in experiments if e.get("passed"))
    entry = {
        "status": "ok",
        "source_file": _rel(newest, results_root),
        "summary": {
            "results_dir": _rel(res_dir, results_root),
            "checks": len(experiments),
            "passed": passed,
            "failed": len(experiments) - passed,
            "findings": failed_assertions,
            "assertions_total": sum(len(e.get("assertions", [])) for e in experiments),
            "assertions_passed": sum(
                1 for e in experiments for a in e.get("assertions", []) if a.get("passed")
            ),
            "failed_experiments": [f["experiment"] for f in failures],
        },
        "passed": (failed_assertions == 0) if experiments else None,
        "failures": failures,
    }
    return entry, []


def _load_security(results_root: Path) -> tuple[dict, list[dict]]:
    res_dir = results_root / "security" / "results"
    subsuites: dict[str, dict] = {}
    findings: list[dict] = []
    chosen: list[Path] = []
    for suite in SECURITY_SUITES:
        src = _newest(list(res_dir.glob(f"{suite}_*.json")))
        if src is None:
            continue
        data = json.loads(src.read_text())
        summ = data.get("summary") or {}
        checks = data.get("checks", [])
        subsuites[suite] = {
            "source_file": _rel(src, results_root),
            "checks": summ.get("total", len(checks)),
            "passed": summ.get("passed", 0),
            "failed": summ.get("failed", 0),
            "findings": len(data.get("findings", [])),
        }
        findings.extend(data.get("findings", []))
        chosen.append(src)
    if not chosen:
        return _missing("security", results_root), []
    counts = {k: sum(s[k] for s in subsuites.values()) for k in ("checks", "passed", "failed")}
    entry = {
        "status": "ok",
        "source_file": _rel(max(chosen, key=lambda p: p.stat().st_mtime), results_root),
        "summary": {
            "results_dir": _rel(res_dir, results_root),
            **counts,
            "findings": len(findings),
            "subsuites": subsuites,
        },
        "passed": counts["failed"] == 0,
        "findings": findings,
    }
    return entry, []


def build_report(results_root: Path, profile: str) -> dict:
    perf_entry, regressions = _load_performance(results_root)
    chaos_entry, _ = _load_chaos(results_root)
    sec_entry, _ = _load_security(results_root)
    suites = {"performance": perf_entry, "chaos": chaos_entry, "security": sec_entry}
    summaries = [e["summary"] for e in suites.values()]
    counts = {
        "suites_ok": sum(1 for e in suites.values() if e["status"] == "ok"),
        "suites_missing": sum(1 for e in suites.values() if e["status"] == "missing"),
        "findings_total": sum(s.get("findings", 0) or 0 for s in summaries),
        "checks_passed": sum(s.get("passed", 0) or 0 for s in summaries),
        "checks_total": sum(s.get("checks", 0) or 0 for s in summaries),
    }
    return {
        "schema": SCHEMA,
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "profile": profile,
        "suites": suites,
        "regressions": regressions,
        "counts": counts,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Aggregate quality-gate suite results into quality-report.{md,json}"
    )
    parser.add_argument(
        "--results-root", default="tests", help="dir holding <suite>/results/ (default: tests)"
    )
    parser.add_argument(
        "--out-dir", default=".", help="where to write quality-report.md/.json (default: .)"
    )
    parser.add_argument(
        "--profile", choices=("quick", "full"), default="quick", help="report profile label"
    )
    args = parser.parse_args(argv)
    results_root, out_dir = Path(args.results_root), Path(args.out_dir)
    if not results_root.is_dir():
        print(f"ERROR: results root not found: {results_root}", file=sys.stderr)
        return 2
    try:
        report = build_report(results_root, args.profile)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "quality-report.json").write_text(json.dumps(report, indent=2) + "\n")
        (out_dir / "quality-report.md").write_text(render_markdown(report))
    except Exception as exc:  # unreadable input / unexpected error → exit 2
        print(f"ERROR: aggregation failed: {exc}", file=sys.stderr)
        return 2
    c = report["counts"]
    print(
        f"quality-report written to {out_dir} "
        f"(suites ok {c['suites_ok']}, missing {c['suites_missing']}, findings {c['findings_total']})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
