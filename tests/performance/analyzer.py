"""Performance results analyzer — trend tracking, SLO evaluation, regression detection.

Reads Locust CSV/JSON results, compares with baselines, generates markdown reports.

Usage:
    python tests/performance/analyzer.py --check-slo --input results/load_stats.csv
    python tests/performance/analyzer.py --compare-baseline --input results/load_stats.csv
    python tests/performance/analyzer.py --generate-report --input results/
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

RESULTS_DIR = Path(__file__).parent / "results"
BASELINE_FILE = RESULTS_DIR / "baseline.json"


@dataclass
class ScenarioResult:
    name: str
    total_requests: int = 0
    failed_requests: int = 0
    median_ms: float = 0.0
    avg_ms: float = 0.0
    p95_ms: float = 0.0
    p99_ms: float = 0.0
    min_ms: float = 0.0
    max_ms: float = 0.0
    rps: float = 0.0
    error_rate_pct: float = 0.0
    timestamp: str = ""


@dataclass
class SLOCheck:
    sli: str
    target: float
    actual: float
    passed: bool
    severity: str


@dataclass
class Regression:
    metric: str
    baseline_value: float
    current_value: float
    change_pct: float
    direction: str  # "increased" or "decreased"


def parse_locust_csv(stats_file: str) -> list[ScenarioResult]:
    """Parse Locust stats CSV file into ScenarioResult objects."""
    results = []
    with open(stats_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("Name", "Aggregated")
            total = int(row.get("Request Count", 0))
            failed = int(row.get("Failure Count", 0))
            rps = float(row.get("Requests/s", 0))

            # Latency fields (Locust CSV format)
            avg = float(row.get("Average Response Time", 0))
            p50 = float(row.get("50%", 0))
            p95 = float(row.get("95%", 0))
            p99 = float(row.get("99%", 0))
            min_rt = float(row.get("Min Response Time", 0))
            max_rt = float(row.get("Max Response Time", 0))

            error_rate = (failed / total * 100) if total > 0 else 0.0

            results.append(
                ScenarioResult(
                    name=name,
                    total_requests=total,
                    failed_requests=failed,
                    median_ms=p50,
                    avg_ms=avg,
                    p95_ms=p95,
                    p99_ms=p99,
                    min_ms=min_rt,
                    max_ms=max_rt,
                    rps=rps,
                    error_rate_pct=round(error_rate, 2),
                )
            )
    return results


def check_slo(results: list[ScenarioResult], slo_config: str | None = None) -> list[SLOCheck]:
    """Evaluate results against SLO thresholds."""
    # Default SLOs (can be overridden by config file)
    default_slos = [
        ("error_rate_pct", 5.0, "warning"),
        ("p95_ms", 2000.0, "warning"),
        ("p99_ms", 5000.0, "warning"),
    ]

    checks = []
    for result in results:
        if result.name == "Aggregated" or not result.name:
            continue
        for metric_name, threshold, severity in default_slos:
            actual = getattr(result, metric_name, 0)
            passed = actual <= threshold
            checks.append(
                SLOCheck(
                    sli=f"{result.name}.{metric_name}",
                    target=threshold,
                    actual=actual,
                    passed=passed,
                    severity=severity,
                )
            )
    return checks


def compare_with_baseline(
    current: list[ScenarioResult], baseline_file: str | None = None
) -> list[Regression]:
    """Compare current results with saved baseline."""
    bf = Path(baseline_file) if baseline_file else BASELINE_FILE
    if not bf.exists():
        return []

    with open(bf) as f:
        baseline_data = json.load(f)

    regressions = []
    baseline_map = {r["name"]: r for r in baseline_data.get("results", [])}

    for result in current:
        if result.name not in baseline_map:
            continue
        bl = baseline_map[result.name]

        for metric in ("p95_ms", "error_rate_pct", "rps"):
            bl_val = bl.get(metric, 0)
            cur_val = getattr(result, metric, 0)
            if bl_val == 0:
                continue
            change_pct = ((cur_val - bl_val) / bl_val) * 100
            if abs(change_pct) > 20:  # 20% threshold
                regressions.append(
                    Regression(
                        metric=f"{result.name}.{metric}",
                        baseline_value=bl_val,
                        current_value=cur_val,
                        change_pct=round(change_pct, 1),
                        direction="increased" if change_pct > 0 else "decreased",
                    )
                )
    return regressions


def save_baseline(results: list[ScenarioResult], output_file: str | None = None) -> None:
    """Save current results as new baseline."""
    out = Path(output_file) if output_file else BASELINE_FILE
    out.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "timestamp": datetime.now().isoformat(),
        "results": [
            {
                "name": r.name,
                "total_requests": r.total_requests,
                "failed_requests": r.failed_requests,
                "p95_ms": r.p95_ms,
                "p99_ms": r.p99_ms,
                "error_rate_pct": r.error_rate_pct,
                "rps": r.rps,
            }
            for r in results
        ],
    }
    with open(out, "w") as f:
        json.dump(data, f, indent=2)


def generate_report(
    results: list[ScenarioResult], slo_checks: list[SLOCheck], regressions: list[Regression]
) -> str:
    """Generate markdown report from analysis results."""
    lines = [
        "# Performance Test Report",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
    ]

    # Overall summary
    total_req = sum(r.total_requests for r in results if r.name and r.name != "Aggregated")
    total_failed = sum(r.failed_requests for r in results if r.name and r.name != "Aggregated")
    overall_error = (total_failed / total_req * 100) if total_req > 0 else 0
    overall_rps = sum(r.rps for r in results if r.name and r.name != "Aggregated")

    lines.append("## Overall Summary")
    lines.append("")
    lines.append(f"- **Total requests:** {total_req}")
    lines.append(f"- **Failed requests:** {total_failed}")
    lines.append(f"- **Overall error rate:** {overall_error:.2f}%")
    lines.append(f"- **Combined throughput:** {overall_rps:.1f} req/s")
    lines.append("")

    # Results table
    lines.append("## Results Summary")
    lines.append("")
    lines.append(
        "| Scenario | Requests | Failed | Error % | P50 (ms) | P95 (ms) | P99 (ms) | RPS |"
    )
    lines.append(
        "|----------|----------|--------|---------|----------|----------|----------|-----|"
    )
    for r in results:
        lines.append(
            f"| {r.name} | {r.total_requests} | {r.failed_requests} "
            f"| {r.error_rate_pct}% | {r.median_ms:.0f} | {r.p95_ms:.0f} "
            f"| {r.p99_ms:.0f} | {r.rps:.1f} |"
        )

    # SLO results
    if slo_checks:
        lines.append("")
        lines.append("## SLO Evaluation")
        lines.append("")
        passed = sum(1 for c in slo_checks if c.passed)
        total = len(slo_checks)
        lines.append(f"**{passed}/{total} SLOs met**")
        lines.append("")
        lines.append("| SLI | Target | Actual | Status |")
        lines.append("|-----|--------|--------|--------|")
        for c in slo_checks:
            status = "PASS" if c.passed else f"FAIL ({c.severity})"
            lines.append(f"| {c.sli} | {c.target} | {c.actual:.2f} | {status} |")

    # Regressions
    if regressions:
        lines.append("")
        lines.append("## Regressions vs Baseline")
        lines.append("")
        lines.append("| Metric | Baseline | Current | Change |")
        lines.append("|--------|----------|---------|--------|")
        for reg in regressions:
            lines.append(
                f"| {reg.metric} | {reg.baseline_value:.1f} "
                f"| {reg.current_value:.1f} | {reg.change_pct:+.1f}% |"
            )
    else:
        lines.append("")
        lines.append("## Regressions vs Baseline")
        lines.append("")
        lines.append("No significant regressions detected.")

    return "\n".join(lines)


def load_trend_history(results_dir: str | None = None, limit: int = 10) -> list[dict]:
    """Load last N baseline results for trend visualization."""
    rd = Path(results_dir) if results_dir else RESULTS_DIR
    history_file = rd / "trend_history.json"
    history = []

    if history_file.exists():
        with open(history_file) as f:
            history = json.load(f)

    return history[-limit:] if limit else history


def append_to_trend(results: list[ScenarioResult], results_dir: str | None = None) -> None:
    """Append current results to trend history."""
    rd = Path(results_dir) if results_dir else RESULTS_DIR
    history_file = rd / "trend_history.json"
    rd.mkdir(parents=True, exist_ok=True)

    history = []
    if history_file.exists():
        try:
            with open(history_file) as f:
                history = json.load(f)
        except (json.JSONDecodeError, OSError):
            history = []

    entry = {
        "timestamp": datetime.now().isoformat(),
        "results": {
            r.name: {
                "p95_ms": r.p95_ms,
                "p99_ms": r.p99_ms,
                "error_rate_pct": r.error_rate_pct,
                "rps": r.rps,
                "total_requests": r.total_requests,
            }
            for r in results
            if r.name and r.name != "Aggregated"
        },
    }
    history.append(entry)

    # Keep last 50 entries
    history = history[-50:]

    with open(history_file, "w") as f:
        json.dump(history, f, indent=2)


def generate_trend_ascii(history: list[dict], metric: str, scenario: str) -> str:
    """Generate ASCII sparkline for a metric trend."""
    if not history:
        return "No trend data"

    values = []
    for entry in history:
        scenario_data = entry.get("results", {}).get(scenario, {})
        val = scenario_data.get(metric, 0)
        values.append(val)

    if not values:
        return "No data"

    mn, mx = min(values), max(values)
    if mx == mn:
        return f"{''.join(['■' for _ in values])} ({mx:.0f})"

    chars = "▁▂▃▄▅▆▇█"
    sparkline = ""
    for v in values:
        idx = int((v - mn) / (mx - mn) * (len(chars) - 1))
        sparkline += chars[idx]

    return f"{sparkline} ({mn:.0f}→{mx:.0f})"


def main() -> None:
    parser = argparse.ArgumentParser(description="Performance results analyzer")
    parser.add_argument(
        "--input", "-i", required=True, help="Path to Locust CSV stats file or results directory"
    )
    parser.add_argument("--check-slo", action="store_true", help="Evaluate against SLO thresholds")
    parser.add_argument(
        "--compare-baseline", action="store_true", help="Compare with saved baseline"
    )
    parser.add_argument(
        "--save-baseline", action="store_true", help="Save current results as baseline"
    )
    parser.add_argument("--generate-report", action="store_true", help="Generate markdown report")
    parser.add_argument("--baseline-file", help="Path to baseline JSON file")
    parser.add_argument("--output", "-o", help="Output file path (report or baseline)")
    args = parser.parse_args()

    input_path = Path(args.input)
    if input_path.is_dir():
        # Find stats CSV in directory
        csvs = list(input_path.glob("*_stats.csv"))
        if not csvs:
            print(f"No *_stats.csv found in {input_path}")
            return
        results = parse_locust_csv(str(csvs[0]))
    else:
        results = parse_locust_csv(str(input_path))

    if not results:
        print("No results parsed.")
        return

    slo_checks = check_slo(results) if args.check_slo else []
    regressions = (
        compare_with_baseline(results, args.baseline_file) if args.compare_baseline else []
    )

    if args.save_baseline:
        save_baseline(results, args.output)
        print(f"Baseline saved to {args.output or BASELINE_FILE}")

    if args.generate_report or args.output:
        report = generate_report(results, slo_checks, regressions)
        if args.output:
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            with open(args.output, "w") as f:
                f.write(report)
            print(f"Report saved to {args.output}")
        else:
            print(report)

    if not args.generate_report and not args.save_baseline and not args.output:
        # Default: print summary
        for r in results:
            print(
                f"{r.name:30s} | {r.total_requests:6d} req | "
                f"{r.error_rate_pct:5.1f}% err | p95={r.p95_ms:.0f}ms | "
                f"{r.rps:.1f} rps"
            )

        if slo_checks:
            passed = sum(1 for c in slo_checks if c.passed)
            print(f"\nSLO: {passed}/{len(slo_checks)} met")


if __name__ == "__main__":
    main()
