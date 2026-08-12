# Versioning Scheme

UPCP follows [Semantic Versioning 2.0](https://semver.org/) with a pre-1.0 development convention.

## Current Version

**0.19.0** — M17 Security & Stability (see `pyproject.toml` for authoritative value)

## Scheme

```
0.MINOR.PATCH
│    │      │
│    │      └─ fixes within milestone (end of sprint or hotfix)
│    │
│    └─ milestone completed
│
└─ always 0 until 1.0.0
```

## Roadmap to 1.0.0

```
0.13.0 ──▶ 0.14.0 ──▶ 0.15.0 ──▶ 0.16.0 ──▶ 0.17.0 ──▶ 0.18.0 ──▶ 0.19.0 ──▶ 0.20.0 ──▶ 0.21.0 ──▶ 0.22.0 ──▶ ...
 M11        M12        M13        M14        M15        M16         M17         M18         M19         M20
 done       done       done       done       done       partial     done        next        plan        plan
```

See `ROADMAP_UNIFIED.md` for full post-M15 plan.

### 0.18.0 — Notifications & Reporting (M16, in progress)

**Goal**: Auto-generate notifications from workflow events, add email/webhook channels, build analytics dashboard.
**Spec**: SPEC-0019
**Sprints**: 4 (1-week sprints)

| Sprint | TASK | Focus | Status |
|--------|------|-------|--------|
| S18.1 | TASK-0100 | NotificationTrigger + event hooks | ✅ DONE |
| S18.2 | TASK-0101 | NotificationChannel + EmailChannel + WebhookChannel | PENDING |
| S18.3 | TASK-0102 | AnalyticsService + 5 API endpoints | PENDING |
| S18.4 | TASK-0103 | Analytics dashboard frontend + Channel Settings UI | PENDING |

### 0.19.0 — Security & Stability (M17, planned)

**Goal**: Fix all critical/high findings from M16 audit. Harden security, fix bugs, add DB indexes.
**Spec**: SPEC-0020
**Sprints**: 4 (1-week sprints)

| Sprint | TASK | Focus |
|--------|------|-------|
| S19.1 | TASK-0104 | Critical bug fixes: query string, Project Settings route, TopBar no-ops |
| S19.2 | TASK-0105 | Security hardening: MCP auth, LLM providers, CSP, agent ownership |
| S19.3 | TASK-0106 | Database hardening: migration 0020 (indexes + ondelete), N+1 fixes |
| S19.4 | TASK-0107 | Architecture cleanup: error logging, dead code, agent inbox, lifespan |

### 0.20.0 — UX Polish, Accessibility & Settings (M18, planned)

**Goal**: Fix accessibility gaps, redesign settings, improve notification UX, enhance project dashboard.
**Spec**: SPEC-0021
**Sprints**: 4 (1-week sprints)

| Sprint | TASK | Focus |
|--------|------|-------|
| S20.1 | TASK-0108 | Accessibility: keyboard DnD, ARIA, breadcrumb UUID resolution |
| S20.2 | TASK-0109 | Settings redesign: tabbed settings with Profile, Notifications, Channels, About |
| S20.3 | TASK-0110 | Notification UX: full /notifications page, click-to-navigate |
| S20.4 | TASK-0111 | Project dashboard: health chart, velocity chart, overview enhancement |

### 0.21.0 — Test Quality & Architecture (M19, planned)

**Goal**: Unify test infrastructure, add service-layer tests, implement event bus.
**Spec**: SPEC-0022
**Sprints**: 3 (1-week sprints)

| Sprint | TASK | Focus |
|--------|------|-------|
| S21.1 | TASK-0112 | Test infrastructure: conftest unification, pytest markers |
| S21.2 | TASK-0113 | Service-layer tests + lifecycle integration test |
| S21.3 | TASK-0114 | Event bus implementation + frontend test coverage |

### 0.22.0 — Extended Features (M20, planned)

**Goal**: Real-time notifications, file uploads, bulk operations, task comments, audit export.
**Spec**: SPEC-0023
**Sprints**: 4 (1-week sprints)

| Sprint | TASK | Focus |
|--------|------|-------|
| S22.1 | TASK-0115 | Real-time notifications via SSE |
| S22.2 | TASK-0116 | File uploads for evidence |
| S22.3 | TASK-0117 | Bulk task operations |
| S22.4 | TASK-0118 | Task comments + audit export |

**1.0.0 candidacy**: After M20 complete + production hardening sprint.

### 0.14.0 — Critical Fixes & Security

**Goal**: No broken features, no critical security gaps.
**Items**: 10 (6 broken features + 4 security)
**Sprints**: 2 (4 weeks)

| Sprint | Items | Points | Focus |
|--------|-------|--------|-------|
| S14.1 (2w) | 0.1–0.6 | 10 | Broken features: TaskDetailSheet execution, HealthPage DB, /health endpoint, AgentActivitySummary, ReportsPage export, EntityFormDialog select |
| S14.2 (2w) | 1.1–1.4 | 5 | Security: CORS headers, SSRF validation, error message sanitization, dependency scanning |

**Definition of Done**:
- [ ] TaskDetailSheet execution tab shows real agent data from API
- [ ] HealthPage shows actual DB connection status
- [ ] Backend /health endpoint checks DB (`SELECT 1`)
- [ ] AgentActivitySummary fetches from API (or removed if no endpoint)
- [ ] ReportsPage export uses `apiRequest` wrapper
- [ ] EntityFormDialog uses shadcn `<Select>`
- [ ] CORS `allow_headers` restricted per environment
- [ ] GitHub adapter validates owner/repo params
- [ ] Git adapter errors don't expose stderr
- [ ] Dependency scanning in CI

### 0.16.0 — Performance & Accessibility

**Goal**: Fast, accessible UI. No wasted loads, no inaccessible controls.
**Items**: 6 (3 perf + 3 a11y)
**Sprints**: 1 (2 weeks)

| Sprint | Items | Points | Focus |
|--------|-------|--------|-------|
| S16.1 (2w) | 4.1–4.3, 5.1–5.3 | 8 | Performance: bundle splitting, staleTime, BoardView endpoint. Accessibility: aria-labels, touch targets, scroll hints |

**Definition of Done**:
- [ ] Bundle < 300KB
- [ ] staleTime configured (no unnecessary refetches)
- [ ] BoardView uses single /tasks endpoint
- [ ] All icon buttons have aria-labels
- [ ] Touch targets ≥ 44px
- [ ] Tables have horizontal scroll hints

### 0.15.0 — Architecture & Backend Cleanup

**Goal**: Clean codebase, consistent APIs, maintainable frontend.
**Items**: 18 (10 backend + 8 frontend arch)
**Sprints**: 3 (6 weeks)

| Sprint | Items | Points | Focus |
|--------|-------|--------|-------|
| S15.1 (2w) | 2.4, 2.8, 2.10, 3.2–3.5 | 8 | Quick wins: Git Provider PATCH, OpenAPI docs, Settings route, useProjectId dedup, dead code, Ctrl+K, Math.random |
| S15.2 (2w) | 2.1–2.3, 3.1 | 9 | Backend: N+1 in Search, eager loading, pagination consistency. Frontend: api.ts split |
| S15.3 (2w) | 2.7, 2.9, 3.6–3.8 | 8 | Backend: response schemas, /tasks endpoint. Frontend: logic to hooks, UUID resolution, ReviewVerdictCard |

**Definition of Done**:
- [ ] Git Providers have PATCH endpoint
- [ ] All endpoints have OpenAPI summary/description
- [ ] Settings route exists and renders
- [ ] useProjectId used in all components (no copy-paste)
- [ ] Dead code removed (Layout.tsx, unused hooks)
- [ ] Single Ctrl+K handler
- [ ] No `Math.random()` keys
- [ ] Search uses single UNION query
- [ ] Critical queries use eager loading
- [ ] Quality/GitRead endpoints have pagination
- [ ] Response schemas consistent (Pydantic response_model)
- [ ] /projects/{id}/tasks endpoint exists
- [ ] Business logic moved to hooks
- [ ] TaskDetailSheet shows resolved names (not UUIDs)
- [ ] ReviewVerdictCard receives onAccept/onReject

### 1.0.0 — Production Ready

**Goal**: Ship it. No broken features, good performance, solid test coverage.
**Items**: 33 (6 perf + 15 UX + 12 tests)
**Sprints**: 4 (8 weeks)

| Sprint | Items | Points | Focus |
|--------|-------|--------|-------|
| S16.1 (2w) | 4.1–4.3, 5.1–5.3 | 8 | Performance: bundle splitting, staleTime, BoardView endpoint. Accessibility: aria-labels, touch targets, scroll hints |
| S16.2 (2w) | 4.4–4.6, 5.4–5.8 | 9 | Performance: lazy mount, dnd-kit lazy, responsive BoardView. UX: password toggle, router nav, AuditPage search, ReportsPage dates, CommandPalette actions |
| S16.3 (2w) | 6.1–6.8 | 9 | Tests: LoginPage, SetupPage, ProjectList, AppShell, TopBar, AuthContext, api.ts, integration |
| S16.4 (2w) | 5.9–5.15, 6.9–6.12 | 7 | Polish: animations, micro-interactions, typography, project switcher, quick-edit, column toggle, breadcrumb. Test cleanup: reduce `as any`, formatRelativeTime, useHotkeys, storage |

**Definition of Done (1.0.0)**:
- [ ] Bundle < 300KB
- [ ] staleTime configured (no unnecessary refetches)
- [ ] BoardView uses single /tasks endpoint
- [ ] All icon buttons have aria-labels
- [ ] Touch targets ≥ 44px
- [ ] Tables have horizontal scroll hints
- [ ] Auth pages use router (not window.location)
- [ ] All critical pages have tests
- [ ] Auth flow tested end-to-end
- [ ] `as any` casts eliminated from mocks
- [ ] No broken buttons/forms
- [ ] Dashboard shows real data
- [ ] All P0 and P1 items from audit closed

## Milestone Summary

| Version | Milestone | Items | Sprints | Weeks |
|---------|-----------|-------|---------|-------|
| 0.14.0 | Critical Fixes & Security | 10 | 2 | 4 |
| 0.15.0 | Architecture & Backend Cleanup | 18 | 3 | 6 |
| 1.0.0 | Production Ready | 33 | 4 | 8 |
| **Total** | | **61** | **9** | **18** |

## Velocity Assumptions

- Solo developer + AI agent assistance
- ~8-10 story points per 2-week sprint
- Points: S=1, M=2, L=3
- 30% buffer for meetings, context switching, unexpected issues

## Version History

| Version | Milestone | Date |
|---------|-----------|------|
| 0.1.0 | Initial scaffold | 2026-07-24 |
| 0.2.0 | M0 — Foundation | 2026-07-24 |
| 0.3.0 | M1 — Projects & RBAC | 2026-07-24 |
| 0.4.0 | M2 — Structure, Delivery, Quality | 2026-07-25 |
| 0.5.0 | M3 — Git Read | 2026-07-25 |
| 0.6.0 | M4 — MCP & CLI | 2026-07-26 |
| 0.7.0 | M5 — Frontend Foundation | 2026-07-26 |
| 0.8.0 | M6 — Reports & LLM | 2026-07-26 |
| 0.9.0 | M7 — Auth, RBAC, Agents | 2026-07-27 |
| 0.10.0 | M8 — Runtime Foundation | 2026-07-27 |
| 0.11.0 | M9 — Agent Workflow MVP | 2026-07-27 |
| 0.12.0 | M10 — Evidence & Review | 2026-07-27 |
| 0.13.0 | M11 — Human Control UX | 2026-07-27 |
| 0.14.0 | M12 — Critical Fixes & Security | 2026-07-30 |
| 0.15.0 | M13 — Architecture & Backend Cleanup | 2026-08-07 |
| 0.16.0 | M14 — Performance & Accessibility | 2026-08-07 |
| 0.17.0 | M15 — Agent Workflow | 2026-08-11 |
| 0.18.0 | M16 — Notifications & Reporting | planned |
| 0.19.0 | M17 — Security & Stability | planned |
| 0.20.0 | M18 — UX Polish, A11y & Settings | planned |
| 0.21.0 | M19 — Test Quality & Architecture | planned |
| 0.22.0 | M20 — Extended Features | planned |

## How to Update Versions

### At milestone completion:

1. Update `pyproject.toml` — `version = "0.X.Y"`
2. Update `frontend/package.json` — `"version": "0.X.Y"`
3. Update this file's version history table (fill in date)
4. Update `CHANGELOG.md` — move `[Unreleased]` items to new version section
5. Update `PROJECT_STATUS.md` — set new version and milestone

### Commit convention:

```
chore: bump version to 0.X.Y — <milestone summary>
```

### Files to update:

| File | Field |
|------|-------|
| `pyproject.toml` | `version = "0.X.Y"` |
| `frontend/package.json` | `"version": "0.X.Y"` |
| `CHANGELOG.md` | New section `## [0.X.Y] - YYYY-MM-DD` |
| `VERSIONING.md` | Version history table + roadmap |
| `PROJECT_STATUS.md` | Version + milestone fields |

## Rules

- **Never skip versions** in the history
- **Never retroactively change** released versions
- **Git tags** are created at 1.0.0+ only
- **Both** pyproject.toml and package.json must match
- **CHANGELOG.md** is the human-readable history
- **Sprint boundaries** don't trigger version bumps — only milestones do
- **Hotfixes** between milestones get patch bumps (0.14.1, etc.)
