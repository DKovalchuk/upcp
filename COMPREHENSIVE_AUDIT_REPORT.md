# UPCP Comprehensive Audit Report

**Date**: 2026-07-25
**Branch**: `feature/TASK-0062-notifications`
**Scope**: Backend API, Frontend UI, MCP Server, Security

---

## Executive Summary

Comprehensive audit performed across 4 dimensions: API functionality, UI/UX, MCP server, and security. Total findings: **40 issues** identified, **11 issues fixed** during this audit cycle.

| Severity | Found | Fixed | Remaining |
|----------|-------|-------|-----------|
| Critical | 6 | 3 | 3 |
| High | 11 | 3 | 8 |
| Medium | 13 | 3 | 10 |
| Low | 10 | 2 | 8 |

---

## Issues Fixed During This Audit

### 1. Test Isolation Bug (5 failing tests)
**File**: `backend/tests/test_search.py`
**Issue**: Module-level `_setup_data()` called at import time; other test files' `make_test_app()` calls `drop_all`/`create_all`, wiping data.
**Fix**: Converted to pytest fixture with `autouse=True` that recreates schema and seeds data before every test.

### 2. Mypy Type Errors (5 errors in 2 files)
**Files**: `backend/app/api/v1/dashboard.py`, `backend/app/api/v1/quality.py`
**Issue**: `**dict` unpacking from `dict[str, object]` didn't match Pydantic model fields.
**Fix**: Explicit field construction with proper typing. Changed service return types to `dict[str, Any]`.

### 3. Ruff Import Order
**File**: `backend/tests/test_search.py`
**Fix**: Auto-fixed with `ruff check --fix`.

### 4. Docker Frontend Missing Dependencies
**Issue**: `cmdk` and `@dnd-kit/core` packages added to `package.json` but Docker image was stale.
**Fix**: Rebuilt Docker frontend image with `docker compose build --no-cache frontend`. Added `vite.config.ts` as read-only volume mount in `docker-compose.yml`.

### 5. Health Page Broken (Proxy Issue)
**Issue**: Frontend called `/health` which wasn't proxied through vite to the backend.
**Fix**: Added `/api/v1/health` endpoint to backend `main.py`. Changed frontend `fetchHealth()` to use `${API_BASE}/health`. Removed `/health` proxy from vite config.

### 6. Missing `/reports` Route
**Issue**: Sidebar linked to `/reports` but no route existed in `router.tsx`.
**Fix**: Added `reportsRoute` to router. Added empty `projectId` handler showing "Select a project" empty state.

### 7. Breadcrumb Showing UUID
**Issue**: BreadcrumbBar used raw URL segments, showing UUIDs for project paths.
**Fix**: Implemented `buildBreadcrumbs()` that filters UUID segments and uses human-readable labels from `SEGMENT_LABELS` map.

### 8. Project Table Rows Not Clickable
**Issue**: `ProjectTable` rendered plain `<TableRow>` without navigation.
**Fix**: Added `cursor-pointer`, `hover:bg-muted/50`, and `onClick` handler using `navigate()` to project detail.

### 9. ProjectTable Not Using StatusBadge
**Issue**: Inline `<span>` with hardcoded primary color instead of design system component.
**Fix**: Replaced with `<StatusBadge status={project.status} />`.

---

## Remaining Critical Issues

### C-1: No Authentication/Authorization
**All endpoints are publicly accessible.** `get_current_user()` returns hardcoded admin. No JWT, no API keys, no session management.
**Impact**: Complete unauthorized access to all data.
**Remediation**: Implement JWT authentication middleware.

### C-2: Hardcoded Secrets
`secret_key = "change_me_local_only"` in config. Database passwords in docker-compose defaults.
**Impact**: Credential compromise if deployed without override.
**Remediation**: Remove defaults, require env vars for production.

### C-3: CORS Allows All Origins
`allow_origins=["*"]` when `env="local"`.
**Impact**: Cross-origin attacks if deployed without config change.
**Remediation**: Restrict to explicit origins.

---

## Remaining High Issues

### H-1: No Rate Limiting
No protection against brute force or DoS attacks.

### H-2: SQL Injection Risk via Sort Parameter
Dynamic `getattr(Project, sort_by)` with user input in projects endpoint.

### H-3: Project Creation Button Non-Functional
"New Project" button in ProjectList has `onClick: () => {}` (no-op). EntityFormDialog never rendered.

### H-4: Edit/Delete Buttons Non-Functional
ProjectDetail header edit/delete buttons have no handlers.

### H-5: TaskDetailSheet Missing Add Functionality
AC/DoD/Subtasks tabs show items but "Add" buttons don't work.

### H-6: Missing Security Headers
No `Content-Security-Policy`, `Referrer-Policy`, or `Permissions-Policy`.

### H-7: Command Injection Risk
`LocalGitAdapter._run()` accepts user-controlled `repo_path` without validation.

### H-8: Error Messages Expose Internals
Git adapter errors include raw stderr output.

---

## Remaining Medium Issues

### M-1: Inconsistent Pagination
Quality and gitread endpoints lack pagination.

### M-2: N+1 Query in Search
3 separate queries instead of single UNION.

### M-3: Settings Route Missing
Sidebar links to `/settings` but no route or component exists.

### M-4: HealthPage Hardcodes Database Status
Database card always shows "Connected" regardless of actual state.

### M-5: ConfirmDialog Closes Before Async Mutation
Dialog closes synchronously before `onConfirm` completes.

### M-6: No CSRF Protection
No CSRF tokens for state-changing operations.

### M-7: SSRF Risk in GitHub Adapter
User-controlled `owner`/`repo` params used in URL construction.

### M-8: Missing Structured Logging
No correlation IDs, no security event logging.

### M-9: ReportsPage Uses Raw Fetch
`handleExportMarkdown` bypasses centralized `apiRequest` helper.

### M-10: Frontend Bundle >500KB
Index chunk is 574KB. Needs code splitting.

---

## Remaining Low Issues

### L-1: Duplicate `formatRelativeTime` in Dashboard and AuditPage
### L-2: `useUrlPagination` uses synthetic `PopStateEvent`
### L-3: BoardView fetches tasks in parallel without deduplication
### L-4: No dependency scanning in CI/CD
### L-5: No SRI for external resources
### L-6: No request ID tracking
### L-7: Breadcrumb shows "health" lowercase (minor)
### L-8: Notification button shows "3" with no context

---

## MCP Server Audit Summary

- **Transport**: HTTP JSON-RPC 2.0 over FastAPI (non-standard, manual implementation)
- **Tools**: 12 total (6 read, 6 write) covering projects, features, tasks
- **Resources**: 1 (context_pack)
- **Tests**: ~74 test cases across 5 files
- **No Authentication**: All MCP endpoints publicly accessible
- **Session Management**: Fixed in TASK-0038 (injected sessions work correctly)

---

## Test Coverage

| Area | Tests | Coverage |
|------|-------|----------|
| Backend | 237 passed | 91% |
| Frontend | 140 passed (22 files) | N/A |
| MCP | ~74 tests | 87% (server), 84% (tools) |

---

## Files Changed

| File | Change |
|------|--------|
| `backend/tests/test_search.py` | Fixed test isolation with pytest fixtures |
| `backend/app/api/v1/dashboard.py` | Fixed mypy type errors |
| `backend/app/api/v1/quality.py` | Fixed mypy type errors |
| `backend/app/quality/service.py` | Added `Any` import, fixed return type |
| `backend/app/reporting/dashboard.py` | Added `Any` import |
| `backend/app/main.py` | Added `/api/v1/health` endpoint |
| `frontend/src/lib/api.ts` | Changed `fetchHealth()` to use API_BASE |
| `frontend/src/router.tsx` | Added `/reports` route |
| `frontend/src/components/project/ReportsPage.tsx` | Added empty projectId handler |
| `frontend/src/components/layouts/BreadcrumbBar.tsx` | Fixed UUID display |
| `frontend/src/components/ProjectTable.tsx` | Added clickable rows + StatusBadge |
| `frontend/vite.config.ts` | Fixed proxy target, host binding |
| `frontend/Dockerfile` | Unchanged (image rebuilt) |
| `docker-compose.yml` | Added vite.config.ts mount + VITE_API_URL |

---

## Next Steps

1. **Immediate**: Implement authentication (Critical)
2. **Week 1**: Add rate limiting, fix CORS, remove hardcoded secrets
3. **Week 2**: Fix non-functional buttons (New Project, Edit/Delete), add Settings page
4. **Week 3**: Add CSP headers, CSRF protection, input validation
5. **Ongoing**: Security audits, dependency scanning, penetration testing
