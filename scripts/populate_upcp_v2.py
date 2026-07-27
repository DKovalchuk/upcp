#!/usr/bin/env python3
"""Populate UPCP with v2 planning entities via REST API."""

import json
import sys
import urllib.request
import urllib.error
from typing import Any

BASE = "http://127.0.0.1:38080/api/v1"

# Track created entities for cross-referencing
created: dict[str, dict[str, str]] = {
    "projects": {},
    "components": {},
    "modules": {},
    "features": {},
    "tasks": {},
}

def api(method: str, path: str, data: dict | None = None) -> dict:
    """Make API request."""
    url = f"{BASE}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()
        print(f"  ERROR {e.code} {method} {path}: {err_body[:200]}")
        return {"error": e.code, "body": err_body}

def create_project(name: str, slug: str, description: str) -> str:
    """Create project and return ID."""
    print(f"Creating project: {name}")
    r = api("POST", "/projects", {
        "name": name, "slug": slug, "description": description, "status": "active"
    })
    pid = r.get("id", "")
    created["projects"][slug] = pid
    print(f"  -> {pid}")
    return pid

def create_component(project_id: str, name: str, slug: str, description: str) -> str:
    """Create component and return ID."""
    print(f"  Creating component: {name}")
    r = api("POST", f"/projects/{project_id}/components", {
        "name": name, "slug": slug, "description": description, "status": "active"
    })
    cid = r.get("id", "")
    created["components"][slug] = cid
    print(f"    -> {cid}")
    return cid

def create_module(component_id: str, name: str, slug: str, description: str) -> str:
    """Create module and return ID."""
    print(f"    Creating module: {name}")
    r = api("POST", f"/components/{component_id}/modules", {
        "name": name, "slug": slug, "description": description, "status": "active"
    })
    mid = r.get("id", "")
    created["modules"][slug] = mid
    print(f"      -> {mid}")
    return mid

def create_feature(project_id: str, name: str, slug: str, description: str,
                   component_id: str | None = None) -> str:
    """Create feature and return ID."""
    print(f"      Creating feature: {name}")
    data: dict[str, Any] = {
        "name": name, "slug": slug, "description": description, "status": "backlog"
    }
    if component_id:
        data["component_id"] = component_id
    r = api("POST", f"/projects/{project_id}/features", data)
    fid = r.get("id", "")
    created["features"][slug] = fid
    print(f"        -> {fid}")
    return fid

def create_task(feature_id: str, title: str, description: str,
                priority: int = 0, component_id: str | None = None,
                module_id: str | None = None) -> str:
    """Create task and return ID."""
    print(f"        Creating task: {title[:60]}...")
    data: dict[str, Any] = {
        "title": title,
        "description": description,
        "status": "backlog",
        "priority": priority,
    }
    if component_id:
        data["component_id"] = component_id
    if module_id:
        data["module_id"] = module_id
    r = api("POST", f"/features/{feature_id}/tasks", data)
    tid = r.get("id", "")
    print(f"          -> {tid[:8]}...")
    return tid

def create_subtask(task_id: str, title: str, description: str = "") -> str:
    """Create subtask."""
    r = api("POST", f"/tasks/{task_id}/subtasks", {
        "title": title, "description": description, "status": "todo"
    })
    return r.get("id", "")

def create_ac(task_id: str, description: str) -> str:
    """Create acceptance criterion."""
    r = api("POST", f"/tasks/{task_id}/acceptance-criteria", {
        "description": description
    })
    return r.get("id", "")

def create_dod(task_id: str, description: str) -> str:
    """Create DoD item."""
    r = api("POST", f"/tasks/{task_id}/dod-items", {
        "description": description
    })
    return r.get("id", "")

# ============================================================
# Metadata block template
# ============================================================

def meta(milestone: str, component: str, module: str, feature: str,
         priority_label: str, size: str, actor: str,
         deps: str = "", evidence: str = "test_output, manual_verification") -> str:
    return f"""

## Metadata
- Milestone: {milestone}
- Component: {component}
- Module: {module}
- Feature: {feature}
- Priority: {priority_label}
- Size: {size}
- Actor: {actor}
- Dependencies: {deps}
- Required evidence: {evidence}
"""

# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 60)
    print("UPCP v2 Population Script")
    print("=" * 60)

    # ── 1. Create UPCP project ──────────────────────────────
    pid = create_project(
        "UPCP v2",
        "upcp-v2",
        "Universal Project Control Plane v2 — Identity, Agent Workflow, "
        "Evidence, Observability and Human Control UX. Self-tracking project "
        "for all v2 development milestones M7–M11."
    )

    # ── 2. Create components ────────────────────────────────
    components_def = [
        ("identity-access", "identity-access",
         "User identity, authentication, organizations, RBAC, sessions. "
         "Foundation for all access control in UPCP."),
        ("agent-management", "agent-management",
         "Agent profiles, tokens, scopes, roles, project assignments. "
         "Agents as first-class subjects with bounded permissions."),
        ("agent-workflow", "agent-workflow",
         "Task claims, heartbeats, progress, clarifications, agent inbox, "
         "playbook, stale detection. Full agent task lifecycle."),
        ("delivery-management", "delivery-management",
         "Projects, structure (components/modules), features, tasks, subtasks, "
         "task lifecycle, dependencies. Core delivery hierarchy."),
        ("quality-evidence", "quality-evidence",
         "Acceptance criteria, DoD, evidence model, quality gates, review rounds, "
         "review findings, review policies. Evidence-based Done."),
        ("runtime-platform", "runtime-platform",
         "Redis integration, rate limiting, idempotency, locks, background jobs, "
         "health checks. Runtime infrastructure."),
        ("observability", "observability",
         "Structured logging, metrics, tracing, correlation IDs, redaction, "
         "Grafana dashboards. Full observability stack."),
        ("secrets-config", "secrets-config",
         "Secret provider abstraction, encrypted fields, feature flags, "
         "settings, startup validation. Secure configuration."),
        ("mcp-api-cli", "mcp-api-cli",
         "MCP tools, REST API, CLI commands, agent guide, error codes, "
         "context packs. All external interfaces."),
        ("frontend-ui", "frontend-ui",
         "App shell, auth UI, project drill-down, agent center, attention "
         "dashboard, task detail, evidence/review UI, notifications, settings."),
        ("reporting-insights", "reporting-insights",
         "Daily/weekly reports, project health, agent activity, attention queue, "
         "LLM summary. Insights and reporting."),
        ("git-integration", "git-integration",
         "Read-only Git adapters (local/GitHub/GitLab), git links, git UI, "
         "CI status (future). Read-only by design."),
        ("notifications", "notifications",
         "In-app notifications, notification preferences, event dispatch, "
         "webhooks (future). Real-time awareness."),
    ]

    for name, slug, desc in components_def:
        create_component(pid, name, slug, desc)

    # ── 3. Create modules ───────────────────────────────────
    modules_def = [
        # identity-access modules
        ("identity-access", [
            ("organizations", "Organizations", "Multi-org entity. Default org for standalone."),
            ("users", "Users", "User accounts with email/password."),
            ("memberships", "Memberships", "User-to-org membership with roles."),
            ("authentication", "Authentication", "Login, logout, refresh, password change."),
            ("sessions", "Sessions", "Session management and revocation."),
            ("rbac", "RBAC", "Roles, permissions, bindings at global/org/project scope."),
        ]),
        # agent-management modules
        ("agent-management", [
            ("agent-profiles", "Agent Profiles", "Agent identity and metadata."),
            ("agent-tokens", "Agent Tokens", "Token creation, hashing, revocation."),
            ("agent-scopes", "Agent Scopes", "Permission scopes for agents."),
            ("agent-roles", "Agent Roles", "Agent-specific RBAC roles."),
            ("agent-project-assignments", "Agent Project Assignments", "Project allowlist for agents."),
            ("agent-audit", "Agent Audit", "Audit trail for all agent actions."),
        ]),
        # agent-workflow modules
        ("agent-workflow", [
            ("task-claims", "Task Claims", "Claim/release/expire task lifecycle."),
            ("heartbeats", "Heartbeats", "Agent heartbeat with progress tracking."),
            ("progress-updates", "Progress Updates", "Progress percent, current/next step."),
            ("clarifications", "Clarifications", "Question/answer blocking flow."),
            ("agent-inbox", "Agent Inbox", "Machine-readable event inbox."),
            ("agent-playbook", "Agent Playbook", "Built-in guide for agents."),
            ("stale-detection", "Stale Detection", "Detect and expire stale claims."),
        ]),
        # delivery-management modules
        ("delivery-management", [
            ("projects", "Projects", "Project CRUD and lifecycle."),
            ("structure", "Structure", "Component and module hierarchy."),
            ("features", "Features", "Feature management and grouping."),
            ("tasks", "Tasks", "Task CRUD with full metadata."),
            ("subtasks", "Subtasks", "Task decomposition."),
            ("task-lifecycle", "Task Lifecycle", "Status machine and transitions."),
            ("dependencies", "Dependencies", "Task dependency tracking."),
        ]),
        # quality-evidence modules
        ("quality-evidence", [
            ("acceptance-criteria", "Acceptance Criteria", "AC management per task."),
            ("dod", "DoD", "Definition of Done items."),
            ("evidence", "Evidence", "Evidence model with verification states."),
            ("quality-gates", "Quality Gates", "Automated quality checks."),
            ("review-rounds", "Review Rounds", "Review round lifecycle."),
            ("review-findings", "Review Findings", "Findings with severity/categories."),
            ("review-policies", "Review Policies", "Review policy enforcement."),
        ]),
        # runtime-platform modules
        ("runtime-platform", [
            ("redis", "Redis", "Redis client, health, reconnection."),
            ("rate-limiting", "Rate Limiting", "Sliding window rate limiter."),
            ("idempotency", "Idempotency", "Idempotency key management."),
            ("locks", "Locks", "Distributed locks for claims."),
            ("background-jobs", "Background Jobs", "Job queue and scheduling."),
            ("health-checks", "Health Checks", "Service health endpoints."),
        ]),
        # observability modules
        ("observability", [
            ("structured-logging", "Structured Logging", "JSON structured logs."),
            ("metrics", "Metrics", "Prometheus metrics collection."),
            ("tracing", "Tracing", "OpenTelemetry distributed tracing."),
            ("correlation", "Correlation", "Request/trace ID propagation."),
            ("redaction", "Redaction", "Secret and PII redaction."),
            ("dashboards", "Dashboards", "Grafana dashboard definitions."),
        ]),
        # secrets-config modules
        ("secrets-config", [
            ("secret-providers", "Secret Providers", "Abstraction for env/file/vault secrets."),
            ("encrypted-fields", "Encrypted Fields", "Encrypted storage for integration secrets."),
            ("feature-flags", "Feature Flags", "Runtime feature toggles."),
            ("settings", "Settings", "Org/project/app settings management."),
            ("startup-validation", "Startup Validation", "Config validation on boot."),
        ]),
        # mcp-api-cli modules
        ("mcp-api-cli", [
            ("mcp-tools", "MCP Tools", "MCP tool definitions and handlers."),
            ("rest-api", "REST API", "REST endpoint definitions."),
            ("cli", "CLI", "Typer CLI commands."),
            ("agent-guide", "Agent Guide", "Built-in agent playbook resource."),
            ("error-codes", "Error Codes", "Machine-readable error catalog."),
            ("context-packs", "Context Packs", "Versioned, tiered context generation."),
        ]),
        # frontend-ui modules
        ("frontend-ui", [
            ("app-shell", "App Shell", "Layout, sidebar, topbar, routing."),
            ("auth-ui", "Auth UI", "Login, setup, user menu pages."),
            ("project-drilldown", "Project Drill-down", "Full project navigation."),
            ("agent-center", "Agent Center", "Agent list, detail, management."),
            ("attention-dashboard", "Attention Dashboard", "Attention-first home dashboard."),
            ("task-detail", "Task Detail", "Enhanced task detail with all tabs."),
            ("evidence-ui", "Evidence UI", "Evidence panel and management."),
            ("review-ui", "Review UI", "Review panel and verdicts."),
            ("notifications-ui", "Notifications UI", "Notification center and prefs."),
            ("reports-ui", "Reports UI", "Reports page enhancement."),
            ("settings-ui", "Settings UI", "Project/org settings pages."),
        ]),
        # reporting-insights modules
        ("reporting-insights", [
            ("daily-reports", "Daily Reports", "Automated daily project reports."),
            ("weekly-reports", "Weekly Reports", "Weekly summary reports."),
            ("project-health", "Project Health", "Health score calculation."),
            ("agent-activity", "Agent Activity", "Agent productivity metrics."),
            ("attention-queue", "Attention Queue", "Items needing human attention."),
            ("llm-summary", "LLM Summary", "Optional LLM-powered summaries."),
        ]),
        # git-integration modules
        ("git-integration", [
            ("read-only-adapters", "Read-Only Adapters", "Local/GitHub/GitLab read adapters."),
            ("git-links", "Git Links", "Links between git objects and tasks."),
            ("git-ui", "Git UI", "Git views in frontend."),
            ("ci-status-future", "CI Status (Future)", "Future CI status reading."),
        ]),
        # notifications modules
        ("notifications", [
            ("in-app-notifications", "In-App Notifications", "Notification model and center."),
            ("notification-preferences", "Notification Preferences", "Per-user/project preferences."),
            ("event-dispatch", "Event Dispatch", "Event-to-notification routing."),
            ("webhooks-future", "Webhooks (Future)", "Future webhook notifications."),
        ]),
    ]

    for comp_slug, mods in modules_def:
        comp_id = created["components"].get(comp_slug)
        if not comp_id:
            print(f"  WARNING: component '{comp_slug}' not found")
            continue
        for mod_name, mod_slug, mod_desc in mods:
            create_module(comp_id, mod_name, mod_slug, mod_desc)

    # ── 4. Create features ──────────────────────────────────
    # We create high-level features grouped by milestone

    # M7: Identity, Access & Agent Foundation
    f_m7_auth = create_feature(pid,
        "First-run owner and auth setup",
        "first-run-auth-setup",
        "First-run setup flow: create owner account, default organization. "
        "Email/password login, logout, refresh token rotation. "
        "Public registration disabled by default.",
        created["components"]["identity-access"])

    f_m7_rbac = create_feature(pid,
        "RBAC roles and permissions",
        "rbac-roles-permissions",
        "Role-based access control with global/org/project scopes. "
        "Owner, Admin, Member, Viewer roles for humans. "
        "Seeded permissions and role bindings.",
        created["components"]["identity-access"])

    f_m7_agents = create_feature(pid,
        "Agent profiles and tokens",
        "agent-profiles-tokens",
        "Agent as first-class subject. Agent profiles with metadata. "
        "Agent tokens: create (show once), hash storage, revoke, track last used. "
        "Agent scopes and project allowlist.",
        created["components"]["agent-management"])

    f_m7_agent_roles = create_feature(pid,
        "Agent RBAC roles",
        "agent-rbac-roles",
        "Agent Reader, Agent Contributor, Agent Builder, Agent Reviewer roles. "
        "Default: Agent Builder with restrictions. "
        "Agents cannot delete, manage users, manage other agents' tokens.",
        created["components"]["agent-management"])

    # M8: Runtime Foundation
    f_m8_redis = create_feature(pid,
        "Redis integration",
        "redis-integration",
        "Redis as required runtime dependency. Client with health check, "
        "graceful reconnect. Key/TTL naming conventions. "
        "Used for: rate limiting, idempotency, locks, heartbeats, session cache.",
        created["components"]["runtime-platform"])

    f_m8_rate_limiting = create_feature(pid,
        "Rate limiting middleware",
        "rate-limiting-middleware",
        "Sliding window rate limiter via Redis. Limit by IP, user, agent, token, route class. "
        "Rate limit headers. Machine-readable errors. Audit abuse events.",
        created["components"]["runtime-platform"])

    f_m8_secrets = create_feature(pid,
        "Secret provider abstraction",
        "secret-provider-abstraction",
        "SecretProvider interface with Env, File, Docker providers. "
        "Encrypted integration secrets. Never return secrets via API. "
        "Never log secrets. Redaction layer.",
        created["components"]["secrets-config"])

    f_m8_logging = create_feature(pid,
        "Structured logging and metrics",
        "structured-logging-metrics",
        "Structured JSON logs with required fields. Secret redaction. "
        "Prometheus metrics endpoint. HTTP/DB/Redis/business metrics.",
        created["components"]["observability"])

    f_m8_tracing = create_feature(pid,
        "OpenTelemetry tracing",
        "opentelemetry-tracing",
        "Distributed tracing for HTTP, DB, Redis, MCP, LLM, Git, reports. "
        "Correlation IDs. Grafana dashboards. Loki/Tempo integration.",
        created["components"]["observability"])

    f_m8_security = create_feature(pid,
        "Security hardening",
        "security-hardening",
        "CORS configuration, security headers, sort whitelist, "
        "Git adapter command injection prevention. "
        "SQL injection prevention. Input validation.",
        created["components"]["runtime-platform"])

    # M9: Agent Workflow MVP
    f_m9_claims = create_feature(pid,
        "Task claim lifecycle",
        "task-claim-lifecycle",
        "Agent claims task → works → releases/completes. Claim states: "
        "active, released, expired, completed. Expiration. Lock via Redis.",
        created["components"]["agent-workflow"])

    f_m9_heartbeats = create_feature(pid,
        "Agent heartbeats and progress",
        "agent-heartbeats-progress",
        "Heartbeat with progress_percent, current_step, next_step, blockers, eta. "
        "Stale claim detection (7min timeout). Progress UI.",
        created["components"]["agent-workflow"])

    f_m9_clarifications = create_feature(pid,
        "Clarification flow",
        "clarification-flow",
        "Agent requests clarification (blocking/non-blocking). "
        "Human answers. States: open, answered, resolved, cancelled.",
        created["components"]["agent-workflow"])

    f_m9_inbox = create_feature(pid,
        "Agent inbox and playbook",
        "agent-inbox-playbook",
        "Machine-readable inbox (GET /agent/inbox). Events: task_assigned, "
        "task_updated, clarification_answered, review_requested, etc. "
        "Agent playbook as MCP resource and REST endpoint.",
        created["components"]["agent-workflow"])

    f_m9_lifecycle = create_feature(pid,
        "Extended task lifecycle",
        "extended-task-lifecycle",
        "New statuses: backlog, ready, claimed, in_progress, blocked, "
        "needs_clarification, ready_for_review, changes_requested, done, cancelled. "
        "Review state: none, pending_review, approved, rejected.",
        created["components"]["delivery-management"])

    f_m9_mcp = create_feature(pid,
        "MCP workflow tools",
        "mcp-workflow-tools",
        "New MCP tools: claim_task, release_task, heartbeat_task, "
        "request_clarification, answer_clarification, submit_for_review, "
        "get_agent_inbox, get_agent_playbook.",
        created["components"]["mcp-api-cli"])

    # M10: Evidence & Review Engine
    f_m10_evidence = create_feature(pid,
        "Evidence model",
        "evidence-model",
        "Evidence entity with types: commit, test_output, manual_verification, "
        "screenshot, doc_update, note, review_note. Verification states: "
        "unverified, agent_verified, human_accepted, rejected, stale.",
        created["components"]["quality-evidence"])

    f_m10_quality_gates = create_feature(pid,
        "Quality gates and DoD coverage",
        "quality-gates-dod-coverage",
        "DoD items can require specific evidence types. "
        "Quality gate checks: required evidence attached, no blocking clarifications, "
        "review policy satisfied. Auto-recalculate on changes.",
        created["components"]["quality-evidence"])

    f_m10_review = create_feature(pid,
        "Review rounds and findings",
        "review-rounds-findings",
        "ReviewRound lifecycle: pending → in_progress → completed/cancelled. "
        "Verdicts: approve, reject, needs_changes. ReviewFindings with "
        "severity (info/warning/critical) and categories.",
        created["components"]["quality-evidence"])

    f_m10_agent_review = create_feature(pid,
        "Agent-assisted review",
        "agent-assisted-review",
        "Agent reviewer reads task, DoD, evidence, git links. "
        "Creates findings, submits verdict. "
        "Executor != reviewer by default. "
        "Human has final authority. Agent auto-close only if explicitly allowed.",
        created["components"]["quality-evidence"])

    # M11: Human Control UX
    f_m11_attention = create_feature(pid,
        "Attention dashboard",
        "attention-dashboard",
        "Attention-first home: needs review, open questions, blocked tasks, "
        "stale claims, failed gates, rejected tasks. "
        "Each item drills down to entity detail.",
        created["components"]["frontend-ui"])

    f_m11_drilldown = create_feature(pid,
        "Full project drill-down",
        "full-project-drill-down",
        "Portfolio → Project → Component → Module → Feature → Task → "
        "Subtask/AC/DoD/Evidence/Review/Audit/Git. "
        "Breadcrumbs, deep links, URL-synced tabs/filters.",
        created["components"]["frontend-ui"])

    f_m11_task_detail = create_feature(pid,
        "Enhanced task detail",
        "enhanced-task-detail",
        "Task detail with tabs: Details, Execution, Clarifications, Evidence, "
        "DoD, Subtasks, Reviews, Git, Audit. "
        "Execution tab shows claim, heartbeat, progress, stale warning.",
        created["components"]["frontend-ui"])

    f_m11_agent_center = create_feature(pid,
        "Agent center",
        "agent-center",
        "Agent list page with status, role, active tasks, last activity. "
        "Agent detail: profile, tokens, scopes, claims, actions, clarifications, "
        "evidence, reviews, audit.",
        created["components"]["frontend-ui"])

    f_m11_notifications_feat = create_feature(pid,
        "Notifications system",
        "notifications-system",
        "In-app notification center. Unread count, mark as read. "
        "Filter by project/type. Preferences. Types: task_submitted_for_review, "
        "agent_review_completed, clarification_requested, claim_stale, etc.",
        created["components"]["notifications"])

    f_m11_reports = create_feature(pid,
        "Enhanced reports",
        "enhanced-reports",
        "Daily/weekly reports. Project health score. Agent activity summary. "
        "Attention queue. Evidence completeness. Review turnaround.",
        created["components"]["reporting-insights"])

    # ── 5. Create tasks ─────────────────────────────────────
    # We'll create the most important tasks for each feature

    # === M7 Tasks ===

    # Auth setup
    t = create_task(f_m7_auth,
        "Add User model and migration",
        "Create SQLAlchemy User model with fields: id, email, password_hash, "
        "display_name, is_active, is_superuser, created_at, updated_at. "
        "Add Alembic migration." + meta("M7", "identity-access", "users", "First-run owner and auth setup", "Critical", "M", "agent"),
        priority=10)

    t = create_task(f_m7_auth,
        "Add Organization model and migration",
        "Create Organization model: id, name, slug, description, is_default, "
        "created_at, updated_at. Default org auto-created on first run." + meta("M7", "identity-access", "organizations", "First-run owner and auth setup", "Critical", "M", "agent"),
        priority=10)

    t = create_task(f_m7_auth,
        "Add Membership model and migration",
        "Membership links User to Organization with role. Fields: id, user_id, "
        "org_id, role, created_at. Unique constraint on (user_id, org_id)." + meta("M7", "identity-access", "memberships", "First-run owner and auth setup", "Critical", "M", "agent"),
        priority=10)

    t = create_task(f_m7_auth,
        "Implement JWT token service",
        "JWT access token (15min) + rotating refresh token (7d). "
        "RS256 or HS256. Token creation, validation, refresh, revocation. "
        "Store refresh tokens in DB." + meta("M7", "identity-access", "authentication", "First-run owner and auth setup", "Critical", "L", "agent"),
        priority=10)

    t = create_task(f_m7_auth,
        "Implement auth middleware",
        "FastAPI dependency that extracts and validates JWT from Authorization header. "
        "Injects current user/org into request state. "
        "Returns 401 for invalid/missing tokens." + meta("M7", "identity-access", "authentication", "First-run owner and auth setup", "Critical", "M", "agent"),
        priority=10)

    t = create_task(f_m7_auth,
        "Create POST /auth/setup endpoint",
        "First-run setup: creates owner user + default organization. "
        "Only works when no users exist. Returns tokens. "
        "Disabled after first user is created." + meta("M7", "identity-access", "authentication", "First-run owner and auth setup", "Critical", "M", "agent"),
        priority=10)

    t = create_task(f_m7_auth,
        "Create POST /auth/login endpoint",
        "Email/password login. Returns access + refresh tokens. "
        "Audit failed login attempts. Rate limit by IP." + meta("M7", "identity-access", "authentication", "First-run owner and auth setup", "Critical", "M", "agent"),
        priority=10)

    t = create_task(f_m7_auth,
        "Add auth to all existing endpoints",
        "Apply auth middleware to all existing API endpoints. "
        "Public: /health, /auth/setup, /auth/login. "
        "All others require valid JWT." + meta("M7", "identity-access", "authentication", "First-run owner and auth setup", "Critical", "L", "agent", deps="JWT service, auth middleware"),
        priority=10)

    # RBAC
    t = create_task(f_m7_rbac,
        "Add Role and Permission models",
        "Role: id, name, scope (global/org/project). "
        "Permission: id, action, resource. "
        "RolePermission: role_id, permission_id. "
        "Seed default roles: Owner, Admin, Member, Viewer." + meta("M7", "identity-access", "rbac", "RBAC roles and permissions", "Critical", "M", "agent"),
        priority=9)

    t = create_task(f_m7_rbac,
        "Add RoleBinding model",
        "RoleBinding: user_id, role_id, org_id (nullable), project_id (nullable). "
        "Scoped bindings. Check permissions via service layer." + meta("M7", "identity-access", "rbac", "RBAC roles and permissions", "Critical", "M", "agent", deps="Role/Permission models"),
        priority=9)

    t = create_task(f_m7_rbac,
        "Implement permission check service",
        "PermissionService: check(user, action, resource, scope, context). "
        "FastAPI dependency for endpoint protection. "
        "Returns 403 with machine-readable error." + meta("M7", "identity-access", "rbac", "RBAC roles and permissions", "Critical", "M", "agent", deps="RoleBinding model"),
        priority=9)

    # Agent management
    t = create_task(f_m7_agents,
        "Add Agent model and migration",
        "Agent: id, name, description, is_active, created_by, "
        "created_at, updated_at. Linked to org." + meta("M7", "agent-management", "agent-profiles", "Agent profiles and tokens", "High", "M", "agent"),
        priority=9)

    t = create_task(f_m7_agents,
        "Add AgentToken model and migration",
        "AgentToken: id, agent_id, token_hash, name, scopes, "
        "expires_at, revoked_at, last_used_at, created_at. "
        "Token shown only once on creation." + meta("M7", "agent-management", "agent-tokens", "Agent profiles and tokens", "High", "M", "agent", deps="Agent model"),
        priority=9)

    t = create_task(f_m7_agents,
        "Create POST /agents endpoint",
        "Create agent profile. Requires admin permission. "
        "Returns agent with id." + meta("M7", "agent-management", "agent-profiles", "Agent profiles and tokens", "High", "S", "agent", deps="Agent model"),
        priority=9)

    t = create_task(f_m7_agents,
        "Create POST /agents/{id}/tokens endpoint",
        "Create agent token. Returns plaintext token once. "
        "Stores hashed version. Track creation audit." + meta("M7", "agent-management", "agent-tokens", "Agent profiles and tokens", "High", "M", "agent", deps="AgentToken model"),
        priority=9)

    t = create_task(f_m7_agents,
        "Implement agent token authentication",
        "Auth middleware variant for agents. "
        "X-Agent-Token header or Bearer token. "
        "Validate hash, check revoked, update last_used." + meta("M7", "agent-management", "agent-tokens", "Agent profiles and tokens", "High", "M", "agent", deps="AgentToken model"),
        priority=9)

    t = create_task(f_m7_agents,
        "Add Agent RBAC roles",
        "Agent roles: Agent Reader, Agent Contributor, Agent Builder, Agent Reviewer. "
        "Default: Agent Builder with restrictions (no delete projects, "
        "no manage users, no manage other agents' tokens)." + meta("M7", "agent-management", "agent-roles", "Agent RBAC roles", "High", "M", "agent", deps="RBAC, Agent model"),
        priority=8)

    # === M8 Tasks ===

    t = create_task(f_m8_redis,
        "Add Redis to docker-compose and backend",
        "Add Redis service to docker-compose. Add redis[hiredis] to requirements. "
        "Create Redis client singleton with health check, reconnect. "
        "Add /health/ready endpoint checking Redis." + meta("M8", "runtime-platform", "redis", "Redis integration", "High", "M", "agent"),
        priority=9)

    t = create_task(f_m8_rate_limiting,
        "Implement sliding window rate limiter",
        "Redis-based sliding window. Configurable per route class: "
        "anonymous (100/min), authenticated (1000/min), agent (500/min), "
        "login (5/min), MCP (200/min). "
        "Headers: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset." + meta("M8", "runtime-platform", "rate-limiting", "Rate limiting middleware", "High", "L", "agent", deps="Redis"),
        priority=9)

    t = create_task(f_m8_secrets,
        "Implement SecretProvider abstraction",
        "Abstract base with get_secret(name) → str. "
        "EnvSecretProvider (default), FileSecretProvider, DockerSecretProvider. "
        "Replace all hardcoded secrets. Startup validation." + meta("M8", "secrets-config", "secret-providers", "Secret provider abstraction", "Critical", "M", "agent"),
        priority=10)

    t = create_task(f_m8_secrets,
        "Add encrypted field support",
        "EncryptedType for SQLAlchemy. Uses ENCRYPTION_KEY from secret provider. "
        "Applied to: integration secrets, API keys stored in DB. "
        "Never return via API (masked in responses)." + meta("M8", "secrets-config", "encrypted-fields", "Secret provider abstraction", "High", "M", "agent", deps="SecretProvider"),
        priority=8)

    t = create_task(f_m8_logging,
        "Implement structured JSON logging",
        "JSON formatter with required fields: timestamp, level, logger, message, "
        "request_id, trace_id, org_id, user_id, agent_id. "
        "Redaction filter for secrets/PII." + meta("M8", "observability", "structured-logging", "Structured logging and metrics", "High", "M", "agent"),
        priority=8)

    t = create_task(f_m8_logging,
        "Add Prometheus metrics endpoint",
        "GET /metrics in Prometheus format. "
        "HTTP: requests_total, duration, active, errors. "
        "DB: pool, query_duration. "
        "Redis: command_duration, errors. "
        "Business: projects, tasks, claims, evidence counts." + meta("M8", "observability", "metrics", "Structured logging and metrics", "High", "L", "agent", deps="Redis"),
        priority=8)

    t = create_task(f_m8_tracing,
        "Add OpenTelemetry tracing",
        "OTel SDK setup. Trace HTTP requests, DB queries, Redis commands, "
        "MCP tool calls. Correlation IDs in all logs and responses. "
        "Export to OTLP collector." + meta("M8", "observability", "tracing", "OpenTelemetry tracing", "Medium", "L", "agent", deps="Structured logging"),
        priority=7)

    t = create_task(f_m8_security,
        "Configure CORS properly",
        "Replace wildcard CORS with explicit allowed origins from config. "
        "Support frontend URL and MCP client URLs." + meta("M8", "runtime-platform", "health-checks", "Security hardening", "High", "S", "agent"),
        priority=9)

    t = create_task(f_m8_security,
        "Add sort_by whitelist for all list endpoints",
        "Prevent SQL injection via sort parameters. "
        "Explicit whitelist per entity: created_at, updated_at, name, priority, status." + meta("M8", "runtime-platform", "health-checks", "Security hardening", "High", "S", "agent"),
        priority=9)

    t = create_task(f_m8_security,
        "Harden Git adapter against command injection",
        "Sanitize all inputs to subprocess calls in Git adapters. "
        "Use shlex.quote, validate branch/commit patterns, "
        "block shell metacharacters." + meta("M8", "runtime-platform", "health-checks", "Security hardening", "Critical", "M", "agent"),
        priority=10)

    # === M9 Tasks ===

    t = create_task(f_m9_claims,
        "Add TaskClaim model and migration",
        "TaskClaim: id, task_id, agent_id, claimed_at, released_at, state, "
        "context_snapshot_id, last_heartbeat_at, expires_at. "
        "States: active, released, expired, completed." + meta("M9", "agent-workflow", "task-claims", "Task claim lifecycle", "High", "M", "agent", deps="M7 agents, M7 RBAC"),
        priority=9)

    t = create_task(f_m9_claims,
        "Implement claim/release API endpoints",
        "POST /tasks/{id}/claim — agent claims task (lock via Redis). "
        "POST /tasks/{id}/release — agent releases claim. "
        "POST /tasks/{id}/heartbeat — update heartbeat. "
        "Machine-readable errors for all edge cases." + meta("M9", "agent-workflow", "task-claims", "Task claim lifecycle", "High", "L", "agent", deps="TaskClaim model, Redis locks"),
        priority=9)

    t = create_task(f_m9_heartbeats,
        "Implement heartbeat processing",
        "Accept heartbeat payload: task_id, progress_percent, current_step, "
        "next_step, blockers, eta. Store in claim. "
        "Detect stale claims (>7min no heartbeat). Auto-expire." + meta("M9", "agent-workflow", "heartbeats", "Agent heartbeats and progress", "High", "M", "agent", deps="TaskClaim model"),
        priority=8)

    t = create_task(f_m9_clarifications,
        "Add ClarificationRequest model and migration",
        "ClarificationRequest: id, task_id, author_type, author_id, question, "
        "context, blocking, state, answer, answered_by, answered_at, created_at. "
        "States: open, answered, resolved, cancelled." + meta("M9", "agent-workflow", "clarifications", "Clarification flow", "High", "M", "agent"),
        priority=8)

    t = create_task(f_m9_clarifications,
        "Implement clarification API endpoints",
        "POST /tasks/{id}/clarifications — create request. "
        "POST /clarifications/{id}/answer — answer. "
        "POST /clarifications/{id}/resolve — resolve. "
        "Block task if blocking clarification is unresolved." + meta("M9", "agent-workflow", "clarifications", "Clarification flow", "High", "M", "agent", deps="ClarificationRequest model"),
        priority=8)

    t = create_task(f_m9_inbox,
        "Implement agent inbox endpoint",
        "GET /agent/inbox?since=<timestamp> — returns events for current agent. "
        "Events: task_assigned, task_updated, clarification_answered, "
        "review_requested, review_verdict, task_reopened, comment_added." + meta("M9", "agent-workflow", "agent-inbox", "Agent inbox and playbook", "High", "M", "agent", deps="M7 agents"),
        priority=8)

    t = create_task(f_m9_inbox,
        "Create agent playbook resource",
        "MCP resource: upcp://agent/playbook. "
        "REST: GET /agent/playbook. "
        "CLI: upcp agent guide. "
        "Explains: auth, context, claim, progress, clarification, evidence, review." + meta("M9", "agent-workflow", "agent-playbook", "Agent inbox and playbook", "Medium", "M", "agent"),
        priority=7)

    t = create_task(f_m9_lifecycle,
        "Extend task status machine",
        "Add statuses: ready, claimed, blocked, needs_clarification, "
        "ready_for_review, changes_requested, cancelled. "
        "Add review_state field: none, pending_review, approved, rejected. "
        "Update all transitions and guards." + meta("M9", "delivery-management", "task-lifecycle", "Extended task lifecycle", "High", "L", "agent", deps="M7 auth"),
        priority=9)

    t = create_task(f_m9_mcp,
        "Add MCP workflow tools",
        "New tools: claim_task, release_task, heartbeat_task, "
        "request_clarification, answer_clarification, submit_task_for_review, "
        "get_agent_inbox, get_agent_playbook. "
        "All with machine-readable errors and idempotency." + meta("M9", "mcp-api-cli", "mcp-tools", "MCP workflow tools", "High", "L", "agent", deps="All M9 API endpoints"),
        priority=8)

    # === M10 Tasks ===

    t = create_task(f_m10_evidence,
        "Add Evidence model and migration",
        "Evidence: id, task_id, dod_item_id (nullable), type, title, description, "
        "url, content_snippet, artifact_ref, created_by_type/id, "
        "verification_state, verified_by_type/id, verified_at, created_at. "
        "Types: commit, test_output, manual_verification, screenshot, "
        "doc_update, note, review_note." + meta("M10", "quality-evidence", "evidence", "Evidence model", "High", "M", "agent", deps="M7 auth"),
        priority=8)

    t = create_task(f_m10_evidence,
        "Implement evidence CRUD API",
        "GET /tasks/{id}/evidence — list. "
        "POST /tasks/{id}/evidence — attach. "
        "GET /evidence/{id} — detail. "
        "POST /evidence/{id}/agent-verify, human-accept, reject." + meta("M10", "quality-evidence", "evidence", "Evidence model", "High", "M", "agent", deps="Evidence model"),
        priority=8)

    t = create_task(f_m10_quality_gates,
        "Implement quality gate calculation",
        "Quality gate checks: required DoD items done, required evidence attached, "
        "no unresolved blocking clarifications, review policy satisfied. "
        "Auto-recalculate on any relevant change. "
        "Expose via quality stats endpoint." + meta("M10", "quality-evidence", "quality-gates", "Quality gates and DoD coverage", "High", "L", "agent", deps="Evidence model, DoD model"),
        priority=8)

    t = create_task(f_m10_review,
        "Add ReviewRound model and migration",
        "ReviewRound: id, task_id, requested_by_type/id, reviewer_type/id, "
        "state, verdict, confidence, summary, policy_snapshot, "
        "created_at, completed_at. "
        "States: pending, in_progress, completed, cancelled. "
        "Verdicts: approve, reject, needs_changes." + meta("M10", "quality-evidence", "review-rounds", "Review rounds and findings", "High", "M", "agent"),
        priority=8)

    t = create_task(f_m10_review,
        "Add ReviewFinding model and migration",
        "ReviewFinding: id, review_round_id, severity, category, message, "
        "evidence_id (nullable), dod_item_id (nullable), suggestion. "
        "Severity: info, warning, critical." + meta("M10", "quality-evidence", "review-findings", "Review rounds and findings", "High", "S", "agent", deps="ReviewRound model"),
        priority=8)

    t = create_task(f_m10_review,
        "Implement review API endpoints",
        "POST /tasks/{id}/submit-review. "
        "POST /tasks/{id}/approve, reject. "
        "POST /tasks/{id}/request-agent-review. "
        "GET /tasks/{id}/review-rounds. "
        "POST /review-rounds/{id}/start, findings, verdict." + meta("M10", "quality-evidence", "review-rounds", "Review rounds and findings", "High", "L", "agent", deps="ReviewRound, ReviewFinding"),
        priority=8)

    t = create_task(f_m10_agent_review,
        "Implement agent review capability",
        "Agent reviewer reads task, DoD, evidence, git links. "
        "Creates findings. Submits verdict. "
        "Cannot be executor of same task (unless self_review allowed). "
        "Cannot close task if policy requires human approval." + meta("M10", "quality-evidence", "review-policies", "Agent-assisted review", "High", "L", "agent", deps="Review API, Agent RBAC"),
        priority=7)

    t = create_task(f_m10_agent_review,
        "Add review policy enforcement",
        "Review policies at project level: human_only, "
        "agent_review_then_human (default), agent_auto_close_if_allowed. "
        "Auto-close conditions: policy allows, all DoD met, all evidence attached, "
        "no blocking clarifications, executor != reviewer." + meta("M10", "quality-evidence", "review-policies", "Agent-assisted review", "High", "M", "agent", deps="Review API"),
        priority=7)

    # === M11 Tasks ===

    t = create_task(f_m11_attention,
        "Build attention dashboard",
        "Attention-first home page. Sections: needs review, open questions, "
        "blocked tasks, stale claims, failed gates, rejected tasks. "
        "Each item has drill-down link. Auto-refresh." + meta("M11", "frontend-ui", "attention-dashboard", "Attention dashboard", "Medium", "L", "frontend", deps="M9 agent workflow, M10 review"),
        priority=7)

    t = create_task(f_m11_drilldown,
        "Implement full project drill-down",
        "Portfolio → Project → Component → Module → Feature → Task. "
        "Breadcrumbs on every page. Deep links with URL state. "
        "URL-synced tabs and filters." + meta("M11", "frontend-ui", "project-drill-down", "Full project drill-down", "Medium", "L", "frontend"),
        priority=7)

    t = create_task(f_m11_task_detail,
        "Enhance task detail with all tabs",
        "Add tabs: Execution (claim/heartbeat/progress), Clarifications, "
        "Evidence (panel), Reviews (panel), Git links, Audit timeline. "
        "Keep existing: Details, AC, DoD, Subtasks." + meta("M11", "frontend-ui", "task-detail", "Enhanced task detail", "Medium", "L", "frontend", deps="M9, M10"),
        priority=7)

    t = create_task(f_m11_agent_center,
        "Build agent center page",
        "Agent list: name, status, role, active tasks, last activity, token status. "
        "Agent detail: profile, tokens, scopes, project assignments, "
        "current claims, recent actions, clarifications, evidence, reviews, audit." + meta("M11", "frontend-ui", "agent-center", "Agent center", "Medium", "L", "frontend", deps="M7 agents"),
        priority=7)

    t = create_task(f_m11_notifications_feat,
        "Implement notification model and API",
        "Notification: id, user_id, type, title, message, entity_type, "
        "entity_id, is_read, created_at. "
        "GET /notifications — list with filters. "
        "POST /notifications/{id}/read — mark read. "
        "POST /notifications/read-all — bulk mark read." + meta("M11", "notifications", "in-app-notifications", "Notifications system", "Medium", "M", "backend"),
        priority=7)

    t = create_task(f_m11_notifications_feat,
        "Build notification center UI",
        "Bell icon in topbar with unread count badge. "
        "Dropdown with notification list, filters, mark as read. "
        "Notification preferences page." + meta("M11", "notifications", "in-app-notifications", "Notifications system", "Medium", "M", "frontend", deps="Notification API"),
        priority=7)

    t = create_task(f_m11_reports,
        "Enhance reporting with health scores",
        "Project health score: 0-100 based on: task completion rate, "
        "blocked ratio, evidence completeness, review turnaround, "
        "stale claims, open clarifications. "
        "Agent activity summary. Attention queue." + meta("M11", "reporting-insights", "project-health", "Enhanced reports", "Medium", "L", "backend"),
        priority=6)

    print("\n" + "=" * 60)
    print("Population complete!")
    print(f"Projects: {len(created['projects'])}")
    print(f"Components: {len(created['components'])}")
    print(f"Modules: {len(created['modules'])}")
    print(f"Features: {len(created['features'])}")
    print("=" * 60)

if __name__ == "__main__":
    main()
