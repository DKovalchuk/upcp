"""Chaos test runner — orchestrate chaos experiments.

Runs chaos scenarios against the test environment, collects verdicts,
generates reports, and saves results for trend tracking.

Usage:
    python tests/chaos/runner.py --profile quick
    python tests/chaos/runner.py --profile full
    python tests/chaos/runner.py --experiment service_kill_app
    python tests/chaos/runner.py --list
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# repo root on sys.path so absolute `tests.chaos.*` imports resolve
# when the runner is invoked as `python tests/chaos/runner.py`
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("chaos.runner")

RESULTS_DIR = Path(__file__).parent / "results"
REPORTS_DIR = Path(__file__).parent / "reports"

# Experiment registry
EXPERIMENTS = {
    "service_kill_app": {
        "module": "tests.chaos.scenarios.service_kill",
        "description": "Kill app container, measure MTTR",
        "params": {"service": "app"},
    },
    "service_kill_db": {
        "module": "tests.chaos.scenarios.service_kill",
        "description": "Kill DB container, measure MTTR",
        "params": {"service": "db"},
    },
    "redis_failure": {
        "module": "tests.chaos.scenarios.redis_failure",
        "description": "Stop Redis, verify graceful degradation",
    },
    "cascade_redis_app": {
        "module": "tests.chaos.scenarios.cascade_failure",
        "description": "Redis failure → app degradation → recovery chain",
    },
    "db_restart": {
        "module": "tests.chaos.scenarios.db_restart",
        "description": "Restart DB during active requests",
    },
    "app_restart": {
        "module": "tests.chaos.scenarios.app_restart",
        "description": "Kill app during active traffic",
    },
    "full_outage": {
        "module": "tests.chaos.scenarios.full_outage",
        "description": "Kill all services, restart in order",
    },
}

PROFILES = {
    "quick": {
        "description": "Quick smoke — 3 fast experiments",
        "experiments": ["service_kill_app", "redis_failure", "db_restart"],
    },
    "standard": {
        "description": "Standard suite — 5 experiments",
        "experiments": [
            "service_kill_app",
            "service_kill_db",
            "redis_failure",
            "cascade_redis_app",
            "db_restart",
        ],
    },
    "full": {
        "description": "Full suite — all experiments including full outage",
        "experiments": list(EXPERIMENTS.keys()),
    },
    "resilience": {
        "description": "Resilience focus — cascade and outage scenarios",
        "experiments": ["cascade_redis_app", "app_restart", "full_outage"],
    },
}


def run_experiment(name: str, **override_params) -> dict:
    """Run a single chaos experiment."""
    if name not in EXPERIMENTS:
        raise ValueError(f"Unknown experiment: {name}")

    exp = EXPERIMENTS[name]
    module_path = exp["module"]

    # Dynamic import
    import importlib

    module = importlib.import_module(module_path)

    from tests.chaos.engine import ChaosEngine

    # CI gate runs the ephemeral upcp-test-ci project — container lookup by
    # compose label must follow it (TASK-0143)
    engine = ChaosEngine(compose_project=os.getenv("CHAOS_COMPOSE_PROJECT", "upcp-test"))

    params = {**exp.get("params", {}), **override_params}
    # Scenarios default health_url to the LOCAL test stack (:38082) — pass it
    # from CHAOS_BASE_URL so probes hit the stack the experiment actually
    # targets. The hardcoded default looked green in local rehearsals only
    # because a local test stack happened to occupy :38082; in CI nothing
    # listened there and every experiment failed at "Step 1" (TASK-0143).
    params.setdefault(
        "health_url",
        os.getenv("CHAOS_BASE_URL", "http://localhost:38082").rstrip("/") + "/health",
    )
    verdict = module.run(engine, **params)

    return {
        "experiment": name,
        "passed": verdict.passed,
        "mttr_seconds": verdict.mttr_seconds,
        "detection_seconds": verdict.detection_seconds,
        "duration_seconds": verdict.duration_seconds,
        "assertions": [
            {
                "name": a.name,
                "passed": a.passed,
                "actual": str(a.actual) if a.actual is not None else None,
                "expected": str(a.expected) if a.expected is not None else None,
                "message": a.message,
            }
            for a in verdict.assertions
        ],
        "summary": verdict.summary,
    }


def run_profile(profile_name: str) -> list[dict]:
    """Run all experiments in a profile."""
    if profile_name not in PROFILES:
        raise ValueError(f"Unknown profile: {profile_name}")

    profile = PROFILES[profile_name]
    results = []

    logger.info("=" * 60)
    logger.info("CHAOS PROFILE: %s — %s", profile_name, profile["description"])
    logger.info("=" * 60)

    for i, exp_name in enumerate(profile["experiments"], 1):
        logger.info("")
        logger.info("[%d/%d] Running: %s", i, len(profile["experiments"]), exp_name)
        logger.info("-" * 40)

        try:
            result = run_experiment(exp_name)
            results.append(result)
            status = "PASS" if result["passed"] else "FAIL"
            logger.info("[%s] %s — MTTR=%.1fs", status, exp_name, result["mttr_seconds"])
        except Exception as e:
            logger.error("[ERROR] %s: %s", exp_name, e)
            results.append(
                {
                    "experiment": exp_name,
                    "passed": False,
                    "error": str(e),
                    "mttr_seconds": 0,
                    "assertions": [],
                    "summary": f"[ERROR] {exp_name}: {e}",
                }
            )

    return results


def save_results(results: list[dict], output_dir: Path | None = None) -> Path:
    """Save results to JSON file."""
    out = output_dir or RESULTS_DIR
    out.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"chaos_{timestamp}.json"
    filepath = out / filename

    data = {
        "timestamp": datetime.now().isoformat(),
        "total": len(results),
        "passed": sum(1 for r in results if r.get("passed")),
        "failed": sum(1 for r in results if not r.get("passed")),
        "experiments": results,
    }

    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)

    logger.info("Results saved to %s", filepath)
    return filepath


def generate_report(results: list[dict]) -> str:
    """Generate markdown chaos test report."""
    lines = [
        "# Chaos Engineering Report",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
    ]

    total = len(results)
    passed = sum(1 for r in results if r.get("passed"))
    failed = total - passed

    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Total experiments:** {total}")
    lines.append(f"- **Passed:** {passed}")
    lines.append(f"- **Failed:** {failed}")
    lines.append(
        f"- **Pass rate:** {passed / total * 100:.0f}%" if total > 0 else "- **Pass rate:** N/A"
    )
    lines.append("")

    # Results table
    lines.append("## Results")
    lines.append("")
    lines.append("| Experiment | Status | MTTR (s) | Duration (s) | Assertions |")
    lines.append("|------------|--------|----------|--------------|------------|")
    for r in results:
        status = "PASS" if r.get("passed") else "FAIL"
        mttr = r.get("mttr_seconds", 0)
        duration = r.get("duration_seconds", 0)
        assertions = r.get("assertions", [])
        a_passed = sum(1 for a in assertions if a.get("passed"))
        a_total = len(assertions)
        lines.append(
            f"| {r['experiment']} | {status} | {mttr:.1f} | {duration:.1f} | {a_passed}/{a_total} |"
        )

    # Detailed results
    lines.append("")
    lines.append("## Detailed Results")
    lines.append("")
    for r in results:
        status = "PASS" if r.get("passed") else "FAIL"
        lines.append(f"### {r['experiment']} [{status}]")
        lines.append("")
        if r.get("error"):
            lines.append(f"**Error:** {r['error']}")
            lines.append("")
            continue
        for a in r.get("assertions", []):
            icon = "PASS" if a.get("passed") else "FAIL"
            lines.append(f"- [{icon}] {a.get('message', a.get('name', 'unknown'))}")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="UPCP Chaos Test Runner")
    parser.add_argument("--profile", "-p", help="Profile name (quick/standard/full/resilience)")
    parser.add_argument("--experiment", "-e", help="Single experiment to run")
    parser.add_argument("--list", "-l", action="store_true", help="List available experiments")
    parser.add_argument("--report", "-r", action="store_true", help="Generate markdown report")
    parser.add_argument("--output", "-o", help="Output directory for results")
    args = parser.parse_args()

    if args.list:
        print("Available experiments:")
        for name, exp in EXPERIMENTS.items():
            print(f"  {name:25s} — {exp['description']}")
        print("\nAvailable profiles:")
        for name, prof in PROFILES.items():
            print(f"  {name:15s} — {prof['description']} ({len(prof['experiments'])} experiments)")
        return

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    if args.profile:
        results = run_profile(args.profile)
    elif args.experiment:
        results = [run_experiment(args.experiment)]
    else:
        print("Specify --profile or --experiment. Use --list for options.")
        sys.exit(1)

    # Save results
    out_dir = Path(args.output) if args.output else RESULTS_DIR
    save_results(results, out_dir)

    # Generate report
    if args.report:
        report = generate_report(results)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = REPORTS_DIR / f"chaos_{timestamp}.md"
        with open(report_path, "w") as f:
            f.write(report)
        logger.info("Report saved to %s", report_path)

    # Print summary
    passed = sum(1 for r in results if r.get("passed"))
    total = len(results)
    print(f"\n{'=' * 60}")
    print(f"CHAOS RESULTS: {passed}/{total} passed")
    for r in results:
        status = "PASS" if r.get("passed") else "FAIL"
        print(f"  [{status}] {r['experiment']}")
    print(f"{'=' * 60}")

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
