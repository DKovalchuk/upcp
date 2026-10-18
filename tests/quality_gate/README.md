# tests/quality_gate — aggregate results reporter

SPEC-0024 Phase 5 (TASK-0143). Combines the machine-readable results of the
three quality-gate suites into **one human-reviewable Markdown report** and
**one machine-readable JSON report**. Pure stdlib (json/argparse/pathlib);
reuses `tests/performance/analyzer.py` via `sys.path` (same pattern as
`tests/security/runner.py` and `tests/chaos/runner.py`).

## CLI

```bash
python tests/quality_gate/aggregate.py --results-root tests --out-dir . [--profile quick|full]
```

| Flag | Default | Meaning |
|------|---------|---------|
| `--results-root` | `tests` | dir containing `<suite>/results/` |
| `--out-dir` | `.` | where `quality-report.md` + `quality-report.json` are written |
| `--profile` | `quick` | report label only (`quick` = develop gate, `full` = nightly); does not filter inputs |

## Inputs (newest file by **mtime** wins)

- `performance/results/*_stats.csv` — newest Locust stats CSV, parsed with
  `analyzer.parse_locust_csv()`; `analyzer.check_slo()` fills checks;
  `performance/results/baseline.json` (optional) feeds
  `analyzer.compare_with_baseline()` for regressions.
- `chaos/results/chaos_*.json` — newest chaos run (`total/passed/failed/experiments[]`).
- `security/results/{authz,fuzz,zap,kali}_*.json` — newest per sub-suite name,
  schema `upcp-security-result/v1` (`checks[]/findings[]/summary{total,passed,failed}`).

A suite with no results at all is reported with `"status": "missing"` — the
partial report is still written (CI runs the job `when: always`).

## Outputs

`quality-report.json` — schema `upcp-quality-report/v1`:

```json
{"schema": "upcp-quality-report/v1", "generated_at": "<iso8601 Z>", "profile": "quick|full",
 "suites": {"performance|chaos|security": {"status": "ok|missing", "source_file": "<relpath>",
            "summary": {...}, "passed": true|false|null}},
 "regressions": [{"metric", "baseline_value", "current_value", "change_pct", "direction"}],
 "counts": {"suites_ok", "suites_missing", "findings_total", "checks_passed", "checks_total"}}
```

`quality-report.md` — header (profile/timestamp) → summary table
(suite | checks | passed | failed | findings | status) → findings bullets
(all security findings by severity, chaos failures, perf deviations) →
*Regression vs baseline (human review)* → missing-suite notes. The regression
section **applies no automatic thresholds** — a human decides; it is omitted
entirely when performance results are missing, and says "no baseline" when
`baseline.json` is absent.

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | report written — findings/failures do NOT change the exit code (the CI gate job decides from suite exit codes) |
| 2 | internal error: results root missing, unreadable/corrupt input, unexpected exception |

## Tests

```bash
.venv/bin/python -m pytest tests/quality_gate -o addopts= -o pythonpath= -q
.venv/bin/ruff check tests/quality_gate && .venv/bin/ruff format tests/quality_gate
```

`test_aggregate.py` builds synthetic fixtures in `tmp_path` mimicking each
suite's real format (see docstring). Note: `backend` must stay off
`sys.path` (the `-o pythonpath=` flag above) or `tests` would resolve to
`backend/tests`.
