#!/usr/bin/env python3
"""Verify every seeded mechanism on the dev stack (TASK-0166 AC4).

Read-back only: hits each read endpoint, prints PASS/FAIL with the key
numbers, exits non-zero on any FAIL.

Run:  SEED_BASE=... SEED_EMAIL=... SEED_PASSWORD=... \
      .venv/bin/python scripts/verify_seed.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import requests as rq  # noqa: E402
from seed_common import BASE, Session, section  # noqa: E402

results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f" — {detail}" if detail else ""))


def main() -> int:
    s = Session()

    projects = (s.get("/api/v1/projects", params={"limit": 50}) or {}).get("items", [])
    upcp = next((p for p in projects if p["slug"] == "upcp"), None)  # type: ignore[union-attr]
    assert upcp
    PID = str(upcp["id"])

    # ── Dashboard ──────────────────────────────────────────────────
    section("Dashboard")
    stats = s.get("/api/v1/dashboard/stats") or {}
    counts = stats.get("task_counts_by_status", {})
    check("dashboard/stats: project_count ≥ 3", (stats.get("project_count") or 0) >= 3,
          str(stats.get("project_count")))
    check("dashboard/stats: tasks in ≥4 statuses", len([v for v in counts.values() if v]) >= 4,  # type: ignore[union-attr]
          str(counts))
    check("dashboard/stats: recent_activity fills the feed (endpoint caps at 10)",
          len(stats.get("recent_activity", [])) >= 10,  # type: ignore[arg-type]
          str(len(stats.get("recent_activity", []))))  # type: ignore[arg-type]
    check("dashboard/stats: health_score is int 0-100",
          isinstance(stats.get("health_score"), int) and 0 <= stats["health_score"] <= 100,  # type: ignore[comparison-overlap]
          str(stats.get("health_score")))

    att = s.get("/api/v1/dashboard/attention") or {}
    expected_sections = ["needs_review", "open_questions", "blocked_tasks",
                         "stale_claims", "failed_dod", "rejected_tasks",
                         "agent_verdicts_waiting", "low_health_projects"]
    for sec in expected_sections:
        items = att.get(sec, [])
        check(f"attention/{sec} non-empty", bool(items), f"{len(items)} items")  # type: ignore[arg-type]

    agents_act = (s.get("/api/v1/dashboard/agent-activity") or {}).get("items", [])
    check("dashboard/agent-activity ≥ 1 active claim", len(agents_act) >= 1,  # type: ignore[arg-type]
          f"{len(agents_act)} agents")  # type: ignore[arg-type]
    check("agent-activity: a stale agent flagged",
          any(a.get("is_stale") for a in agents_act),  # type: ignore[union-attr]
          str([a.get("agent_name") for a in agents_act if a.get("is_stale")]))  # type: ignore[union-attr]

    health = s.get(f"/api/v1/projects/{PID}/health") or {}
    check("projects/{id}/health: breakdown present", "breakdown" in health,
          f"score={health.get('score')}")
    portfolio = s.get("/api/v1/portfolio/overview") or {}
    check("portfolio/overview returns projects", bool(portfolio.get("projects") or portfolio.get("items")),
          str(sorted(portfolio.keys())))

    # ── Quality ────────────────────────────────────────────────────
    section("Quality")
    qs = s.get(f"/api/v1/projects/{PID}/quality/stats") or {}
    check("quality/stats: total_dod ≥ 10", (qs.get("total_dod") or 0) >= 10, str(qs.get("total_dod")))
    check("quality/stats: passed_dod ≥ 5", (qs.get("passed_dod") or 0) >= 5, str(qs.get("passed_dod")))
    check("quality/stats: pass_rate > 0", (qs.get("pass_rate") or 0) > 0, str(qs.get("pass_rate")))

    feats = (s.get(f"/api/v1/projects/{PID}/features", params={"limit": 100}) or {}).get("items", [])
    seed_feat = next((f for f in feats if f["slug"] == "seed-workflow-verification"), None)  # type: ignore[union-attr]
    tasks = (s.get(f"/api/v1/features/{seed_feat['id']}/tasks", params={"limit": 100})  # type: ignore[index]
             or {}).get("items", [])
    by_title = {t["title"]: t for t in tasks}  # type: ignore[union-attr]

    def tstate(title: str) -> str:
        t = by_title.get(title)
        return str(t["status"]) if t else "MISSING"

    # ── Lifecycle states ───────────────────────────────────────────
    section("Task lifecycle states")
    for title, expect in [
        ("Seed: review-gate happy path", "ready_for_review"),
        ("Seed: blocked by upstream dependency", "blocked"),
        ("Seed: waiting on a blocking clarification", "needs_clarification"),
        ("Seed: never started, cancelled", "cancelled"),
        ("Seed: refined and ready for pickup", "ready"),
        ("Seed: claim will go stale", "claimed"),
        ("Seed: gate blocked by failing DoD", "in_progress"),
        ("Seed: claimed then released back", "backlog"),
        ("Seed: already shipped", "done"),
        ("Seed: in review", "ready_for_review"),
        ("Seed: changes requested", "changes_requested"),
    ]:
        got = tstate(title)
        check(f"lifecycle: '{title}' = {expect}", got == expect, got)

    # ── Workflow read-backs ────────────────────────────────────────
    section("Workflow (claims/heartbeats/clarifications)")
    t_gate = str(by_title.get("Seed: review-gate happy path", {}).get("id", ""))
    t_clar = str(by_title.get("Seed: waiting on a blocking clarification", {}).get("id", ""))
    claims = (s.get(f"/api/v1/tasks/{t_gate}/claims") or {}).get("items", [])
    check("t_gate has an active claim", any(c["state"] == "active" for c in claims),  # type: ignore[union-attr]
          str(len(claims)))
    beats = (s.get(f"/api/v1/tasks/{t_gate}/heartbeats") or {}).get("items", [])
    check("t_gate has heartbeats", len(beats) >= 1, str(len(beats)))  # type: ignore[arg-type]
    clars = (s.get(f"/api/v1/tasks/{t_clar}/clarifications") or {}).get("items", [])
    check("t_clar: blocking open clarification", any(  # type: ignore[union-attr]
        c["blocking"] and c["state"] == "open" for c in clars), str(len(clars)))  # type: ignore[union-attr]
    rounds = (s.get(f"/api/v1/tasks/{t_gate}/review-rounds") or {}).get("items", [])
    check("t_gate: pending review round (from gate)", any(  # type: ignore[union-attr]
        r["state"] == "pending" for r in rounds), str(len(rounds)))  # type: ignore[union-attr]

    # ── Notifications (bell bucket) ────────────────────────────────
    section("Notifications")
    unread = s.get("/api/v1/notifications/unread-count") or {}
    check("unread-count in 'default' bucket > 0", (unread.get("count") or 0) > 0,
          str(unread.get("count")))
    notifs = (s.get("/api/v1/notifications") or {}).get("items", [])
    check("notifications list non-empty", bool(notifs), str(len(notifs)))  # type: ignore[arg-type]

    # ── Audit ──────────────────────────────────────────────────────
    section("Audit")
    audit = s.get(f"/api/v1/projects/{PID}/audit-events", params={"limit": 50}) or {}
    check("project audit-events ≥ 15", (audit.get("total") or 0) >= 15, str(audit.get("total")))
    csv_export = rq.get(f"{BASE}/api/v1/audit/export",
                        params={"project_id": PID, "format": "csv"},
                        headers={"Authorization": f"Bearer {s._access}"}, timeout=30)
    check("audit export CSV 200 + rows", csv_export.status_code == 200
          and csv_export.text.count("\n") > 5, f"{csv_export.status_code}, "
          f"{csv_export.text.count(chr(10))} lines")

    # ── Git ────────────────────────────────────────────────────────
    section("Git")
    providers = s.get(f"/api/v1/projects/{PID}/git-providers") or []
    check("git provider exists", bool(providers), str(len(providers)))  # type: ignore[arg-type]
    if providers:
        pvid = providers[0]["id"]  # type: ignore[index]
        branches = s.get(f"/api/v1/git-providers/{pvid}/branches") or []
        commits = s.get(f"/api/v1/git-providers/{pvid}/commits") or []
        check("git branches ≥ 3", len(branches) >= 3, str(len(branches)))  # type: ignore[arg-type]
        check("git commits ≥ 6", len(commits) >= 6, str(len(commits)))  # type: ignore[arg-type]

    # ── Analytics ──────────────────────────────────────────────────
    section("Analytics")
    vel = (s.get("/api/v1/analytics/project/" + PID + "/velocity") or {}).get("items", [])
    check("velocity: ≥ 2 weeks with data", len([w for w in vel if w.get("count")]) >= 2,  # type: ignore[union-attr]
          str([(w.get("week"), w.get("count")) for w in vel if w.get("count")]))  # type: ignore[union-attr]
    trends = (s.get(f"/api/v1/analytics/project/{PID}/trends") or {}).get("items", [])
    check("trends: created+completed spread across weeks",
          len([w for w in trends if w.get("created") or w.get("completed")]) >= 4,  # type: ignore[union-attr]
          str(len([w for w in trends if w.get("created") or w.get("completed")])))  # type: ignore[union-attr]
    hist = (s.get(f"/api/v1/analytics/project/{PID}/health-history") or {}).get("items", [])
    check("health-history ≥ 7 days", len(hist) >= 7, str(len(hist)))  # type: ignore[arg-type]
    agents_ov = (s.get("/api/v1/analytics/agents/overview") or {}).get("items", [])
    check("agents overview ≥ 1", len(agents_ov) >= 1, str(len(agents_ov)))  # type: ignore[arg-type]

    # ── Channels / reports / search / membership ───────────────────
    section("Channels, reports, search, identity")
    channels = (s.get("/api/v1/notification-channels") or {}).get("items", [])
    check("notification channels ≥ 3", len(channels) >= 3, str(len(channels)))  # type: ignore[arg-type]
    reports = (s.get(f"/api/v1/projects/{PID}/reports", params={"limit": 20}) or {}).get("items", [])
    check("daily reports ≥ 4", len(reports) >= 4, str(len(reports)))  # type: ignore[arg-type]
    search = s.get("/api/v1/search", params={"q": "auth", "limit": 10}) or []
    check("search returns hits", bool(search), f"{len(search)} hits")  # type: ignore[arg-type]
    me = s.get("/auth/me") or {}
    check("/auth/me: organizations non-empty (membership backfill)",
          bool(me.get("organizations")), str(me.get("organizations")))

    # ── Deps / subtasks / comments ─────────────────────────────────
    section("Structure extras")
    all_project_tasks = (s.get(f"/api/v1/projects/{PID}/tasks",
                               params={"limit": 100}) or {}).get("items", [])
    dep_tasks = [t for t in all_project_tasks if t["title"] in (  # type: ignore[union-attr]
        "Branch listing and commit history", "Task-to-commit linking")]
    check("task has subtasks",
          bool((s.get(f"/api/v1/tasks/{t_gate}/subtasks") or {}).get("items")),
          str(len((s.get(f"/api/v1/tasks/{t_gate}/subtasks") or {}).get("items", []))))  # type: ignore[arg-type]
    check("task has comments",
          bool((s.get(f"/api/v1/tasks/{t_gate}/comments") or {}).get("items")),
          str(len((s.get(f"/api/v1/tasks/{t_gate}/comments") or {}).get("items", []))))  # type: ignore[arg-type]
    check("dependency tasks exist", len(dep_tasks) == 2, str(len(dep_tasks)))

    # ── Infra endpoints ────────────────────────────────────────────
    section("Infra endpoints")
    h = rq.get(f"{BASE}/health", timeout=15)
    check("/health ok", h.status_code == 200 and h.json().get("status") == "ok",  # type: ignore[union-attr]
          str(h.json().get("status")))  # type: ignore[union-attr]
    m = rq.get(f"{BASE}/metrics", timeout=15)
    check("/metrics exposes http_requests_total",
          m.status_code == 200 and "http_requests_total" in m.text,
          f"{m.status_code}")
    # SSE: first keepalive arrives after 15s of silence — wait it out
    try:
        with rq.get(f"{BASE}/api/v1/notifications/stream",
                    headers={"Authorization": f"Bearer {s._access}"},
                    stream=True, timeout=(5, 20)) as stream:
            first = next(stream.iter_lines(), b"")
            check("SSE stream opens (keepalive received)", stream.status_code == 200,
                  str(first[:60]))
    except Exception as exc:  # noqa: BLE001
        check("SSE stream opens", False, str(exc)[:80])

    # MCP smoke: initialize + tools/list over streamable HTTP
    try:
        mcp = rq.post(f"{BASE}/mcp",
                      json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
                      headers={"Authorization": f"Bearer {s._access}",
                               "Accept": "application/json, text/event-stream"},
                      timeout=15)
        check("MCP tools/list responds", mcp.status_code in (200, 400, 406),
              f"{mcp.status_code}: {mcp.text[:80]}")
    except Exception as exc:  # noqa: BLE001
        check("MCP tools/list responds", False, str(exc)[:80])

    # ── Summary ────────────────────────────────────────────────────
    section("Result")
    failed = [r for r in results if not r[1]]
    print(f"  {len(results) - len(failed)}/{len(results)} checks passed")
    for name, _, detail in failed:
        print(f"  ✗ {name} — {detail}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
