#!/usr/bin/env python3
"""Seed UPCP with realistic data across all domains."""

import requests
import sys

BASE = "http://127.0.0.1:38080"

# ── Auth ─────────────────────────────────────────────
def login():
    r = requests.post(f"{BASE}/auth/login", json={"email": "admin@example.com", "password": "admin123"})
    r.raise_for_status()
    return r.json()["access_token"]

TOKEN = login()
H = {"Authorization": f"Bearer {TOKEN}"}

def api(method, path, **kw):
    fn = getattr(requests, method)
    r = fn(f"{BASE}{path}", headers=H, **kw)
    if r.status_code >= 400:
        print(f"  WARN {method.upper()} {path} → {r.status_code}: {r.text[:120]}")
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

# ── Clean up placeholder projects ───────────────────
existing = get("/api/v1/projects", limit=50)
placeholder_names = {"Attach Project", "Rev Project", "Evi Project", "Clar Project", "Test Project",
                     "UPCP v2", "Audit Test Project", "Космическая Одиссея", "Я кукарача!", "Demo Project"}
for p in existing.get("items", []):
    if p["name"] in placeholder_names:
        print(f"  Skipping placeholder: {p['name']} (has dependencies)")

# ── Project: UPCP ─────────────────────────────────────
existing_proj = get("/api/v1/projects", limit=50)
upcp_proj = next((p for p in existing_proj.get("items", []) if p["slug"] == "upcp"), None)
if upcp_proj:
    PID = upcp_proj["id"]
    print(f"✓ Project: UPCP (existing, {PID[:8]})")
else:
    proj = post("/api/v1/projects", {
        "name": "UPCP",
        "slug": "upcp",
        "description": "Universal Project Control Plane — AI-first project management platform with DDD architecture, "
                       "agent workflow, SSE notifications, and comprehensive quality gates.",
        "status": "active",
        "settings": {
            "default_branch": "develop",
            "auto_review": True,
            "dod_strict": True,
            "evidence_required": True,
        },
    })
    PID = proj["id"]
    print(f"✓ Project: UPCP ({PID[:8]})")

# ── Project: ИИ Лаба (keep existing if found) ──────
ai_lab = next((p for p in existing_proj.get("items", []) if p["name"] == "ИИ Лаба"), None)
if ai_lab:
    AI_PID = ai_lab["id"]
    print(f"✓ Project: ИИ Лаба (existing, {AI_PID[:8]})")
else:
    ai_lab = post("/api/v1/projects", {
        "name": "ИИ Лаба",
        "slug": "ai-laba",
        "description": "Ecosystem for AI-powered educational and productivity tools.",
        "status": "active",
    })
    AI_PID = ai_lab["id"]
    print(f"✓ Project: ИИ Лаба ({AI_PID[:8]})")

# ── Components ──────────────────────────────────────
components = {}
for name, desc in [
    ("Backend API", "FastAPI-based REST API with DDD bounded contexts"),
    ("Frontend SPA", "React + TanStack Router + shadcn/ui single-page app"),
    ("Infrastructure", "Docker, nginx, PostgreSQL, Redis, observability stack"),
    ("Agent Framework", "AI agent workflow engine with claims, heartbeats, reviews"),
]:
    c = post(f"/api/v1/projects/{PID}/components", {
        "name": name,
        "description": desc,
        "component_type": "service" if name != "Infrastructure" else "infrastructure",
        "status": "active",
    })
    if c:
        components[name] = c["id"]
        print(f"  ✓ Component: {name} ({c['id'][:8]})")

# ── Modules ─────────────────────────────────────────
modules = {}
backend_id = components.get("Backend API")
frontend_id = components.get("Frontend SPA")
infra_id = components.get("Infrastructure")

mod_defs = [
    (backend_id, "Auth Module", "JWT auth, RBAC, rate limiting, session management", "service"),
    (backend_id, "Projects Module", "Project CRUD, settings, portfolio overview", "service"),
    (backend_id, "Delivery Module", "Features, tasks, subtasks, sprint management", "service"),
    (backend_id, "Quality Module", "DoD items, acceptance criteria, evidence, reviews", "service"),
    (backend_id, "Notifications Module", "SSE streams, notification channels, delivery tracking", "service"),
    (backend_id, "Agent Workflow Module", "Claims, heartbeats, playbooks, clarifications", "service"),
    (backend_id, "GitRead Module", "Git provider integration, commit tracking, branch management", "service"),
    (backend_id, "Analytics Module", "Velocity, trends, health history, agent performance", "service"),
    (frontend_id, "Dashboard View", "Stats, attention items, portfolio overview, recent activity", "view"),
    (frontend_id, "Projects View", "Project list, detail, settings, structure browser", "view"),
    (frontend_id, "Task Board View", "Feature/task Kanban, drag-drop, bulk ops", "view"),
    (frontend_id, "Auth Views", "Login, setup, password management", "view"),
    (infra_id, "Docker Stack", "Dockerfiles, compose files, volume management", "service"),
    (infra_id, "Observability Stack", "Prometheus, Grafana, Loki, Tempo, OTel Collector", "service"),
]

for parent_id, name, desc, mtype in mod_defs:
    if not parent_id:
        continue
    m = post(f"/api/v1/components/{parent_id}/modules", {
        "name": name,
        "description": desc,
        "module_type": mtype,
        "status": "active",
    })
    if m:
        modules[name] = m["id"]
        print(f"    ✓ Module: {name} ({m['id'][:8]})")

# ── Features + Tasks ────────────────────────────────
PRIORITY = {"critical": 10, "high": 7, "medium": 5, "low": 3}

feature_defs = [
    {
        "name": "Authentication & Authorization",
        "description": "JWT-based auth with refresh tokens, rate limiting, RBAC, setup flow.",
        "status": "done",
        "tasks": [
            {"title": "JWT login + refresh token flow", "priority": 10, "status": "done"},
            {"title": "Rate limiting (5/min login, 60/min API)", "priority": 7, "status": "done"},
            {"title": "RBAC roles and permission checks", "priority": 7, "status": "done"},
            {"title": "Password change flow", "priority": 5, "status": "done"},
            {"title": "Setup wizard for first admin user", "priority": 5, "status": "done"},
        ],
    },
    {
        "name": "Project Management",
        "description": "Full project lifecycle: create, configure, track health, portfolio overview.",
        "status": "done",
        "tasks": [
            {"title": "Project CRUD with slug generation", "priority": 7, "status": "done"},
            {"title": "Project settings and configuration", "priority": 5, "status": "done"},
            {"title": "Project health scoring algorithm", "priority": 7, "status": "done"},
            {"title": "Portfolio overview across all projects", "priority": 5, "status": "done"},
        ],
    },
    {
        "name": "Delivery Pipeline",
        "description": "Feature → Task → Subtask hierarchy with status workflow.",
        "status": "done",
        "tasks": [
            {"title": "Feature CRUD with type/status/priority", "priority": 10, "status": "done"},
            {"title": "Task CRUD under features", "priority": 10, "status": "done"},
            {"title": "Subtask support", "priority": 7, "status": "done"},
            {"title": "Bulk task status updates", "priority": 5, "status": "done"},
            {"title": "Task status workflow (backlog→in_progress→review→done)", "priority": 7, "status": "done"},
        ],
    },
    {
        "name": "Quality Gates",
        "description": "Definition of Done, acceptance criteria, evidence upload, reviews.",
        "status": "done",
        "tasks": [
            {"title": "DoD items per task with check/uncheck", "priority": 7, "status": "done"},
            {"title": "Acceptance criteria CRUD", "priority": 7, "status": "done"},
            {"title": "Evidence upload (file, URL, text)", "priority": 10, "status": "done"},
            {"title": "Quality stats per project", "priority": 5, "status": "done"},
            {"title": "Submit review workflow", "priority": 7, "status": "done"},
        ],
    },
    {
        "name": "Real-time Notifications (SSE)",
        "description": "Server-Sent Events for live updates, notification channels, delivery tracking.",
        "status": "in_progress",
        "tasks": [
            {"title": "SSE endpoint for notification stream", "priority": 10, "status": "done"},
            {"title": "Fix: SSE Authorization header (EventSource→fetch)", "priority": 10, "status": "done"},
            {"title": "Notification channels (email, webhook)", "priority": 7, "status": "in_progress"},
            {"title": "Notification read/unread tracking", "priority": 5, "status": "done"},
            {"title": "Critical event toast notifications", "priority": 5, "status": "done"},
        ],
    },
    {
        "name": "Agent Workflow Engine",
        "description": "AI agent claims, heartbeats, playbooks, clarifications, reviews.",
        "status": "in_progress",
        "tasks": [
            {"title": "Agent registration and token management", "priority": 7, "status": "done"},
            {"title": "Task claim/release with atomic locking", "priority": 10, "status": "done"},
            {"title": "Heartbeat monitoring (stale detection)", "priority": 7, "status": "done"},
            {"title": "Agent playbook system", "priority": 5, "status": "in_progress"},
            {"title": "Clarification request/response flow", "priority": 5, "status": "done"},
        ],
    },
    {
        "name": "Observability & Testing",
        "description": "Metrics, logging, tracing, test infrastructure, chaos engineering.",
        "status": "in_progress",
        "tasks": [
            {"title": "Prometheus metrics middleware + /metrics", "priority": 7, "status": "done"},
            {"title": "Grafana dashboards (provisioned)", "priority": 5, "status": "done"},
            {"title": "Playwright E2E test suite (21 tests)", "priority": 7, "status": "done"},
            {"title": "SPEC-0024 test environment Phase 2-5", "priority": 5, "status": "backlog"},
        ],
    },
    {
        "name": "Git Integration",
        "description": "Git provider connection, branch/commit tracking, task-to-commit linking.",
        "status": "backlog",
        "tasks": [
            {"title": "Git provider CRUD (GitLab, GitHub)", "priority": 7, "status": "backlog"},
            {"title": "Branch listing and commit history", "priority": 5, "status": "backlog"},
            {"title": "Task-to-commit linking", "priority": 5, "status": "backlog"},
        ],
    },
]

task_ids = []
for fdef in feature_defs:
    tasks = fdef.pop("tasks")
    feat = post(f"/api/v1/projects/{PID}/features", fdef)
    if not feat:
        continue
    fid = feat["id"]
    print(f"  ✓ Feature: {fdef['name']} ({fid[:8]}) [{fdef['status']}]")

    for t in tasks:
        task = post(f"/api/v1/features/{fid}/tasks", t)
        if task:
            task_ids.append(task["id"])
            status_icon = {"done": "✓", "in_progress": "→", "backlog": "…"}.get(t["status"], "?")
            print(f"    {status_icon} Task: {t['title'][:50]} [{t['status']}]")

# ── Quality: Add DoD + Acceptance Criteria to a few tasks ──
done_tasks = [tid for tid in task_ids]
if len(done_tasks) >= 3:
    for tid in done_tasks[:5]:
        # DoD items
        post(f"/api/v1/tasks/{tid}/dod-items", {"title": "Code reviewed", "is_completed": True})
        post(f"/api/v1/tasks/{tid}/dod-items", {"title": "Tests pass", "is_completed": True})
        post(f"/api/v1/tasks/{tid}/dod-items", {"title": "Documentation updated", "is_completed": True})

        # Acceptance criteria
        post(f"/api/v1/tasks/{tid}/acceptance-criteria", {
            "description": "Endpoint returns correct response format",
            "is_met": True,
            "evidence": "API tests pass, OpenAPI spec validated",
        })
        post(f"/api/v1/tasks/{tid}/acceptance-criteria", {
            "description": "Error handling covers edge cases",
            "is_met": True,
            "evidence": "Rate limiting tested, 401/403 flows verified",
        })
    print("  ✓ Quality: DoD items + AC added to 5 tasks")

# ── Agents ──────────────────────────────────────────
agent_defs = [
    {"name": "commander", "display_name": "Commander", "capabilities": ["orchestration", "delegation", "monitoring"]},
    {"name": "backend-dev", "display_name": "Backend Developer", "capabilities": ["python", "fastapi", "sql", "ddd"]},
    {"name": "frontend-dev", "display_name": "Frontend Developer", "capabilities": ["react", "typescript", "ui-ux"]},
    {"name": "qa-engineer", "display_name": "QA Engineer", "capabilities": ["testing", "playwright", "coverage"]},
    {"name": "devops", "display_name": "DevOps Engineer", "capabilities": ["docker", "ci-cd", "observability"]},
]

agent_ids = []
for adef in agent_defs:
    agent = post("/api/v1/agents", adef)
    if agent:
        agent_ids.append(agent["id"])
        print(f"  ✓ Agent: {adef['display_name']} ({agent['id'][:8]})")

# ── Agent claims + heartbeats on in-progress tasks ──
in_progress_tasks = [tid for tid in task_ids]  # claim first 3 tasks
for i, tid in enumerate(in_progress_tasks[:3]):
    agent_id = agent_ids[i % len(agent_ids)]
    claim = post(f"/api/v1/tasks/{tid}/claim", {"agent_id": agent_id})
    if claim:
        post(f"/api/v1/tasks/{tid}/heartbeat", {"agent_id": agent_id, "status": "working"})
        print(f"  → Claimed: task {tid[:8]} by agent {agent_id[:8]}")

# ── Reports ─────────────────────────────────────────
report = post(f"/api/v1/projects/{PID}/reports/daily", {})
if report and "id" in report:
    print(f"  ✓ Report: daily ({report['id'][:8]})")

# ── Search test ─────────────────────────────────────
search_result = get("/api/v1/search", q="authentication", project_id=PID, limit=5)
if search_result:
    hits = search_result if isinstance(search_result, list) else search_result.get("items", [])
    print(f"  ✓ Search: 'authentication' → {len(hits)} results")

# ── Summary ─────────────────────────────────────────
print("\n" + "=" * 60)
stats = get("/api/v1/dashboard/stats")
if stats:
    print(f"Projects: {stats.get('project_count')}")
    print(f"Tasks by status: {stats.get('task_counts_by_status')}")

health = get(f"/api/v1/projects/{PID}/health")
if health:
    print(f"UPCP Health Score: {health.get('score', 'N/A')}")

print("=" * 60)
print("✓ Seed complete!")
