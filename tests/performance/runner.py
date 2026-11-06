"""Performance test runner — orchestrate Locust scenarios with profiles.

Runs Locust scenarios against the test environment, collects results,
and optionally generates reports.

Usage:
    python tests/performance/runner.py --profile smoke
    python tests/performance/runner.py --profile load --report
    python tests/performance/runner.py --scenario scenario_concurrency --users 50 --run-time 3m
    python tests/performance/runner.py --profile all --report --save-baseline
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

RESULTS_DIR = Path(__file__).parent / "results"
REPORTS_DIR = Path(__file__).parent / "reports"
LOCUSTFILES_DIR = Path(__file__).parent / "locustfiles"
PROFILES_FILE = Path(__file__).parent / "config" / "profiles.yaml"

# make `from common import ...` (pre-test health check) work when the
# runner is invoked from the repo root
sys.path.insert(0, str(LOCUSTFILES_DIR))


def load_profile(name: str) -> dict:
    """Load a test profile from profiles.yaml."""
    try:
        import yaml

        with open(PROFILES_FILE) as f:
            data = yaml.safe_load(f)
        return data["profiles"].get(name, {})
    except ImportError:
        print("Warning: PyYAML not installed. Using hardcoded defaults.")
        return _default_profile(name)
    except FileNotFoundError:
        return _default_profile(name)


def _default_profile(name: str) -> dict:
    """Fallback profiles when YAML config is not available."""
    defaults = {
        "smoke": {"users": 10, "spawn_rate": 5, "run_time": "30s", "scenarios": ["scenario_mixed"]},
        "load": {"users": 50, "spawn_rate": 10, "run_time": "5m", "scenarios": ["scenario_mixed"]},
        "stress": {
            "users": 200,
            "spawn_rate": 20,
            "run_time": "10m",
            "scenarios": ["scenario_mixed"],
        },
    }
    return defaults.get(name, defaults["smoke"])


def run_locust(
    scenario: str,
    users: int,
    spawn_rate: int,
    run_time: str,
    host: str,
    csv_prefix: str | None = None,
    html_report: str | None = None,
    headless: bool = True,
) -> int:
    """Execute a Locust test run."""
    scenario_file = LOCUSTFILES_DIR / f"{scenario}.py"
    if not scenario_file.exists():
        print(f"Scenario not found: {scenario_file}")
        return 1

    cmd = [
        sys.executable,
        "-m",
        "locust",
        "-f",
        str(scenario_file),
        "--host",
        host,
    ]

    if headless:
        cmd.extend(["--headless"])

    cmd.extend(
        [
            "-u",
            str(users),
            "-r",
            str(spawn_rate),
            "--run-time",
            run_time,
        ]
    )

    if csv_prefix:
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        cmd.extend(["--csv", str(RESULTS_DIR / csv_prefix)])

    if html_report:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        cmd.extend(["--html", str(REPORTS_DIR / html_report)])

    print(f"\n{'=' * 60}")
    print(f"Running: {scenario}")
    print(f"Users: {users}, Spawn rate: {spawn_rate}, Duration: {run_time}")
    print(f"Host: {host}")
    print(f"{'=' * 60}\n")

    result = subprocess.run(cmd, cwd=str(LOCUSTFILES_DIR))
    return result.returncode


def run_profile(
    profile_name: str,
    host: str,
    report: bool = False,
    save_baseline: bool = False,
) -> int:
    """Run all scenarios in a profile.

    Follows load-testing best practices:
    1. Pre-test health check
    2. Execute scenarios
    3. Post-test analysis + report
    4. Baseline comparison + trend update
    """
    profile = load_profile(profile_name)
    if not profile:
        print(f"Profile not found: {profile_name}")
        return 1

    # Pre-test health check
    try:
        from common import check_target_health

        if not check_target_health(host):
            print("ERROR: Target environment is not healthy. Aborting.")
            return 1
    except ImportError:
        print("WARNING: Could not import health check — proceeding without")

    scenarios = profile.get("scenarios", ["scenario_mixed"])
    users = profile.get("users", 10)
    spawn_rate = profile.get("spawn_rate", 5)
    run_time = profile.get("run_time", "30s")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    exit_code = 0

    for scenario in scenarios:
        csv_prefix = f"{profile_name}_{scenario}_{timestamp}"
        html_path = f"{profile_name}_{scenario}_{timestamp}.html" if report else None

        rc = run_locust(
            scenario=scenario,
            users=users,
            spawn_rate=spawn_rate,
            run_time=run_time,
            host=host,
            csv_prefix=csv_prefix,
            html_report=html_path,
        )
        if rc != 0:
            exit_code = rc
            print(f"WARNING: {scenario} failed with exit code {rc}")

    # Post-test analysis — run whenever CSVs exist, even on FAILED runs:
    # a failing profile is exactly when the SLO verdict/report matters most
    # (the old `exit_code == 0` gate silently dropped reports — TASK-0140).
    try:
        from analyzer import (
            append_to_trend,
            check_slo,
            compare_with_baseline,
            generate_report,
            parse_locust_csv,
        )
        from analyzer import (
            save_baseline as persist_baseline,
        )

        csv_files = sorted(RESULTS_DIR.glob(f"{profile_name}_*_stats.csv"))
        if csv_files:
            results = parse_locust_csv(str(csv_files[-1]))
            slo_checks = check_slo(results)
            regressions = compare_with_baseline(results)
            append_to_trend(results)

            if report:
                report_text = generate_report(results, slo_checks, regressions)
                report_path = REPORTS_DIR / f"{profile_name}_{timestamp}.md"
                REPORTS_DIR.mkdir(parents=True, exist_ok=True)
                with open(report_path, "w") as f:
                    f.write(report_text)
                print(f"\nReport saved to: {report_path}")

            if save_baseline:
                # NB: the boolean arg is `save_baseline`; the imported
                # function is aliased `persist_baseline` to avoid shadowing
                # (the old call hit "bool not callable" — TASK-0140).
                persist_baseline(results)
                print("Baseline saved.")

            # Print summary
            slo_passed = sum(1 for c in slo_checks if c.passed)
            slo_total = len(slo_checks)
            print(f"\nSLO: {slo_passed}/{slo_total} met")
            if regressions:
                print(f"Regressions: {len(regressions)} detected — review report")
    except Exception as e:
        print(f"Post-test analysis failed: {e}")

    return exit_code


def main() -> None:
    parser = argparse.ArgumentParser(description="UPCP Performance Test Runner")
    parser.add_argument("--profile", "-p", help="Profile name from profiles.yaml")
    parser.add_argument("--scenario", "-s", help="Single scenario to run")
    parser.add_argument(
        "--host",
        default=os.getenv("LOCUST_HOST", "http://localhost:38082"),
        help="Target host URL (host-run default: test app on localhost; "
        "compose locust-master passes --host=http://app:8080 explicitly)",
    )
    parser.add_argument("--users", "-u", type=int, default=10, help="Number of concurrent users")
    parser.add_argument("--spawn-rate", "-r", type=int, default=5, help="Users spawned per second")
    parser.add_argument("--run-time", "-t", default="30s", help="Test duration (e.g. 30s, 5m)")
    parser.add_argument("--report", action="store_true", help="Generate markdown report")
    parser.add_argument("--save-baseline", action="store_true", help="Save results as new baseline")
    parser.add_argument("--web", action="store_true", help="Run with Locust web UI (not headless)")
    args = parser.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    if args.profile:
        sys.exit(run_profile(args.profile, args.host, args.report, args.save_baseline))
    elif args.scenario:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        rc = run_locust(
            scenario=args.scenario,
            users=args.users,
            spawn_rate=args.spawn_rate,
            run_time=args.run_time,
            host=args.host,
            csv_prefix=f"{args.scenario}_{timestamp}",
            headless=not args.web,
        )
        sys.exit(rc)
    else:
        print("Specify --profile or --scenario. Use --help for options.")
        sys.exit(1)


if __name__ == "__main__":
    main()
