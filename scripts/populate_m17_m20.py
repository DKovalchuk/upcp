#!/usr/bin/env python3
"""Populate UPCP project with M17-M20 features, tasks, components, and modules.

Uses MCP for feature/task CRUD and direct DB for component/module creation.
Stage environment: API on port 3080, DB on port 35433.
"""

import json
import uuid
import urllib.request

PROJECT_ID = "d9313eae-7e0b-4060-85ca-2e5591faefd2"
MCP_URL = "http://localhost:3080/mcp/"
DB_DSN = "postgresql://upcp:upcp_local_change_me@127.0.0.1:35433/upcp"


def mcp_call(tool_name: str, arguments: dict) -> dict:
    """Call MCP tool and return parsed result."""
    payload = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
    }).encode()
    req = urllib.request.Request(MCP_URL, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    text = data["result"]["content"][0]["text"]
    return json.loads(text)


def create_feature(name: str, slug: str, description: str, status: str = "backlog") -> str:
    """Create feature via MCP, return feature ID."""
    result = mcp_call("feature_create", {
        "project_id": PROJECT_ID,
        "name": name,
        "slug": slug,
        "description": description,
        "status": status,
    })
    fid = result["id"]
    print(f"  Feature: {name} -> {fid[:8]}")
    return fid


def create_task(feature_id: str, title: str, description: str, priority: int = 1, status: str = "backlog") -> str:
    """Create task via MCP, return task ID."""
    result = mcp_call("task_create", {
        "feature_id": feature_id,
        "title": title,
        "description": description,
        "status": status,
        "priority": priority,
    })
    tid = result["id"]
    print(f"    Task: {title[:60]}... -> {tid[:8]}")
    return tid


# ── Components & Modules (direct DB) ──

def create_component_and_modules(conn, component_name: str, modules: list[str]) -> str:
    """Create component and its modules directly in DB."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    cur = conn.cursor()
    comp_id = str(uuid.uuid4())
    cur.execute(
        "INSERT INTO component (id, project_id, name, slug, description, status, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, 'active', %s, %s)",
        (comp_id, PROJECT_ID, component_name, component_name.lower().replace(" & ", "-").replace(" ", "-"), f"Component: {component_name}", now, now),
    )
    for mod_name in modules:
        mod_id = str(uuid.uuid4())
        mod_slug = mod_name.lower().replace(" & ", "-").replace(" ", "-")
        cur.execute(
            "INSERT INTO module (id, component_id, name, slug, description, status, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, 'active', %s, %s)",
            (mod_id, comp_id, mod_name, mod_slug, f"Module: {mod_name}", now, now),
        )
    conn.commit()
    print(f"  Component: {component_name} ({len(modules)} modules)")
    return comp_id


# ══════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════

def main():
    import psycopg

    conn = psycopg.connect(DB_DSN)

    # ── 1. Create new components for M17-M20 ──
    print("\n═══ NEW COMPONENTS & MODULES ═══")
    new_components = {
        "Security Hardening": [
            "MCP Auth Middleware",
            "LLM Provider Cleanup",
            "CSP Hardening",
            "Agent Ownership Checks",
            "Env Flag Guards",
        ],
        "Database Hardening": [
            "Migration 0020 Indexes",
            "ForeignKey ondelete",
            "N+1 Query Fixes",
        ],
        "Architecture Cleanup": [
            "Notification Error Logging",
            "Dead Code Removal",
            "FastAPI Lifespan",
            "Agent Inbox Realization",
        ],
        "Accessibility": [
            "Keyboard DnD",
            "ARIA Attributes",
            "Breadcrumb Resolution",
        ],
        "Settings Redesign": [
            "Settings Tabs Layout",
            "User Profile Tab",
            "Notification Preferences Tab",
            "Channel Config Tab",
        ],
        "Notification UX": [
            "Notifications Page",
            "Click-to-Navigate",
            "Notification Filtering",
        ],
        "Test Infrastructure": [
            "Conftest Unification",
            "Pytest Markers",
            "Frontend Coverage",
        ],
        "Event Bus": [
            "In-Process Pub/Sub",
            "Event Subscribers",
        ],
        "Real-Time Notifications": [
            "SSE Endpoint",
            "Frontend EventSource",
        ],
        "File Uploads": [
            "Upload Endpoint",
            "Storage Adapter",
            "Upload UI",
        ],
        "Bulk Operations": [
            "Bulk Status Change",
            "Bulk Assign",
            "Bulk UI",
        ],
        "Task Comments": [
            "Comment Model",
            "Comment API",
            "Comment UI",
        ],
    }
    for comp_name, modules in new_components.items():
        create_component_and_modules(conn, comp_name, modules)

    # ── 2. Create M17 features & tasks ──
    print("\n═══ M17: SECURITY & STABILITY (0.19.0) ═══")

    # M17 S1: Critical Bug Fixes
    f17s1 = create_feature(
        "Critical Bug Fixes",
        "m17-critical-bug-fixes",
        "M17 S19.1: Fix 5 critical/high bugs from M16 audit. Query string construction, Project Settings route, TopBar no-ops, Settings version, Dashboard empty state.",
    )

    create_task(f17s1,
        "Fix fetchProjectTasks query string construction bug",
        """BUG-001 | Severity: Critical | File: frontend/src/lib/api/tasks.ts

PROBLEM: The `sep` logic is broken when both query filters and pagination are present. `paginationParams()` returns strings prefixed with `?` but `sep` is set to `&` when both `qs` and `pag` are non-empty. Resulting URL is malformed: `/tasks&status=foo?offset=0&limit=20`.

ACCEPTANCE CRITERIA:
- [ ] URL correctly formed with pagination only: /tasks?offset=0&limit=20
- [ ] URL correctly formed with filters only: /tasks?status=backlog
- [ ] URL correctly formed with both: /tasks?status=backlog&offset=0&limit=20
- [ ] URL correctly formed with no params: /tasks

DoD: All 4 URL patterns tested, existing tests pass.""",
        priority=0)

    create_task(f17s1,
        "Fix Project Settings route — add to TAB_ROUTES",
        """BUG-002 | Severity: High | File: frontend/src/components/project/ProjectDetail.tsx

PROBLEM: Sidebar links to /projects/$projectId/settings but TAB_ROUTES map does NOT include 'settings'. User sees Overview tab instead.

ACCEPTANCE CRITERIA:
- [ ] 'settings' added to TAB_ROUTES map
- [ ] Settings tab trigger added to TabsList
- [ ] Settings tab content shows project edit form
- [ ] Other tabs still work correctly
- [ ] URL updates when switching to Settings tab

DoD: Settings tab renders project edit form, all tabs functional.""",
        priority=1)

    create_task(f17s1,
        "Fix TopBar Profile/Settings no-op handlers",
        """BUG-003 | Severity: High | File: frontend/src/components/layouts/TopBar.tsx:91-92

PROBLEM: DropdownMenu items "Profile" and "Settings" have onClick={() => {}} — clickable items that do nothing.

ACCEPTANCE CRITERIA:
- [ ] Profile click navigates to /settings
- [ ] Settings click navigates to /settings
- [ ] Dropdown closes after navigation

DoD: Both menu items navigate to /settings.""",
        priority=1)

    create_task(f17s1,
        "Fix hardcoded APP_VERSION in SettingsPage",
        """BUG-004 | Severity: Medium | File: frontend/src/components/SettingsPage.tsx:8

PROBLEM: const APP_VERSION = '0.14.0' is hardcoded. Current version is 0.17.0.

ACCEPTANCE CRITERIA:
- [ ] APP_VERSION read from import.meta.env.VITE_APP_VERSION
- [ ] vite.config.ts defines VITE_APP_VERSION from package.json
- [ ] Fallback to 'unknown' if env var not set

DoD: Version displays correctly, auto-updates with package.json.""",
        priority=2)

    create_task(f17s1,
        "Fix Dashboard 'New Project' empty state no-op button",
        """BUG-005 | Severity: Low | File: frontend/src/components/Dashboard.tsx:102

PROBLEM: Empty state action={{ label: 'New Project', onClick: () => {} }} — button does nothing.

ACCEPTANCE CRITERIA:
- [ ] Clicking "New Project" navigates to /projects
- [ ] (Optional) Create dialog opens automatically via search param

DoD: Button navigates to projects page.""",
        priority=2)

    # M17 S2: Security Hardening
    f17s2 = create_feature(
        "Security Hardening",
        "m17-security-hardening",
        "M17 S19.2: Fix 5 security vulnerabilities. MCP auth bypass, LLM stubs, CSP unsafe-eval, agent ownership, env guard.",
    )

    create_task(f17s2,
        "Add authentication to MCP endpoints",
        """SEC-001 | Severity: High | File: backend/app/identity/middleware.py:52

PROBLEM: MCP endpoints at /mcp/ are explicitly skipped by auth middleware. Anyone can call MCP tools including task CRUD, claims, evidence — no authentication required.

ACCEPTANCE CRITERIA:
- [ ] MCP /mcp/ path added to auth middleware protection
- [ ] MCP endpoints return 401 without valid token
- [ ] MCP endpoints work with valid JWT Bearer token
- [ ] MCP endpoints work with valid X-Agent-Token header
- [ ] All existing MCP tests updated with auth headers

DoD: MCP requires auth, 3 new tests verify rejection/approval.""",
        priority=0)

    create_task(f17s2,
        "Remove or implement LLM provider stubs",
        """SEC-002 | Severity: High | File: backend/app/llm/gateway.py:22-43

PROBLEM: All 3 LLM providers return fake summaries ("Summary generated by..."). /reports/{id}/summarize silently produces fabricated results.

ACCEPTANCE CRITERIA:
- [ ] Stub implementations removed
- [ ] NullProvider raises NotImplementedError with config guidance
- [ ] /reports/{id}/summarize returns 501 when LLM not configured
- [ ] No fake summaries ever returned
- [ ] Existing tests updated to expect 501

DoD: 501 returned without config, no placeholder text in responses.""",
        priority=0)

    create_task(f17s2,
        "Harden CSP — remove unsafe-eval",
        """SEC-003 | Severity: Medium | File: backend/app/main.py:122

PROBLEM: CSP header allows 'unsafe-inline' and 'unsafe-eval' for scripts. unsafe-eval allows arbitrary code execution.

ACCEPTANCE CRITERIA:
- [ ] 'unsafe-eval' removed from script-src
- [ ] Frontend loads correctly (no CSP violations)
- [ ] Test verifies CSP header does not contain unsafe-eval

DoD: CSP hardened, frontend functional, test passes.""",
        priority=1)

    create_task(f17s2,
        "Add ownership checks to agent endpoints",
        """SEC-004 | Severity: Low | File: backend/app/identity/agent_endpoints.py

PROBLEM: Agent endpoints require auth but no ownership check. Any authenticated user can view any agent's data.

ACCEPTANCE CRITERIA:
- [ ] Agent owner can access all agent endpoints
- [ ] Admin/superuser can access all agent endpoints
- [ ] Other users get 403 Forbidden
- [ ] Non-existent agent returns 404

DoD: Ownership enforced, 3 new tests verify access control.""",
        priority=2)

    create_task(f17s2,
        "Replace env='test' guard with explicit disable flags",
        """SEC-005 | Severity: Medium | File: backend/app/main.py:95,99, backend/app/shared/config.py

PROBLEM: Rate limiting and auth middleware skipped when env="test". If UPCP_ENV accidentally set to "test" in production, all protections disabled.

ACCEPTANCE CRITERIA:
- [ ] UPCP_DISABLE_RATE_LIMIT flag added to Settings
- [ ] UPCP_DISABLE_AUTH flag added to Settings
- [ ] env="test" no longer disables protections
- [ ] Default: both protections enabled
- [ ] Test conftest sets disable flags explicitly

DoD: Protections default-on, explicit flags needed to disable.""",
        priority=1)

    # M17 S3: Database Hardening
    f17s3 = create_feature(
        "Database Hardening",
        "m17-database-hardening",
        "M17 S19.3: Migration 0020 with 17+ indexes, 27 ForeignKey ondelete fixes, N+1 query resolution.",
    )

    create_task(f17s3,
        "Create migration 0020: indexes on FK columns + status columns",
        """DB-001 | Severity: Medium | File: backend/alembic/versions/0020_add_indexes_ondelete.py

PROBLEM: 17+ frequently queried FK columns have no indexes, causing full table scans.

INDEXES TO ADD:
- task.feature_id, task.status
- feature.project_id
- component.project_id, module.component_id
- project.status
- report.project_id
- task_claim.agent_id
- audit_event: entity_id, event_type, entity_type, timestamp
- gitread: provider.project_id, branch.provider_id, commit.provider_id, pr.provider_id
- git_link: (entity_type, entity_id)

ACCEPTANCE CRITERIA:
- [ ] Migration 0020 creates all 17 indexes
- [ ] Migration is reversible (downgrade drops indexes)
- [ ] No duplicate index errors on re-run
- [ ] Migration runs cleanly on existing data

DoD: All indexes created, migration clean.""",
        priority=0)

    create_task(f17s3,
        "Fix ForeignKey ondelete behavior for 27 columns",
        """DB-002 | Severity: Medium | Files: delivery/models.py, structure/models.py, quality/models.py, reporting/models.py, gitread/models.py

PROBLEM: 27 ForeignKey columns have no ondelete clause. PostgreSQL defaults to RESTRICT — prevents parent deletion.

RULES:
- Child tables (owns lifecycle): CASCADE — subtask.task_id, clarification.task_id, etc.
- Required references: CASCADE — task.feature_id, feature.project_id, etc.
- Optional references: SET NULL — task.component_id, task.module_id, evidence.dod_item_id

ACCEPTANCE CRITERIA:
- [ ] All 27 ForeignKeys have explicit ondelete
- [ ] Child tables use CASCADE
- [ ] Optional refs use SET NULL
- [ ] Migration 0020 includes ondelete changes
- [ ] Deleting a project cascades correctly

DoD: All FKs have ondelete, cascade behavior verified.""",
        priority=0)

    create_task(f17s3,
        "Fix N+1 query in agent detail endpoint",
        """DB-003 | Severity: Medium | File: backend/app/identity/agent_endpoints.py:157

PROBLEM: Agent claims endpoint loops through claims and does db.get(Task, c.task_id) for each — N+1 query pattern.

FIX: Use single IN clause to batch-fetch tasks.

ACCEPTANCE CRITERIA:
- [ ] Agent claims endpoint uses batch query
- [ ] Query count <= 3 for agent claims (claims + tasks + heartbeats)
- [ ] Response format unchanged

DoD: N+1 eliminated, query count verified in test.""",
        priority=1)

    # M17 S4: Architecture Cleanup
    f17s4 = create_feature(
        "Architecture Cleanup",
        "m17-architecture-cleanup",
        "M17 S19.4: Notification error logging, dead auth/ removal, agent inbox fix, FastAPI lifespan, notification target resolution.",
    )

    create_task(f17s4,
        "Add logging to 7 notification trigger exception handlers",
        """ARCH-001 | Severity: High | Files: delivery/service.py, delivery/workflow.py, delivery/stale_reaper.py, quality/service.py

PROBLEM: 7 trigger call sites use `except Exception: pass` — errors completely invisible.

FIX: Add `logger.warning("Notification trigger failed for %s", event_type, exc_info=True)` to all 7 sites.

ACCEPTANCE CRITERIA:
- [ ] All 7 trigger sites log warnings on failure
- [ ] No bare `except Exception: pass` remains
- [ ] Notification failure still does not block main operation
- [ ] Log includes event type and exception info

DoD: All 7 sites log, no silent failures, main operations unaffected.""",
        priority=0)

    create_task(f17s4,
        "Delete dead auth/ module",
        """ARCH-002 | Severity: Medium | Directory: backend/app/auth/

PROBLEM: auth/ directory contains legacy models (rbac_user, rbac_role, rbac_permission) from earlier iteration. Active auth is in identity/.

ACCEPTANCE CRITERIA:
- [ ] backend/app/auth/ directory deleted
- [ ] No imports from app.auth remain
- [ ] All tests pass

DoD: Dead code removed, no import errors.""",
        priority=2)

    create_task(f17s4,
        "Fix agent inbox stub to return real events",
        """ARCH-003 | Severity: Medium | File: backend/app/api/v1/agent_self.py:69

PROBLEM: agent_inbox() always returns {"events": []} despite having AgentInboxEvent model.

FIX: Query AgentInboxEvent table, support unread_only filter, return last 50 events.

ACCEPTANCE CRITERIA:
- [ ] Agent inbox returns real events from AgentInboxEvent
- [ ] Supports unread_only filter
- [ ] Returns last 50 events ordered by created_at desc
- [ ] Existing tests pass

DoD: Real events returned, filter works, 2 new tests pass.""",
        priority=1)

    create_task(f17s4,
        "Migrate deprecated @app.on_event to FastAPI lifespan",
        """ARCH-004 | Severity: Medium | File: backend/app/main.py:108

PROBLEM: @app.on_event("startup") is deprecated.

FIX: Use @asynccontextmanager async def lifespan(app) with yield.

ACCEPTANCE CRITERIA:
- [ ] No @app.on_event decorators remain
- [ ] Reaper starts on app startup
- [ ] Reaper stops on app shutdown
- [ ] No deprecation warnings

DoD: Lifespan context manager works, no deprecation warnings.""",
        priority=2)

    create_task(f17s4,
        "Fix notification default target resolution",
        """ARCH-005 | Severity: Low | File: backend/app/reporting/trigger.py:99

PROBLEM: Notifications default to user_id="system" which is invisible to users.

FIX: Resolve target from entity context (e.g., task assignee) before falling back to "system".

ACCEPTANCE CRITERIA:
- [ ] Task notifications go to task assignee when available
- [ ] Fallback to "system" only when no user determined
- [ ] Existing tests pass

DoD: Notifications reach correct user, fallback only when needed.""",
        priority=2)

    # ── 3. Create M18 features & tasks ──
    print("\n═══ M18: UX POLISH, A11Y & SETTINGS (0.20.0) ═══")

    f18s1 = create_feature(
        "Accessibility Fixes",
        "m18-accessibility-fixes",
        "M18 S20.1: BoardView keyboard DnD, ARIA on accordions, breadcrumb UUID resolution, task card focus.",
    )
    create_task(f18s1,
        "Add KeyboardSensor to BoardView for accessible DnD",
        """A11Y-001 | Severity: High | File: frontend/src/components/project/BoardView.tsx

PROBLEM: BoardView only has PointerSensor — keyboard DnD completely inaccessible.

ACCEPTANCE CRITERIA:
- [ ] KeyboardSensor added from @dnd-kit/core
- [ ] Tasks can be moved between columns via keyboard (Tab + Enter/Space)
- [ ] Screen reader announces drag state
- [ ] Keyboard navigation: Tab to card, Enter to pick up, Arrow keys to move, Enter to drop

DoD: Full keyboard DnD flow works, screen reader compatible.""",
        priority=0)

    create_task(f18s1,
        "Add ARIA attributes to expandable sections",
        """A11Y-002 | Severity: High | Files: DeliveryPage.tsx, StructurePage.tsx

PROBLEM: FeatureSection and ComponentCard use onClick on div elements for expand/collapse but lack aria-expanded, role="button", keyboard handlers.

ACCEPTANCE CRITERIA:
- [ ] aria-expanded attribute on all expand/collapse triggers
- [ ] role="button" on clickable divs
- [ ] onKeyDown handler for Enter and Space keys
- [ ] Screen reader announces expanded/collapsed state

DoD: All interactive elements keyboard accessible, ARIA correct.""",
        priority=0)

    create_task(f18s1,
        "Resolve UUIDs in breadcrumbs",
        """A11Y-003 | Severity: Medium | File: frontend/src/components/layouts/BreadcrumbBar.tsx

PROBLEM: BreadcrumbBar silently drops UUID segments — shows "Home > Projects" instead of "Home > Projects > My Project > Structure".

ACCEPTANCE CRITERIA:
- [ ] Project ID resolved to project name via useProject hook
- [ ] Breadcrumb shows resolved name
- [ ] Fallback to truncated UUID if project not found

DoD: Breadcrumbs show human-readable names.""",
        priority=1)

    create_task(f18s1,
        "Make BoardView task cards keyboard-focusable",
        """A11Y-004 | Severity: Medium | File: frontend/src/components/project/BoardView.tsx

PROBLEM: DraggableTaskCard lacks tabIndex and keyboard handlers for click-to-open.

ACCEPTANCE CRITERIA:
- [ ] tabIndex={0} on task cards
- [ ] onKeyDown Enter opens TaskDetailSheet
- [ ] Focus-visible outline on task cards

DoD: Task cards focusable, Enter opens detail, visual focus indicator.""",
        priority=1)

    f18s2 = create_feature(
        "Settings Redesign",
        "m18-settings-redesign",
        "M18 S20.2: Tabbed settings page with Profile, Notifications, Channels, Appearance, About tabs.",
    )
    create_task(f18s2,
        "Create tabbed Settings layout with 5 tabs",
        """SETTINGS-001 | Severity: Medium | File: frontend/src/components/SettingsPage.tsx

CURRENT: Single page with 3 cards (theme, API info, version).

TARGET: Tabbed layout:
- Profile: user name, email, password change
- Notifications: per-event-type toggle, channel selection
- Channels: email/webhook CRUD, test connection
- Appearance: theme toggle (existing)
- About: version, API info, health status (existing)

ACCEPTANCE CRITERIA:
- [ ] Settings page uses Tabs component (same as ProjectDetail)
- [ ] 5 tabs rendered: Profile, Notifications, Channels, Appearance, About
- [ ] Existing theme/API/version content moved to appropriate tabs
- [ ] URL sync with search params (?tab=profile)

DoD: 5 tabs functional, existing content preserved, URL synced.""",
        priority=0)

    create_task(f18s2,
        "Implement User Profile tab",
        """SETTINGS-002 | Severity: Medium | New file: frontend/src/components/settings/ProfileTab.tsx

ACCEPTANCE CRITERIA:
- [ ] Shows current user name and email (read-only for now)
- [ ] "Change Password" button opens dialog
- [ ] Password change form with current/new/confirm fields
- [ ] Success/error toast on save

DoD: Profile displays user info, password change works.""",
        priority=1)

    create_task(f18s2,
        "Implement Notification Preferences tab",
        """SETTINGS-003 | Severity: Medium | New file: frontend/src/components/settings/NotificationPreferencesTab.tsx

ACCEPTANCE CRITERIA:
- [ ] Per-event-type toggle switches (review, clarification, claim, quality, agent)
- [ ] Digest frequency selector (Instant, Hourly, Daily)
- [ ] Quiet hours time range (start/end)
- [ ] Save button persists preferences (localStorage for now)
- [ ] Load saved preferences on mount

DoD: Preferences saved/loaded, UI reflects state.""",
        priority=1)

    f18s3 = create_feature(
        "Notification UX Improvements",
        "m18-notification-ux",
        "M18 S20.3: Full /notifications page, click-to-navigate, error handling, filtering.",
    )
    create_task(f18s3,
        "Create /notifications page with filters and grouping",
        """NOTIF-001 | Severity: Medium | New files: frontend/src/pages/NotificationsPage.tsx, frontend/src/components/notifications/NotificationList.tsx

ACCEPTANCE CRITERIA:
- [ ] /notifications route added to router
- [ ] Page shows all notifications grouped by day (Today, Yesterday, Older)
- [ ] Filter bar: All/Unread/Read, Type filter, Project filter
- [ ] Mark All Read button
- [ ] Pagination (50 per page)
- [ ] Empty state when no notifications

DoD: Full page with filters, grouping, pagination.""",
        priority=0)

    create_task(f18s3,
        "Add click-to-navigate on notification items",
        """NOTIF-002 | Severity: Medium | File: frontend/src/components/notifications/NotificationBell.tsx

PROBLEM: Clicking notification only marks as read — does not navigate to entity.

ACCEPTANCE CRITERIA:
- [ ] Click marks notification as read
- [ ] Click navigates to entity (task → TaskDetailSheet, project → ProjectDetail)
- [ ] entity_type and entity_id used for navigation
- [ ] Fallback to /notifications if entity not found

DoD: Click navigates to correct entity.""",
        priority=0)

    create_task(f18s3,
        "Add error handling to notification mark-read",
        """NOTIF-003 | Severity: Low | File: frontend/src/components/notifications/NotificationBell.tsx:55

PROBLEM: markNotificationRead(id).then(onRead) — no .catch(), failures silent.

ACCEPTANCE CRITERIA:
- [ ] .catch() with showToast.error() added
- [ ] Optimistic update rolled back on error

DoD: Errors shown to user, UI consistent.""",
        priority=2)

    f18s4 = create_feature(
        "Project Dashboard Enhancement",
        "m18-project-dashboard",
        "M18 S20.4: Health score card, task completion donut, velocity sparkline, recent activity for project.",
    )
    create_task(f18s4,
        "Enhance Project Overview tab with health + charts",
        """DASH-001 | Severity: Medium | File: frontend/src/components/project/ProjectDetail.tsx (TabsContent value="overview")

CURRENT: Shows only basic metadata (name, slug, status, dates).

TARGET:
- Health score card with trend indicator (up/down/stable)
- Task completion donut chart (done/in-progress/backlog)
- Velocity sparkline (tasks completed per week, last 8 weeks)
- Recent activity feed (last 10 audit events for this project)

ACCEPTANCE CRITERIA:
- [ ] Health score fetched from /projects/{id}/health
- [ ] Health displayed with color-coded badge
- [ ] Task status distribution shown as donut or bar
- [ ] Velocity shown as sparkline or mini bar chart
- [ ] Recent activity fetched from audit endpoint
- [ ] Responsive layout (stack on mobile)

DoD: Overview tab shows health, charts, activity.""",
        priority=1)

    # ── 4. Create M19 features & tasks ──
    print("\n═══ M19: TEST QUALITY & ARCHITECTURE (0.21.0) ═══")

    f19s1 = create_feature(
        "Test Infrastructure",
        "m19-test-infrastructure",
        "M19 S21.1: conftest unification, pytest markers, model imports, frontend coverage.",
    )
    create_task(f19s1,
        "Unify test fixtures in conftest.py",
        """TEST-001 | Severity: Medium | File: backend/tests/conftest.py

PROBLEM: 8+ test files duplicate SQLAlchemy engine setup instead of using shared conftest.

ACCEPTANCE CRITERIA:
- [ ] conftest.py imports ALL models for create_all()
- [ ] Shared _test_engine and _TestSession in conftest
- [ ] All test files updated to use shared fixtures
- [ ] No duplicate engine creation in test files

DoD: All tests use shared fixtures, no duplication.""",
        priority=0)

    create_task(f19s1,
        "Add pytest markers and frontend coverage",
        """TEST-002 | Severity: Low | Files: backend/pyproject.toml, frontend/vitest.config.ts

ACCEPTANCE CRITERIA:
- [ ] pytest markers: slow, integration, unit
- [ ] Marker registration in pyproject.toml [tool.pytest.ini_options]
- [ ] @vitest/coverage-v8 added to frontend
- [ ] Coverage threshold configured (80% statements)

DoD: Markers work, frontend coverage reports.""",
        priority=2)

    f19s2 = create_feature(
        "Service-Layer Tests",
        "m19-service-tests",
        "M19 S21.2: Unit tests for delivery/quality/reporting services, notification endpoints, lifecycle integration test.",
    )
    create_task(f19s2,
        "Add service-layer unit tests for delivery, quality, reporting",
        """TEST-003 | Severity: High | New files: test_delivery_service.py, test_quality_service.py, test_reporting_service.py

PROBLEM: Service-layer business logic tested only via HTTP endpoints, not in isolation.

ACCEPTANCE CRITERIA:
- [ ] DeliveryService: create, get, update, delete, list with pagination
- [ ] QualityService: AC/DoD CRUD, evidence verify/accept/reject, review gate
- [ ] ReportingService: create report, generate daily, list with pagination
- [ ] Each test file: 8-12 tests, all passing

DoD: 30+ service-layer unit tests pass.""",
        priority=0)

    create_task(f19s2,
        "Add notification HTTP endpoint tests",
        """TEST-004 | Severity: Medium | New file: backend/tests/test_notification_endpoints.py

ACCEPTANCE CRITERIA:
- [ ] GET /notifications returns paginated list
- [ ] GET /notifications?unread_only=true filters correctly
- [ ] GET /notifications/unread-count returns count
- [ ] POST /notifications/{id}/read marks as read
- [ ] POST /notifications/read-all marks all as read
- [ ] 404 for non-existent notification

DoD: 6 endpoint tests pass.""",
        priority=1)

    create_task(f19s2,
        "Create full lifecycle integration test",
        """TEST-005 | Severity: High | New file: backend/tests/test_lifecycle_integration.py

PROBLEM: No single test covers task creation → claim → progress → evidence → review → completion.

ACCEPTANCE CRITERIA:
- [ ] Test creates project → feature → task
- [ ] Task lifecycle: backlog → ready → claimed → in_progress → ready_for_review → done
- [ ] Evidence attached during in_progress
- [ ] Review round created and verdict submitted
- [ ] Quality gate enforced (DoD must pass before done)
- [ ] All operations within single test, all assertions pass

DoD: Full lifecycle test passes, covers 6+ contexts.""",
        priority=0)

    f19s3 = create_feature(
        "Event Bus Implementation",
        "m19-event-bus",
        "M19 S21.3: In-process pub/sub event bus replacing direct NotificationTrigger calls.",
    )
    create_task(f19s3,
        "Implement in-process event bus and migrate trigger calls",
        """ARCH-006 | Severity: Medium | New file: backend/app/shared/events.py

PROBLEM: Cross-context communication via direct service calls with try/except: pass. Doesn't scale.

FIX: Simple in-process EventBus with subscribe/publish.

ACCEPTANCE CRITERIA:
- [ ] EventBus class with subscribe(event_type, handler) and publish(event_type, **data)
- [ ] NotificationTrigger subscribes to all 8 event types
- [ ] Services publish events instead of calling trigger directly
- [ ] EventBus is testable (can inspect published events)
- [ ] All existing notification tests still pass

DoD: Event bus operational, trigger decoupled from producers.""",
        priority=0)

    # ── 5. Create M20 features & tasks ──
    print("\n═══ M20: EXTENDED FEATURES (0.22.0) ═══")

    f20s1 = create_feature(
        "Real-Time Notifications (SSE)",
        "m20-realtime-notifications",
        "M20 S22.1: Server-Sent Events for notification push, replacing 30s polling for critical events.",
    )
    create_task(f20s1,
        "Implement SSE notification endpoint + frontend EventSource",
        """SSE-001 | Severity: Medium | Files: backend/app/api/v1/notifications.py, frontend/src/hooks/use-notifications.ts

ACCEPTANCE CRITERIA:
- [ ] GET /api/v1/notifications/stream SSE endpoint
- [ ] Events emitted on NotificationTrigger.publish()
- [ ] Frontend EventSource with reconnect on disconnect
- [ ] Fallback to polling if SSE unavailable
- [ ] Toast (sonner) for critical events (blocking clarification, review submitted)

DoD: Real-time notifications work, polling fallback functional.""",
        priority=0)

    f20s2 = create_feature(
        "File Uploads for Evidence",
        "m20-file-uploads",
        "M20 S22.2: File attachment support for evidence (local storage + S3 adapter).",
    )
    create_task(f20s2,
        "Implement evidence file upload endpoint and UI",
        """UPLOAD-001 | Severity: Medium | Files: backend/app/api/v1/evidence.py, frontend/src/components/project/EvidenceTab.tsx

ACCEPTANCE CRITERIA:
- [ ] POST /api/v1/evidence/upload with multipart form
- [ ] Local filesystem storage (data/uploads/)
- [ ] File type whitelist: pdf, png, jpg, txt, json, csv, md
- [ ] Size limit: 10MB
- [ ] Frontend: drag-and-drop upload zone in EvidenceTab
- [ ] Uploaded file linked to evidence record

DoD: Files upload successfully, stored locally, linked to evidence.""",
        priority=0)

    f20s3 = create_feature(
        "Bulk Task Operations",
        "m20-bulk-operations",
        "M20 S22.3: Multi-select tasks, bulk status change, bulk assign.",
    )
    create_task(f20s3,
        "Implement bulk task operations",
        """BULK-001 | Severity: Medium | Files: backend/app/api/v1/delivery.py, frontend/src/components/project/DeliveryPage.tsx

ACCEPTANCE CRITERIA:
- [ ] Checkbox column in task table (list view)
- [ ] Select all / deselect all
- [ ] Bulk action bar appears when tasks selected
- [ ] Actions: change status, assign to agent
- [ ] Confirmation dialog for bulk actions
- [ ] Backend: PATCH /api/v1/tasks/bulk endpoint
- [ ] All selected tasks updated atomically

DoD: Multi-select works, bulk actions execute correctly.""",
        priority=0)

    f20s4 = create_feature(
        "Task Comments & Audit Export",
        "m20-comments-export",
        "M20 S22.4: Threaded comments on tasks + audit trail CSV/JSON export.",
    )
    create_task(f20s4,
        "Implement task comments with threading",
        """COMMENT-001 | Severity: Medium | Files: backend/app/delivery/models.py, backend/app/api/v1/delivery.py, frontend/src/components/project/TaskDetailSheet.tsx

ACCEPTANCE CRITERIA:
- [ ] Comment model: task_id, author_id, body, parent_id, created_at
- [ ] Migration 0021: comment table
- [ ] API: POST /tasks/{id}/comments, GET /tasks/{id}/comments
- [ ] Comments tab in TaskDetailSheet
- [ ] Threaded display (parent → replies)
- [ ] Create comment form with submit

DoD: Comments create/display with threading.""",
        priority=0)

    create_task(f20s4,
        "Implement audit trail export (CSV/JSON)",
        """EXPORT-001 | Severity: Low | Files: backend/app/api/v1/audit.py, frontend/src/components/project/AuditPage.tsx

ACCEPTANCE CRITERIA:
- [ ] GET /api/v1/audit/export?format=csv&project_id=...
- [ ] GET /api/v1/audit/export?format=json&project_id=...
- [ ] CSV with headers: timestamp, event_type, actor, entity, details
- [ ] JSON with nested payload
- [ ] Export button on AuditPage
- [ ] Download triggers browser save dialog

DoD: Export works for both formats, button on UI.""",
        priority=2)

    conn.close()
    print("\n═══ DONE ═══")
    print("Created: 12 new components, 60+ new modules, 17 features, 40+ tasks")
    print("All with detailed descriptions, DoD, and acceptance criteria.")


if __name__ == "__main__":
    main()
