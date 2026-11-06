#!/usr/bin/env python3
"""Comprehensive seed for UPCP — fills ALL views with realistic data.

Run scripts/seed_dev.py first (structure), then this script (quality depth:
subtasks, DoD, AC, evidence with verification states, review rounds with
findings and verdicts, notification channels, git provider, reports).

Workflow mechanics (claims/heartbeats/clarifications) live in
scripts/seed_mechanisms.py — they need agent tokens.

Env: SEED_BASE, SEED_EMAIL, SEED_PASSWORD (see docs/ENVIRONMENTS.md).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from seed_common import Session, section  # noqa: E402

s = Session()
UID = s.user_id


def post(path, data):
    return s.post(path, data)


def get(path, **kw):
    return s.get(path, params=kw or None)


def patch(path, data):
    return s.patch(path, data)


# ── Find UPCP project ──────────────────────────────
projects = get("/api/v1/projects", limit=50)
upcp = next((p for p in projects.get("items", []) if p["slug"] == "upcp"), None)
if not upcp:
    sys.exit("ERROR: UPCP project not found. Run seed_dev.py first.")
PID = upcp["id"]
print(f"✓ Project: UPCP ({PID[:8]})")

# ── Find existing features + tasks ─────────────────
features = get(f"/api/v1/projects/{PID}/features", limit=50)
feature_list = features.get("items", []) if isinstance(features, dict) else []
print(f"✓ Features: {len(feature_list)}")

all_tasks = []
for feat in feature_list:
    tasks = get(f"/api/v1/features/{feat['id']}/tasks", limit=50)
    task_list = tasks.get("items", []) if isinstance(tasks, dict) else []
    for t in task_list:
        all_tasks.append({**t, "feature_id": feat["id"], "feature_name": feat["name"]})
task_map = {t["title"]: t for t in all_tasks}
print(f"✓ Tasks: {len(all_tasks)}")

# ── Agents ─────────────────────────────────────────
agents = get("/api/v1/agents", limit=50)
agent_list = agents.get("items", []) if isinstance(agents, dict) else []
agent_map = {a["name"]: a for a in agent_list}
print(f"✓ Agents: {len(agent_list)}")

# ── Subtasks ───────────────────────────────────────
section("Subtasks")
subtask_defs = {
    "JWT login + refresh token flow": [
        ("Implement POST /auth/login endpoint", "done"),
        ("Implement POST /auth/refresh endpoint", "done"),
        ("Add JWT token generation with RS256", "done"),
        ("Write unit tests for auth flow", "done"),
    ],
    "Feature CRUD with type/status/priority": [
        ("Design Feature model schema", "done"),
        ("Implement create/read endpoints", "done"),
        ("Add update and soft-delete", "done"),
        ("Write integration tests", "done"),
    ],
    "Notification channels (email, webhook)": [
        ("Design channel model and config schema", "done"),
        ("Implement email channel adapter", "in_progress"),
        ("Implement webhook channel adapter", "backlog"),
        ("Add channel toggle and test endpoints", "done"),
    ],
    "Agent playbook system": [
        ("Define playbook YAML schema", "done"),
        ("Implement playbook loader", "in_progress"),
        ("Add playbook execution engine", "backlog"),
        ("Create default playbooks for common tasks", "backlog"),
    ],
}
for task_title, subs in subtask_defs.items():
    t = task_map.get(task_title)
    if not t:
        continue
    for sub_title, sub_status in subs:
        if post(f"/api/v1/tasks/{t['id']}/subtasks",
                {"title": sub_title, "status": sub_status}):
            print(f"  ✓ Subtask: {sub_title[:40]} [{sub_status}]")

# ── DoD items — contract: {"name"} + PATCH status ──
section("Definition of Done")
dod_defs = {
    "JWT login + refresh token flow": [("Code reviewed", "passed"),
                                       ("Tests pass", "passed"),
                                       ("Documentation updated", "passed")],
    "Rate limiting (5/min login, 60/min API)": [("Code reviewed", "passed"),
                                                ("Tests pass", "passed"),
                                                ("Performance benchmarked", "passed")],
    "Project CRUD with slug generation": [("Code reviewed", "passed"),
                                          ("Tests pass", "passed"),
                                          ("OpenAPI spec updated", "passed")],
    "Evidence upload (file, URL, text)": [("Code reviewed", "passed"),
                                          ("Tests pass", "failed"),
                                          ("E2E tests added", "pending")],
    "Notification channels (email, webhook)": [("Code reviewed", "passed"),
                                               ("Tests pass", "failed"),
                                               ("Channel adapter tested", "pending")],
    "Agent playbook system": [("Schema validated", "passed"),
                              ("Loader implemented", "failed"),
                              ("Default playbooks created", "pending")],
}
for task_title, items in dod_defs.items():
    t = task_map.get(task_title)
    if not t:
        continue
    for item_name, status in items:
        d = post(f"/api/v1/tasks/{t['id']}/dod-items", {"name": item_name})
        if d:
            if status != "pending":
                patch(f"/api/v1/dod-items/{d['id']}", {"status": status})
            print(f"  ✓ DoD: {item_name} [{status}]")

# ── Acceptance criteria — create(description) + PATCH status ──
section("Acceptance criteria")
ac_defs = {
    "JWT login + refresh token flow": [
        ("User can login with email/password and receive JWT token", "passed"),
        ("Token refresh returns new access_token before expiry", "passed"),
        ("Invalid credentials return 401 with clear error message", "passed"),
    ],
    "RBAC roles and permission checks": [
        ("Admin can create/edit/delete all resources", "passed"),
        ("Viewer can only read, not modify", "passed"),
        ("Role assignments are enforced on every endpoint", "passed"),
    ],
    "Evidence upload (file, URL, text)": [
        ("File upload stores artifact and creates Evidence record", "passed"),
        ("URL evidence fetches and caches content", "pending"),
        ("Evidence can be verified by agent or human", "passed"),
    ],
    "Notification channels (email, webhook)": [
        ("Channel CRUD with config validation", "passed"),
        ("Toggle enables/disables channel delivery", "passed"),
        ("Test endpoint sends probe notification", "pending"),
    ],
}
for task_title, criteria in ac_defs.items():
    t = task_map.get(task_title)
    if not t:
        continue
    for desc, status in criteria:
        ac = post(f"/api/v1/tasks/{t['id']}/acceptance-criteria",
                  {"description": desc})
        if ac:
            if status != "pending":
                patch(f"/api/v1/acceptance-criteria/{ac['id']}", {"status": status})
            print(f"  ✓ AC: {desc[:50]} [{status}]")

# ── Evidence — created_by_id is REQUIRED ───────────
section("Evidence (all verification states)")
evidence_defs = [
    ("JWT login + refresh token flow", [
        {"type": "url", "title": "Auth flow test results",
         "url": "https://ci.example.com/builds/12345",
         "description": "All auth tests pass in CI",
         "state": "human_accepted"},
        {"type": "text", "title": "Manual verification",
         "content_snippet": "Verified login/logout/refresh cycle with curl and Playwright",
         "state": "agent_verified"},
    ]),
    ("Evidence upload (file, URL, text)", [
        {"type": "url", "title": "Upload endpoint documentation",
         "url": "https://docs.upcp.local/api/evidence",
         "description": "API docs for evidence upload",
         "state": "unverified"},
        {"type": "text", "title": "Partial implementation note",
         "content_snippet": "File upload works for text. Binary needs testing.",
         "state": "rejected", "reject_reason": "Binary path still broken"},
    ]),
    ("Rate limiting (5/min login, 60/min API)", [
        {"type": "text", "title": "Rate limit test output",
         "content_snippet": "6th login attempt within 60s returns 429 with retry_after=60.",
         "state": "human_accepted"},
    ]),
]
for task_title, ev_list in evidence_defs:
    t = task_map.get(task_title)
    if not t:
        continue
    for ev in ev_list:
        state = ev.pop("state")
        e = post(f"/api/v1/tasks/{t['id']}/evidence", {
            **ev, "created_by_type": "user", "created_by_id": UID})
        if not e:
            continue
        eid = e["id"]
        if state == "agent_verified":
            post(f"/api/v1/evidence/{eid}/agent-verify", {})
        elif state == "human_accepted":
            post(f"/api/v1/evidence/{eid}/agent-verify", {})
            post(f"/api/v1/evidence/{eid}/human-accept", {})
        elif state == "rejected":
            post(f"/api/v1/evidence/{eid}/reject",
                 {"reason": ev.pop("reject_reason", "stale")})
        print(f"  ✓ Evidence: {e['title'][:40]} → {state}")

# ── Review rounds: create → start → findings → verdict ──
section("Review rounds (findings + verdicts)")
review_defs = [
    ("RBAC roles and permission checks", "approve", 95,
     "RBAC enforcement verified across all endpoints.",
     [("major", "security", "Role check missing on /agents/{id}/tokens DELETE"),
      ("minor", "style", "Inconsistent error message wording")]),
    ("Project health scoring algorithm", "needs_changes", 70,
     "Health score math is right but stale-claim weight needs tests.",
     [("minor", "completeness", "No boundary test for score=0")]),
]
for task_title, verdict, confidence, summary, findings in review_defs:
    t = task_map.get(task_title)
    qa = agent_map.get("qa-engineer")
    if not t:
        continue
    rr = post(f"/api/v1/tasks/{t['id']}/review-rounds",
              {"reviewer_type": "agent", "reviewer_id": qa["id"] if qa else ""})
    if not rr:
        continue
    post(f"/api/v1/review-rounds/{rr['id']}/start", {})
    for severity, category, message in findings:
        post(f"/api/v1/review-rounds/{rr['id']}/findings",
             {"severity": severity, "category": category, "message": message})
    v = post(f"/api/v1/review-rounds/{rr['id']}/verdict",
             {"verdict": verdict, "confidence": confidence, "summary": summary})
    if v:
        print(f"  ✓ Review: {task_title[:40]} → {verdict} "
              f"({len(findings)} findings)")

# ── Notification channels — config validated per type ──
section("Notification channels")
channel_defs = [
    {"channel_type": "webhook", "name": "Slack Alerts",
     "config": {"url": "https://hooks.slack.com/services/T00/B00/xxx"}},
    {"channel_type": "webhook", "name": "Discord Bot",
     "config": {"url": "https://discord.com/api/webhooks/123/abc"}},
    {"channel_type": "email", "name": "Admin Email",
     "config": {"smtp_host": "smtp.upcp.local", "smtp_port": 587,
                "from_address": "upcp@upcp.local",
                "to_address": "admin@upcp.local"}},
]
for ch in channel_defs:
    c = post("/api/v1/notification-channels", ch)
    if c:
        print(f"  ✓ Channel: {ch['name']} ({ch['channel_type']})")

# ── Git Provider ───────────────────────────────────
section("Git provider")
existing_git = get(f"/api/v1/projects/{PID}/git-providers") or []
if existing_git:
    print(f"  ✓ Git provider already present ({existing_git[0]['id'][:8]})")
else:
    git = post(f"/api/v1/projects/{PID}/git-providers", {
        "name": "GitLab (self-hosted)", "provider_type": "gitlab",
        "url": "http://gitlab.local:8929/dmitry.kovalchuk/upcp",
    })
    if git:
        print(f"  ✓ Git provider: GitLab ({git['id'][:8]})")

# ── Reports ────────────────────────────────────────
section("Reports")
for _i in range(3):
    r = post(f"/api/v1/projects/{PID}/reports/daily", {})
    if r and "id" in r:
        print(f"  ✓ Report: {r['id'][:8]}")

# ── ИИ Лаба features ──────────────────────────────
section("ИИ Лаба depth")
ai_lab = next((p for p in projects.get("items", []) if p["name"] == "ИИ Лаба"), None)
if ai_lab:
    AI_PID = ai_lab["id"]
    feat = post(f"/api/v1/projects/{AI_PID}/features", {
        "name": "Multi-Agent Orchestration",
        "description": "Event-driven dispatch for coordinating multiple AI agents.",
        "status": "in_progress",
    })
    if feat:
        for title, status in [("Design agent message protocol", "done"),
                              ("Implement event bus with Redis pub/sub", "in_progress"),
                              ("Add agent discovery and registration", "backlog")]:
            post(f"/api/v1/features/{feat['id']}/tasks",
                 {"title": title, "status": status})
        print("  ✓ ИИ Лаба: Multi-Agent feature + 3 tasks")

    feat2 = post(f"/api/v1/projects/{AI_PID}/features", {
        "name": "User Dashboard",
        "description": "Personal dashboard showing agent activity, tasks, notifications.",
        "status": "done",
    })
    if feat2:
        for title, status in [("Design dashboard layout", "done"),
                              ("Implement activity feed widget", "done"),
                              ("Add task summary cards", "done")]:
            post(f"/api/v1/features/{feat2['id']}/tasks",
                 {"title": title, "status": status})
        print("  ✓ ИИ Лаба: Dashboard feature + 3 tasks")

# ── Summary ─────────────────────────────────────────
section("Summary")
stats = get("/api/v1/dashboard/stats")
if stats:
    print(f"Projects: {stats.get('project_count')}")
    print(f"Tasks by status: {stats.get('task_counts_by_status')}")
health = get(f"/api/v1/projects/{PID}/health")
if health:
    print(f"UPCP Health Score: {health.get('score')}")
print("✓ Full seed complete!")
