#!/usr/bin/env python3
"""Seed dev with full agent-workflow mechanics + negative-path evidence.

Complements seed_dev.py (structure) and seed_full.py (quality depth):
this script exercises the *state machine* — task lifecycle transitions,
agent tokens, claims, heartbeats, clarifications, the review gate — and
prints expected-vs-actual statuses for every negative path.

Run:  SEED_BASE=... SEED_EMAIL=... SEED_PASSWORD=... \
      .venv/bin/python scripts/seed_mechanisms.py
Exit code: 0 = all negative-path expectations matched, 1 = mismatch.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import requests as rq  # noqa: E402
from seed_common import BASE, Session, section  # noqa: E402

FEATURE_NAME = "Seed — Workflow Verification"


def main() -> int:
    s = Session()
    uid = s.user_id
    email = str((s.get("/auth/me") or {}).get("email", "?"))
    print(f"Logged in as {email} ({uid[:8]}), base={BASE}")

    # ── Agents + tokens ────────────────────────────────────────────
    section("Agents & tokens")
    agents = (s.get("/api/v1/agents", params={"limit": 50}) or {}).get("items", [])
    tokens: dict[str, str] = {}
    for a in agents:  # type: ignore[union-attr]
        tok = s.post(f"/api/v1/agents/{a['id']}/tokens", {"name": f"seed-{a['name']}"},
                     expect=(201,))
        if tok:
            tokens[str(a["name"])] = str(tok["token"])
            print(f"  ✓ token for {a['name']}")
    if not tokens:
        print("FATAL: no agent tokens — cannot exercise workflow")
        return 1
    agent_by_name = {str(a["name"]): str(a["id"]) for a in agents}  # type: ignore[union-attr]
    commander, backend, qa = tokens["commander"], tokens["backend-dev"], tokens["qa-engineer"]

    # ── Feature for lifecycle tasks ────────────────────────────────
    section("Verification feature")
    project_id = _upcp(s)
    feats = (s.get(f"/api/v1/projects/{project_id}/features",
                   params={"limit": 100}) or {}).get("items", [])
    feat = next((f for f in feats if f["name"] == FEATURE_NAME), None)  # type: ignore[union-attr]
    if not feat:
        feat = s.post(f"/api/v1/projects/{project_id}/features", {
            "name": FEATURE_NAME, "slug": "seed-workflow-verification",
            "description": "Tasks exercising the full lifecycle for dev verification.",
            "status": "in_progress",
        }, expect=(201,))
    assert feat
    FID = str(feat["id"])

    def new_task(title: str, status: str = "backlog", assign_default: bool = False) -> str:
        """Create a task, or reuse an existing one with the same title
        (keeps re-runs from duplicating fixtures)."""
        existing = (s.get(f"/api/v1/features/{FID}/tasks",
                          params={"limit": 100}) or {}).get("items", [])
        for t in existing:  # type: ignore[union-attr]
            if t["title"] == title:
                return str(t["id"])
        body: dict[str, object] = {"title": title, "status": status, "priority": 5}
        if assign_default:
            # notification events resolve their target from assignee_id —
            # "default" is the bucket the frontend bell reads.
            body["assignee_type"] = "user"
            body["assignee_id"] = "default"
        t = s.post(f"/api/v1/features/{FID}/tasks", body, expect=(201,))
        assert t, f"task create failed: {title}"
        return str(t["id"])

    def patch_status(tid: str, st: str) -> None:
        if s.patch(f"/api/v1/tasks/{tid}", {"status": st}):
            print(f"  ✓ task {tid[:8]} → {st}")

    def claim(tid: str, tk: str) -> dict[str, object] | None:
        return s.request("POST", f"/api/v1/tasks/{tid}/claim", agent_token=tk,
                         json={}, expect=(201,))

    def beat(tid: str, tk: str, pct: int, step: str) -> dict[str, object] | None:
        return s.request("POST", f"/api/v1/tasks/{tid}/heartbeat", agent_token=tk,
                         json={"progress_percent": pct, "current_step": step,
                               "next_step": "continue"}, expect=(200,))

    # ── 1. Lifecycle: valid transitions through the PATCH API ──────
    section("Lifecycle transitions (valid paths)")
    t_gate = new_task("Seed: review-gate happy path", assign_default=True)
    t_block = new_task("Seed: blocked by upstream dependency", assign_default=True)
    t_clar = new_task("Seed: waiting on a blocking clarification", assign_default=True)
    t_cancel = new_task("Seed: never started, cancelled")
    t_ready = new_task("Seed: refined and ready for pickup")
    t_stale = new_task("Seed: claim will go stale", assign_default=True)
    t_dodneg = new_task("Seed: gate blocked by failing DoD", assign_default=True)
    new_task("Seed: already shipped", status="done")          # create allows any status
    new_task("Seed: in review", status="ready_for_review")    # (state machine is
    new_task("Seed: changes requested", status="changes_requested")  # PATCH-only)
    t_release = new_task("Seed: claimed then released back")

    patch_status(t_gate, "ready")
    patch_status(t_block, "ready")
    patch_status(t_clar, "ready")
    patch_status(t_cancel, "cancelled")   # backlog → cancelled
    patch_status(t_stale, "ready")
    patch_status(t_ready, "ready")
    patch_status(t_dodneg, "ready")
    patch_status(t_release, "ready")

    # ── 2. Claims + heartbeats (X-Agent-Token) ─────────────────────
    section("Claims & heartbeats (agent-token auth)")
    if claim(t_gate, commander):
        print("  ✓ t_gate claimed by commander (ready → claimed)")
        beat(t_gate, commander, 45, "Wiring the review gate")
        patch_status(t_gate, "in_progress")          # claimed → in_progress
    if claim(t_stale, qa):
        print("  ✓ t_stale claimed by qa-engineer (heartbeat backdated via SQL later)")
        beat(t_stale, qa, 10, "Kicked off — will go stale")
    if claim(t_clar, backend):
        print("  ✓ t_clar claimed by backend-dev")
        beat(t_clar, backend, 20, "Awaiting clarification")
        patch_status(t_clar, "in_progress")          # needed: blocking clarification
        #                                        requires in_progress → needs_clarification
    if claim(t_dodneg, commander):
        print("  ✓ t_dodneg claimed by commander (gate-DoD negative fixture)")
        beat(t_dodneg, commander, 30, "Prepping the failing-DoD fixture")
        patch_status(t_dodneg, "in_progress")
    if claim(t_block, tokens["devops"]):
        print("  ✓ t_block claimed by devops (→ in_progress → blocked below)")
        beat(t_block, tokens["devops"], 15, "Waiting on upstream infra")
        patch_status(t_block, "in_progress")
    if claim(t_release, tokens["devops"]):
        print("  ✓ t_release claimed by devops")
        rel = s.request("POST", f"/api/v1/tasks/{t_release}/release",
                        agent_token=tokens["devops"], json={}, expect=(200,))
        if rel:
            print("  ✓ t_release released → back to backlog (claim lifecycle)")

    # ── 3. Clarifications (agent token + active claim) ─────────────
    section("Clarifications")
    clar_open = s.request("POST", f"/api/v1/tasks/{t_clar}/clarifications",
                          agent_token=backend,
                          json={"question": "Should the webhook channel support mTLS?",
                                "context": "Dev-seed: blocking question for attention UI.",
                                "blocking": True},
                          expect=(201,))
    if clar_open:
        print("  ✓ blocking OPEN clarification → t_clar = needs_clarification")
    clar_done = s.request("POST", f"/api/v1/tasks/{t_gate}/clarifications",
                          agent_token=commander,
                          json={"question": "Which rint profile applies to scripts/?",
                                "context": "Dev-seed, non-blocking.", "blocking": False},
                          expect=(201,))
    if clar_done:
        ans = s.request("POST", f"/api/v1/clarifications/{clar_done['id']}/answer",
                        agent_token=commander,
                        json={"answer": "ruff default with line-length 100."},
                        expect=(200,))
        if ans:
            print("  ✓ clarification asked + answered (non-blocking)")

    # ── 4. Blocked task + failing DoD (attention: blocked, failed) ─
    section("Blocked task + failing DoD (attention fodder)")
    patch_status(t_block, "blocked")                 # in_progress → blocked
    for name, st in [("Integration tests pass", "failed"),
                     ("Security review done", "pending")]:
        d = s.post(f"/api/v1/tasks/{t_block}/dod-items", {"name": name}, expect=(201,))
        if d and st != "pending":
            s.patch(f"/api/v1/dod-items/{d['id']}", {"status": st})
        elif d:
            print(f"  ✓ DoD '{name}' left pending")
    dneg = s.post(f"/api/v1/tasks/{t_dodneg}/dod-items",
                  {"name": "Performance budget met"}, expect=(201,))
    if dneg:
        s.patch(f"/api/v1/dod-items/{dneg['id']}", {"status": "failed"})
        print("  ✓ t_dodneg DoD → failed (gate negative fixture)")

    # ── 5. Quality on t_gate → submit-review gate (positive) ───────
    section("Quality: DoD/AC/evidence → review gate")
    for name in ("Code reviewed", "Tests pass", "Docs updated"):
        d = s.post(f"/api/v1/tasks/{t_gate}/dod-items", {"name": name}, expect=(201,))
        if d:
            s.patch(f"/api/v1/dod-items/{d['id']}", {"status": "passed"})
    print("  ✓ 3 DoD items → passed")
    ac = s.post(f"/api/v1/tasks/{t_gate}/acceptance-criteria",
                {"description": "Gate returns 400 with machine-readable reason"},
                expect=(201,))
    if ac:
        s.patch(f"/api/v1/acceptance-criteria/{ac['id']}", {"status": "passed"})
        print("  ✓ AC created → passed")
    ev = s.post(f"/api/v1/tasks/{t_gate}/evidence", {
        "type": "url", "title": "Gate CI run",
        "url": "http://gitlab.local:8929/upcp/-/pipelines/519",
        "description": "Green quality gate pipeline",
        "created_by_type": "user", "created_by_id": uid,
    }, expect=(201,))
    if ev:
        s.post(f"/api/v1/evidence/{ev['id']}/agent-verify", {}, expect=(200,))
        s.post(f"/api/v1/evidence/{ev['id']}/human-accept", {}, expect=(200,))
        print("  ✓ evidence: created → agent_verified → human_accepted")
    ev2 = s.post(f"/api/v1/tasks/{t_block}/evidence", {
        "type": "text", "title": "Broken reproduction notes",
        "content_snippet": "Does not reproduce on dev.",
        "created_by_type": "user", "created_by_id": uid,
    }, expect=(201,))
    if ev2:
        s.post(f"/api/v1/evidence/{ev2['id']}/reject", {"reason": "Not reproducible"},
               expect=(200,))
        print("  ✓ evidence rejected (verification_state variety)")
    gate = s.post(f"/api/v1/tasks/{t_gate}/submit-review", {}, expect=(201,))
    if gate:
        print(f"  ✓ review gate PASSED → t_gate ready_for_review, "
              f"round {gate['id'][:8]} state={gate['state']}")

    # ── 6. Review verdicts (reject / agent-approver / pending) ─────
    section("Review rounds & verdicts")
    rnd = s.post(f"/api/v1/tasks/{t_block}/review-rounds",
                 {"reviewer_type": "human", "reviewer_id": uid}, expect=(201,))
    if rnd:
        s.post(f"/api/v1/review-rounds/{rnd['id']}/start", {}, expect=(200,))
        s.post(f"/api/v1/review-rounds/{rnd['id']}/findings", {
            "severity": "major", "category": "correctness",
            "message": "Task can stay blocked forever without an unblock path",
            "suggestion": "Add explicit unblock transition",
        }, expect=(201,))
        s.post(f"/api/v1/review-rounds/{rnd['id']}/verdict", {
            "verdict": "reject", "confidence": 80,
            "summary": "Needs the unblock path before merge.",
        }, expect=(200,))
        print("  ✓ round: pending → in_progress → findings → verdict=reject")
    arnd = s.post(f"/api/v1/tasks/{t_stale}/review-rounds",
                  {"reviewer_type": "agent", "reviewer_id": agent_by_name["qa-engineer"]},
                  expect=(201,))
    if arnd:
        s.post(f"/api/v1/review-rounds/{arnd['id']}/start", {}, expect=(200,))
        s.post(f"/api/v1/review-rounds/{arnd['id']}/verdict", {
            "verdict": "approve", "confidence": 92,
            "summary": "Dev-seed: agent verdict awaiting human confirmation.",
        }, expect=(200,))
        print("  ✓ agent-reviewer round completed (attention: verdicts waiting)")
    if s.post(f"/api/v1/tasks/{t_ready}/review-rounds",
              {"reviewer_type": "human", "reviewer_id": uid}, expect=(201,)):
        print("  ✓ PENDING round on t_ready (attention: needs review)")

    # ── 7. Comments + subtasks + bulk ──────────────────────────────
    section("Comments, subtasks, bulk update")
    for text in ["Picked this up for the dev seed.",
                 "Second comment: gate contract verified."]:
        s.request("POST", f"/api/v1/tasks/{t_gate}/comments",
                  params={"body": text, "author_type": "human", "author_id": uid},
                  expect=(201,))
    print("  ✓ 2 comments")
    for title, st in [("Draft contract test", "done"), ("Wire fixture", "in_progress"),
                      ("Review with QA", "todo")]:
        s.post(f"/api/v1/tasks/{t_gate}/subtasks",
               {"title": title, "status": st}, expect=(201,))
    print("  ✓ 3 subtasks (todo/in_progress/done)")
    if s.patch("/api/v1/tasks/bulk",
               {"task_ids": [t_ready], "updates": {"priority": 8}}, expect=(200,)):
        print("  ✓ bulk update (priority → 8)")

    # ── 8. Reports for every project ───────────────────────────────
    section("Reports")
    projects = (s.get("/api/v1/projects", params={"limit": 50}) or {}).get("items", [])
    for p in projects:  # type: ignore[union-attr]
        rep = s.post(f"/api/v1/projects/{p['id']}/reports/daily", {}, expect=(201,))
        if rep:
            print(f"  ✓ daily report for {p['name']} ({rep['id'][:8]})")

    # ── 9. Negative paths — expected vs actual ─────────────────────
    section("Negative paths (expected vs actual)")
    results: list[tuple[str, int, int]] = []

    def raw(method: str, path: str, expected: int, name: str,
            agent_token: str | None = None, **kw: object) -> None:
        hdr = ({"X-Agent-Token": agent_token} if agent_token
               else {"Authorization": f"Bearer {s._access}"})
        resp = rq.request(method, f"{BASE}{path}", headers=hdr, **kw)  # type: ignore[arg-type]
        mark = "✓" if resp.status_code == expected else "✗"
        print(f"  {mark} {name}: expected {expected}, got {resp.status_code}")
        results.append((name, expected, resp.status_code))

    raw("POST", f"/api/v1/tasks/{t_cancel}/claim", 409,
        "claim a cancelled task", agent_token=commander, json={})
    raw("POST", f"/api/v1/tasks/{t_ready}/claim", 401,
        "claim without agent token", json={})
    raw("POST", "/api/v1/tasks/00000000-0000-0000-0000-000000000000/claim", 404,
        "claim unknown task", agent_token=commander, json={})
    raw("PATCH", f"/api/v1/tasks/{t_gate}", 422,
        "invalid transition ready_for_review → backlog", json={"status": "backlog"})
    raw("POST", f"/api/v1/tasks/{t_block}/submit-review", 400,
        "review gate: task blocked", json={})
    raw("POST", f"/api/v1/tasks/{t_dodneg}/submit-review", 400,
        "review gate: DoD not passed", json={})
    raw("POST", f"/api/v1/tasks/{t_block}/complete", 400,
        "complete: failing DoD items", json={})
    raw("PATCH", "/api/v1/tasks/00000000-0000-0000-0000-000000000000", 404,
        "update unknown task", json={"status": "ready"})
    raw("PATCH", "/api/v1/dod-items/nope", 404, "update unknown DoD item",
        json={"status": "passed"})
    raw("PATCH", "/api/v1/acceptance-criteria/nope", 404, "update unknown AC",
        json={"status": "passed"})
    raw("GET", "/api/v1/projects/00000000-0000-0000-0000-000000000000/health", 404,
        "health of unknown project")

    failed = [n for n, e, a in results if e != a]
    print(f"\n  negative paths: {len(results) - len(failed)}/{len(results)} "
          f"matched expectations")

    # ── Summary (ids for SQL backfill + verification) ──────────────
    section("Summary")
    for name, tid in [("t_gate", t_gate), ("t_block", t_block), ("t_clar", t_clar),
                      ("t_cancel", t_cancel), ("t_ready", t_ready),
                      ("t_stale", t_stale)]:
        print(f"  {name} = {tid}")
    print("  SQL backfill still required: membership, audit_event, git branches/"
          "\n  commits, task_dependency, analytics backdating, stale heartbeat on "
          f"t_stale {t_stale[:8]}.")
    return 1 if failed else 0


def _upcp(s: Session) -> str:
    projects = (s.get("/api/v1/projects", params={"limit": 50}) or {}).get("items", [])
    p = next((x for x in projects if x["slug"] == "upcp"), None)  # type: ignore[union-attr]
    assert p, "UPCP project not found — run scripts/seed_dev.py first"
    return str(p["id"])


if __name__ == "__main__":
    raise SystemExit(main())
