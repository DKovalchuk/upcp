"""Tests for the quality-gate aggregate reporter (TASK-0143 / SPEC-0024 Phase 5).

Fixtures mimic the real suite formats: Locust `*_stats.csv` +
`baseline.json` (analyzer schema), `chaos_<ts>.json` (chaos runner),
`<suite>_<ts>.json` with schema `upcp-security-result/v1` (security runner).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tests.quality_gate.aggregate import main  # noqa: E402

PERF_HEADER = "Type,Name,Request Count,Failure Count,Median Response Time,Average Response Time,Min Response Time,Max Response Time,Average Content Size,Requests/s,Failures/s,50%,66%,75%,80%,90%,95%,98%,99%,99.9%,99.99%,100%\n"

T_NEW = 2_000_000_000  # newer mtime
T_OLD = 1_000_000_000  # older mtime
ALPHA_ROW = ("alpha", 10, 0, 1.0, 5.0, 4.0, 50.0, 90.0)
GAMMA_ROW = ("gamma", 10, 0, 1.0, 5.0, 4.0, 50.0, 90.0)
PASS_A = {"name": "a1", "passed": True, "actual": "1", "expected": "1", "message": "m"}
PASS_A2 = {"name": "a2", "passed": True, "actual": "1", "expected": "1", "message": "m"}
FAIL_A = {"name": "mttr_app", "passed": False, "actual": "60", "message": "MTTR too high"}
EXP_OK = {"experiment": "exp_ok", "passed": True, "assertions": [PASS_A]}
EXP_BAD = {"experiment": "exp_bad", "passed": False, "assertions": [PASS_A2, FAIL_A]}
EXP_NEW = {"experiment": "exp_new", "passed": True, "assertions": []}
EXP_OLD = {"experiment": "exp_old", "passed": True, "assertions": []}
FULL_ROWS = [
    ("alpha", 100, 0, 10.0, 50.0, 40.0, 100.0, 200.0),
    ("beta", 50, 0, 5.0, 3000.0, 1000.0, 3000.0, 6000.0),
    ("Aggregated", 150, 0, 15.0, 60.0, 14.0, 900.0, 1200.0),
]
BASELINE_ROWS = [
    {"name": "alpha", "p95_ms": 50.0, "error_rate_pct": 0.0, "rps": 10.0},
    {"name": "beta", "p95_ms": 3000.0, "error_rate_pct": 0.0, "rps": 5.0},
]


def _perf_csv(results_root: Path, filename: str, rows: list[tuple], mtime: int) -> Path:
    """rows: (name, req, fail, rps, avg, p50, p95, p99)."""
    path = results_root / "performance" / "results" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "".join(
        f"POST,{n},{req},{fail},{p50},{avg},{p50},{p99},100,{rps},0.0,"
        f"{p50},{p50},{p50},{p50},{p50},{p95},{p99},{p99},{p99},{p99},{p99}\n"
        for (n, req, fail, rps, avg, p50, p95, p99) in rows
    )
    path.write_text(PERF_HEADER + body)
    os.utime(path, (mtime, mtime))
    return path


def _baseline(results_root: Path, entries: list[dict]) -> Path:
    path = results_root / "performance" / "results" / "baseline.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"timestamp": "2026-10-18T00:00:00", "results": entries}))
    return path


def _chaos(results_root: Path, filename: str, experiments: list[dict], mtime: int) -> Path:
    path = results_root / "chaos" / "results" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "timestamp": "2026-10-18T06:00:00",
        "total": len(experiments),
        "passed": sum(1 for e in experiments if e.get("passed")),
        "failed": sum(1 for e in experiments if not e.get("passed")),
        "experiments": experiments,
    }
    path.write_text(json.dumps(data))
    os.utime(path, (mtime, mtime))
    return path


def _security(
    results_root: Path, filename: str, suite: str, passed: int, failed: int, finding: str
) -> Path:
    """Build one upcp-security-result/v1 doc (findings == failed checks)."""
    path = results_root / "security" / "results" / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    checks = [{"name": f"{suite} ok", "category": "c", "status": "pass", "severity": ""}] * passed
    checks += [
        {"name": f"{suite} fail", "category": "c", "status": "fail", "severity": "high"}
    ] * failed
    data = {
        "schema": "upcp-security-result/v1",
        "suite": suite,
        "target": "http://localhost:38082",
        "checks": checks,
        "findings": [{"severity": "high", "title": finding, "category": "c", "detail": "d"}]
        * failed,
        "summary": {"total": passed + failed, "passed": passed, "failed": failed},
    }
    path.write_text(json.dumps(data))
    return path


def _run(results_root: Path, out_dir: Path, *extra: str) -> tuple[int, dict | None, str]:
    rc = main(["--results-root", str(results_root), "--out-dir", str(out_dir), *extra])
    jp, mp = out_dir / "quality-report.json", out_dir / "quality-report.md"
    data = json.loads(jp.read_text()) if jp.exists() else None
    md = mp.read_text() if mp.exists() else ""
    return rc, data, md


def _full_fixture(results_root: Path) -> None:
    """perf (2 scenarios + Aggregated) + baseline, chaos (1 ok 1 bad), security (authz+fuzz)."""
    _perf_csv(results_root, "load_20260101_000000_stats.csv", FULL_ROWS, T_NEW)
    _baseline(results_root, BASELINE_ROWS)
    _chaos(results_root, "chaos_20260101_000000.json", [EXP_OK, EXP_BAD], T_NEW)
    _security(results_root, "authz_20260101_000000.json", "authz", 2, 1, "authz: role bypass")
    _security(results_root, "fuzz_20260101_000000.json", "fuzz", 1, 1, "fuzz: sqli probe")


def test_newest_file_selected_by_mtime(tmp_path: Path) -> None:
    """Two runs per suite → newer mtime wins (even when the name sorts earlier)."""
    _perf_csv(tmp_path, "load_20260101_stats.csv", [ALPHA_ROW], T_NEW)
    _perf_csv(tmp_path, "load_20261231_stats.csv", [GAMMA_ROW], T_OLD)
    _chaos(tmp_path, "chaos_20260101_000000.json", [EXP_NEW], T_NEW)
    _chaos(tmp_path, "chaos_20261231_000000.json", [EXP_OLD], T_OLD)

    rc, data, _ = _run(tmp_path, tmp_path / "out")

    assert rc == 0
    assert data["suites"]["performance"]["source_file"].endswith("load_20260101_stats.csv")
    assert data["suites"]["chaos"]["source_file"].endswith("chaos_20260101_000000.json")
    assert data["suites"]["chaos"]["summary"]["checks"] == 1
    assert not Path(data["suites"]["chaos"]["source_file"]).is_absolute()  # relpath, not abs


def test_security_latest_per_suite_name(tmp_path: Path) -> None:
    _security(tmp_path, "authz_20260101.json", "authz", 2, 1, "newer authz finding")
    _security(tmp_path, "authz_20261231.json", "authz", 0, 2, "older authz finding")
    _security(tmp_path, "fuzz_20260606.json", "fuzz", 1, 0, "fuzz finding")
    for f in (tmp_path / "security" / "results").glob("authz_*.json"):
        os.utime(f, (T_NEW if "20260101" in f.name else T_OLD,) * 2)

    rc, data, _ = _run(tmp_path, tmp_path / "out")

    assert rc == 0
    sec = data["suites"]["security"]
    assert sec["status"] == "ok"
    assert set(sec["summary"]["subsuites"]) == {"authz", "fuzz"}
    assert sec["summary"]["subsuites"]["authz"]["source_file"].endswith("authz_20260101.json")
    # newer authz (1 finding) wins over older (2 findings) → 1 + 0 from fuzz
    assert sec["summary"]["findings"] == 1
    assert sec["findings"][0]["title"] == "newer authz finding"


def test_missing_suites_reported_exit_zero(tmp_path: Path) -> None:
    rc, data, md = _run(tmp_path, tmp_path / "out")

    assert rc == 0
    assert data["schema"] == "upcp-quality-report/v1"
    assert all(s["status"] == "missing" for s in data["suites"].values())
    assert data["counts"] == {
        "suites_ok": 0,
        "suites_missing": 3,
        "findings_total": 0,
        "checks_passed": 0,
        "checks_total": 0,
    }
    assert data["regressions"] == []
    assert "Missing suites" in md and "no results" in md
    assert "Regression vs baseline" not in md  # no perf results → no regression section
    assert data["suites"]["chaos"]["passed"] is None


def test_findings_and_counts_aggregated(tmp_path: Path) -> None:
    _full_fixture(tmp_path)

    rc, data, md = _run(tmp_path, tmp_path / "out")

    assert rc == 0, "findings/failures must not change the exit code"
    assert data["counts"] == {
        "suites_ok": 3,
        "suites_missing": 0,
        "findings_total": 4,  # 2 security + 1 chaos assertion + 1 perf regression
        "checks_passed": 8,  # 4 SLO + 1 experiment + 3 checks
        "checks_total": 13,  # 6 SLO + 2 experiments + 5 checks
    }
    assert data["regressions"][0]["metric"] == "alpha.p95_ms"
    assert data["suites"]["performance"]["passed"] is False  # beta p95/p99 SLO warnings fail
    assert data["suites"]["chaos"]["passed"] is False
    assert data["suites"]["security"]["passed"] is False
    assert "authz: role bypass" in md and "fuzz: sqli probe" in md
    assert "exp_bad" in md and "MTTR too high" in md


def test_regression_section_with_baseline(tmp_path: Path) -> None:
    _full_fixture(tmp_path)

    _, _, md = _run(tmp_path, tmp_path / "out")

    assert "Regression vs baseline (human review)" in md
    assert "alpha.p95_ms" in md
    assert "human" in md.lower()
    assert "No automatic" in md  # stresses: no automatic thresholds, human decides


def test_regression_section_says_no_baseline(tmp_path: Path) -> None:
    _perf_csv(tmp_path, "load_stats.csv", [ALPHA_ROW], T_NEW)

    rc, data, md = _run(tmp_path, tmp_path / "out")

    assert rc == 0
    assert data["suites"]["performance"]["summary"]["baseline_present"] is False
    assert data["regressions"] == []
    assert "Regression vs baseline (human review)" in md
    assert "no baseline" in md.lower()


def test_json_schema_contract(tmp_path: Path) -> None:
    _full_fixture(tmp_path)

    _, data, _ = _run(tmp_path, tmp_path / "out", "--profile", "full")

    for key in ("schema", "generated_at", "profile", "suites", "regressions", "counts"):
        assert key in data
    assert data["schema"] == "upcp-quality-report/v1"
    assert data["profile"] == "full"
    assert data["generated_at"].endswith("Z")
    assert data["generated_at"] == data["generated_at"].replace(" ", "T")  # iso8601
    for suite in data["suites"].values():
        assert {"status", "source_file", "summary", "passed"} <= set(suite)
        assert suite["status"] in ("ok", "missing")
    assert set(data["counts"]) == {
        "suites_ok",
        "suites_missing",
        "findings_total",
        "checks_passed",
        "checks_total",
    }


def test_markdown_summary_table(tmp_path: Path) -> None:
    _full_fixture(tmp_path)

    _, _, md = _run(tmp_path, tmp_path / "out")

    assert md.startswith("# Quality Gate Report")
    assert "**Profile:** quick" in md  # default profile label
    assert "| Suite | Checks | Passed | Failed | Findings | Status |" in md
    assert all(f"| {s} |" in md for s in ("performance", "chaos", "security"))
    assert "| ok |" in md


def test_errors_exit_2(tmp_path: Path) -> None:
    # unreadable (corrupt) required input
    path = tmp_path / "chaos" / "results" / "chaos_20260101_000000.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not valid json")
    assert _run(tmp_path, tmp_path / "out")[0] == 2
    # missing results root = unreadable required input
    assert _run(tmp_path / "no-such-dir", tmp_path / "out2")[0] == 2


def test_cli_end_to_end_subprocess(tmp_path: Path) -> None:
    _full_fixture(tmp_path)
    out = tmp_path / "ci-out"
    script = REPO_ROOT / "tests" / "quality_gate" / "aggregate.py"
    args = [sys.executable, str(script), "--results-root", str(tmp_path), "--out-dir", str(out)]
    proc = subprocess.run(args, capture_output=True, text=True, cwd=REPO_ROOT)

    assert proc.returncode == 0, proc.stderr
    assert (out / "quality-report.md").exists()
    assert (out / "quality-report.json").exists()
