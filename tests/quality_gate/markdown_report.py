"""Markdown rendering for the quality-gate aggregate report (SPEC-0024 Phase 5).

Sections: header (profile/timestamp) → summary table → per-suite findings
bullets → regression-vs-baseline (human review, NO automatic thresholds)
→ missing-suite notes.
"""

from __future__ import annotations

SUITE_NAMES = ("performance", "chaos", "security")
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
MAX_DETAIL = 200


def _sev_rank(item: dict) -> int:
    return SEVERITY_ORDER.get(str(item.get("severity", "")).lower(), 9)


def _truncate(text: str) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= MAX_DETAIL else text[: MAX_DETAIL - 1] + "…"


def _findings_lines(suites: dict) -> list[str]:
    out: list[str] = []
    sec = suites["security"]
    findings = sorted(sec.get("findings", []), key=_sev_rank) if sec["status"] == "ok" else []
    for f in findings:
        sev = str(f.get("severity") or "unknown").upper()
        out.append(f"- **[{sev}] {f.get('title', '')}** ({f.get('category', '')})")
        detail = f.get("detail", "")
        if detail and detail != f.get("title"):
            out.append(f"  - {_truncate(detail)}")

    chaos = suites["chaos"]
    for fail in chaos.get("failures", []):
        mttr = fail.get("mttr_seconds")
        suffix = f" — MTTR {mttr:.1f}s" if isinstance(mttr, int | float) else ""
        out.append(f"- **chaos: {fail['experiment']}**{suffix}")
        bad = fail.get("failed_assertions", [])
        if bad:
            out.extend(f"  - {a.get('name')}: {a.get('message')}" for a in bad)
        elif fail.get("summary"):
            out.append(f"  - {fail['summary']}")

    perf = suites["performance"]
    if perf["status"] == "ok" and perf["summary"].get("regressions"):
        n = perf["summary"]["regressions"]
        out.append(
            f"- **performance:** {n} deviation(s) vs baseline — see *Regression vs baseline* below"
        )
    return out or ["- none."]


def _regression_lines(report: dict) -> list[str]:
    """Present only when performance results exist (nothing to compare otherwise)."""
    perf = report["suites"]["performance"]
    if perf["status"] != "ok":
        return []
    lines = [
        "## Regression vs baseline (human review)",
        "",
        "No automatic thresholds are applied to the numbers below: they are "
        "informational differences vs the tracked baseline, and a human decides "
        "whether each deviation is an acceptable regression.",
        "",
    ]
    if not perf["summary"].get("baseline_present"):
        lines.append(
            "No baseline — `baseline.json` not found; regression comparison not "
            "performed (new environment)."
        )
    elif not report["regressions"]:
        lines.append("No significant deviations vs the tracked baseline.")
    else:
        lines += [
            "| Metric | Baseline | Current | Change |",
            "|--------|----------|---------|--------|",
        ]
        lines += [
            f"| {r['metric']} | {r['baseline_value']:.1f} | {r['current_value']:.1f} "
            f"| {r['change_pct']:+.1f}% ({r['direction']}) |"
            for r in report["regressions"]
        ]
    lines.append("")
    return lines


def _missing_lines(suites: dict) -> list[str]:
    missing = [n for n in SUITE_NAMES if suites[n]["status"] == "missing"]
    if not missing:
        return []
    lines = ["## Missing suites", ""]
    for name in missing:
        results_dir = suites[name]["summary"].get("results_dir", "")
        lines.append(f"- **{name}** — no results found in `{results_dir}` (suite not yet run)")
    lines.append("")
    return lines


def render_markdown(report: dict) -> str:
    suites = report["suites"]
    lines = [
        "# Quality Gate Report",
        "",
        f"**Profile:** {report['profile']} · **Generated:** {report['generated_at']}",
        "",
        "## Summary",
        "",
        "| Suite | Checks | Passed | Failed | Findings | Status |",
        "|-------|--------|--------|--------|----------|--------|",
    ]
    for name in SUITE_NAMES:
        entry = suites[name]
        s = entry.get("summary", {})
        lines.append(
            f"| {name} | {s.get('checks', 0)} | {s.get('passed', 0)} | "
            f"{s.get('failed', 0)} | {s.get('findings', 0)} | {entry['status']} |"
        )
    lines += ["", "## Findings", ""]
    lines += _findings_lines(suites)
    lines.append("")
    lines += _regression_lines(report)
    lines += _missing_lines(suites)
    return "\n".join(lines).rstrip("\n") + "\n"
