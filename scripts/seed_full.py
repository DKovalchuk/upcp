#!/usr/bin/env python3
"""Comprehensive seed for UPCP — fills ALL views with realistic data.
Run seed_dev.py first to create projects, components, modules, features, tasks."""

import requests
import time
import sys

BASE = "http://127.0.0.1:38080"
DELAY = 0.15  # seconds between requests to avoid rate limiting

def login():
    r = requests.post(f"{BASE}/auth/login", json={"email": "admin@example.com", "password": "admin123"})
    r.raise_for_status()
    return r.json()["access_token"]

TOKEN = login()
H = {"Authorization": f"Bearer {TOKEN}"}
_req_count = 0

def api(method, path, **kw):
    global _req_count
    _req_count += 1
    if _req_count % 5 == 0:
        time.sleep(DELAY)
    fn = getattr(requests, method)
    r = fn(f"{BASE}{path}", headers=H, **kw)
    if r.status_code == 429:
        time.sleep(3)
        r = fn(f"{BASE}{path}", headers=H, **kw)
    if r.status_code >= 400:
        print(f"  WARN {method.upper()} {path} → {r.status_code}: {r.text[:150]}")
        return None
    if r.status_code == 204:
        return {}
    return r.json()

def post(path, data):
    return api("post", path, json=data)

def get(path, **kw):
    return api("get", path, params=kw)

def patch(path, data):
    return api("patch", path, json=data)

# ── Find UPCP project ──────────────────────────────
projects = get("/api/v1/projects", limit=50)
upcp = next((p for p in projects.get("items", []) if p["slug"] == "upcp"), None)
if not upcp:
    print("ERROR: UPCP project not found. Run seed_dev.py first.")
    sys.exit(1)
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

# ── Agent tokens ───────────────────────────────────
for name, agent in agent_map.items():
    tok = post(f"/api/v1/agents/{agent['id']}/tokens", {"name": f"{name}-token"})
    if tok:
        print(f"  ✓ Token: {name}")

# ── Subtasks ───────────────────────────────────────
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
        s = post(f"/api/v1/tasks/{t['id']}/subtasks", {"title": sub_title, "status": sub_status})
        if s:
            print(f"  ✓ Subtask: {sub_title[:40]} [{sub_status}]")

# ── DoD Items ──────────────────────────────────────
dod_defs = {
    "JWT login + refresh token flow": [("Code reviewed", "pass"), ("Tests pass", "pass"), ("Documentation updated", "pass")],
    "Rate limiting (5/min login, 60/min API)": [("Code reviewed", "pass"), ("Tests pass", "pass"), ("Performance benchmarked", "pass")],
    "Project CRUD with slug generation": [("Code reviewed", "pass"), ("Tests pass", "pass"), ("OpenAPI spec updated", "pass")],
    "Evidence upload (file, URL, text)": [("Code reviewed", "pass"), ("Tests pass", "fail"), ("E2E tests added", "fail")],
    "Notification channels (email, webhook)": [("Code reviewed", "pass"), ("Tests pass", "fail"), ("Channel adapter tested", "fail")],
    "Agent playbook system": [("Schema validated", "pass"), ("Loader implemented", "fail"), ("Default playbooks created", "fail")],
}
for task_title, items in dod_defs.items():
    t = task_map.get(task_title)
    if not t:
        continue
    for item_name, status in items:
        d = post(f"/api/v1/tasks/{t['id']}/dod-items", {"name": item_name})
        if d and status == "pass":
            patch(f"/api/v1/dod-items/{d['id']}", {"status": "pass"})
        print(f"  ✓ DoD: {item_name} [{status}]")

# ── Acceptance Criteria ────────────────────────────
ac_defs = {
    "JWT login + refresh token flow": [
        ("User can login with email/password and receive JWT token", True),
        ("Token refresh returns new access_token before expiry", True),
        ("Invalid credentials return 401 with clear error message", True),
    ],
    "RBAC roles and permission checks": [
        ("Admin can create/edit/delete all resources", True),
        ("Viewer can only read, not modify", True),
        ("Role assignments are enforced on every endpoint", True),
    ],
    "Evidence upload (file, URL, text)": [
        ("File upload stores artifact and creates Evidence record", True),
        ("URL evidence fetches and caches content", False),
        ("Evidence can be verified by agent or human", True),
    ],
    "Notification channels (email, webhook)": [
        ("Channel CRUD with config validation", True),
        ("Toggle enables/disables channel delivery", True),
        ("Test endpoint sends probe notification", False),
    ],
}
for task_title, criteria in ac_defs.items():
    t = task_map.get(task_title)
    if not t:
        continue
    for desc, met in criteria:
        ac = post(f"/api/v1/tasks/{t['id']}/acceptance-criteria", {"description": desc})
        if ac:
            print(f"  ✓ AC: {desc[:50]}")

# ── Evidence ───────────────────────────────────────
evidence_defs = [
    ("JWT login + refresh token flow", [
        {"type": "url", "title": "Auth flow test results", "url": "https://ci.example.com/builds/12345",
         "description": "All auth tests pass in CI", "created_by_type": "user"},
        {"type": "text", "title": "Manual verification",
         "content_snippet": "Verified login/logout/refresh cycle with curl and Playwright", "created_by_type": "user"},
    ]),
    ("Evidence upload (file, URL, text)", [
        {"type": "url", "title": "Upload endpoint documentation", "url": "https://docs.upcp.local/api/evidence",
         "description": "API docs for evidence upload", "created_by_type": "user"},
        {"type": "text", "title": "Partial implementation note",
         "content_snippet": "File upload works for text. Binary needs testing. URL fetching returns error on some sites.", "created_by_type": "user"},
    ]),
    ("Rate limiting (5/min login, 60/min API)", [
        {"type": "text", "title": "Rate limit test output",
         "content_snippet": "6th login attempt within 60s returns 429 with retry_after=60. API endpoints limited to 60/min.",
         "created_by_type": "user"},
    ]),
]
for task_title, ev_list in evidence_defs:
    t = task_map.get(task_title)
    if not t:
        continue
    for ev in ev_list:
        e = post(f"/api/v1/tasks/{t['id']}/evidence", ev)
        if e:
            print(f"  ✓ Evidence: {ev['title'][:40]}")

# ── Clarifications ─────────────────────────────────
clarification_defs = [
    ("Notification channels (email, webhook)", "Should webhook support custom headers for auth tokens?",
     "Need to decide if webhook channels should support arbitrary HTTP headers.", True),
    ("Notification channels (email, webhook)", "What is the retry policy for failed deliveries?",
     "Looking for guidance on exponential backoff and max retry count.", False),
    ("Agent playbook system", "Should playbooks support conditional steps?",
     "Agent needs to know if playbooks can have if/else branching.", True),
    ("Heartbeat monitoring (stale detection)", "What is the stale timeout threshold?",
     "Need to confirm: 5 min for stale, 30 min for offline?", False),
]
for task_title, question, context, blocking in clarification_defs:
    t = task_map.get(task_title)
    if not t:
        continue
    c = post(f"/api/v1/tasks/{t['id']}/clarifications", {
        "question": question, "context": context, "blocking": blocking,
    })
    if c:
        print(f"  ✓ Clarification: {question[:50]}")
        if not blocking:
            ans = post(f"/api/v1/clarifications/{c['id']}/answer", {
                "answer": "Per spec: 5 min stale threshold, 30 min offline. Use exponential backoff, max 5 retries."
            })
            if ans:
                print(f"    ✓ Answered")

# ── Task claims + heartbeats ───────────────────────
claims_data = [
    ("Portfolio overview across all projects", "commander"),
    ("Bulk task status updates", "backend-dev"),
    ("Notification channels (email, webhook)", "frontend-dev"),
    ("Agent playbook system", "devops"),
]
for task_title, agent_name in claims_data:
    t = task_map.get(task_title)
    a = agent_map.get(agent_name)
    if not t or not a:
        continue
    claim = post(f"/api/v1/tasks/{t['id']}/claim", {"agent_id": a["id"]})
    if claim:
        print(f"  ✓ Claimed: {task_title[:40]} by {agent_name}")
        hb = post(f"/api/v1/tasks/{t['id']}/heartbeat", {
            "progress_percent": 45, "current_step": "Implementing core logic",
            "next_step": "Write tests", "blockers": [],
        })
        if hb:
            print(f"    ✓ Heartbeat")

# ── Review Rounds ──────────────────────────────────
review_tasks = ["RBAC roles and permission checks", "Project health scoring algorithm"]
for task_title in review_tasks:
    t = task_map.get(task_title)
    if not t:
        continue
    qa = agent_map.get("qa-engineer")
    rr = post(f"/api/v1/tasks/{t['id']}/review-rounds", {
        "reviewer_type": "agent", "reviewer_id": qa["id"] if qa else "",
    })
    if rr:
        print(f"  ✓ Review round: {task_title[:40]}")
        post(f"/api/v1/review-rounds/{rr['id']}/start", {})
        post(f"/api/v1/review-rounds/{rr['id']}/findings", {
            "summary": "Code follows DDD patterns correctly",
            "severity": "info", "file_path": "backend/app/shared/rbac.py", "line": 42,
        })
        post(f"/api/v1/review-rounds/{rr['id']}/findings", {
            "summary": "Missing error handling for invalid role names",
            "severity": "warning", "file_path": "backend/app/shared/rbac.py", "line": 78,
        })

# ── Notification Channels ──────────────────────────
channel_defs = [
    {"channel_type": "webhook", "name": "Slack Alerts",
     "config": {"url": "https://hooks.slack.com/services/T00/B00/xxx", "channel": "#upcp-alerts"}},
    {"channel_type": "webhook", "name": "Discord Bot",
     "config": {"url": "https://discord.com/api/webhooks/123/abc"}},
    {"channel_type": "email", "name": "Admin Email",
     "config": {"to": "admin@upcp.local", "smtp_host": "smtp.upcp.local"}},
]
for ch in channel_defs:
    c = post("/api/v1/notification-channels", ch)
    if c:
        print(f"  ✓ Channel: {ch['name']} ({ch['channel_type']})")

# ── Git Provider ───────────────────────────────────
git = post(f"/api/v1/projects/{PID}/git-providers", {
    "name": "GitLab (self-hosted)", "provider_type": "gitlab",
    "url": "http://gitlab.local:8929/dmitry.kovalchuk/upcp",
})
if git:
    print(f"  ✓ Git provider: GitLab ({git['id'][:8]})")

# ── Reports ────────────────────────────────────────
for i in range(3):
    r = post(f"/api/v1/projects/{PID}/reports/daily", {})
    if r and "id" in r:
        print(f"  ✓ Report: {r['id'][:8]}")

# ── ИИ Лаба features ──────────────────────────────
ai_lab = next((p for p in projects.get("items", []) if p["name"] == "ИИ Лаба"), None)
if ai_lab:
    AI_PID = ai_lab["id"]
    feat = post(f"/api/v1/projects/{AI_PID}/features", {
        "name": "Multi-Agent Orchestration",
        "description": "Event-driven dispatch for coordinating multiple AI agents.",
        "status": "in_progress",
    })
    if feat:
        for title, status in [("Design agent message protocol", "done"), ("Implement event bus with Redis pub/sub", "in_progress"), ("Add agent discovery and registration", "backlog")]:
            post(f"/api/v1/features/{feat['id']}/tasks", {"title": title, "status": status})
        print(f"  ✓ ИИ Лаба: Multi-Agent feature + 3 tasks")

    feat2 = post(f"/api/v1/projects/{AI_PID}/features", {
        "name": "User Dashboard",
        "description": "Personal dashboard showing agent activity, tasks, and notifications.",
        "status": "done",
    })
    if feat2:
        for title, status in [("Design dashboard layout", "done"), ("Implement activity feed widget", "done"), ("Add task summary cards", "done")]:
            post(f"/api/v1/features/{feat2['id']}/tasks", {"title": title, "status": status})
        print(f"  ✓ ИИ Лаба: Dashboard feature + 3 tasks")

# ── Summary ─────────────────────────────────────────
time.sleep(2)
print("\n" + "=" * 60)
stats = get("/api/v1/dashboard/stats")
if stats:
    print(f"Projects: {stats.get('project_count')}")
    print(f"Tasks by status: {stats.get('task_counts_by_status')}")
health = get(f"/api/v1/projects/{PID}/health")
if health:
    print(f"UPCP Health Score: {health.get('score')}")
print("=" * 60)
print("✓ Full seed complete!")
