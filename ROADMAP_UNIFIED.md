# UPCP Unified Roadmap — Post-M15

**Created:** 2026-08-12
**Updated:** 2026-10-31 (TASK-0160: gaps M16/M18/M19 закрыты, After-M20 п.1-3 закрыты, п.4 → TASK-0161…0163)
**Source:** M16 Comprehensive Audit + existing plans
**Sprint size:** 1 week
**Current:** 0.22.0 (M19 + M20 complete)
**Next:** production hardening — TASK-0161 (E2E coverage), TASK-0162 (deployment guide), TASK-0163 (performance benchmarks)

---

## Milestone Overview

```
0.17.0 ✅ ──▶ 0.18.0 ──▶ 0.19.0 ✅ ──▶ 0.20.0 ──▶ 0.21.0 ✅ ──▶ 0.22.0 ✅ → ...
   M15          M16         M17          M18          M19          M20
   done       done        done      done        done ✅       done
```

After M20: Этап 1 ✅ (TASK-0145…0153) → M16/M18 gaps ✅ (TASK-0102/0103/0108/0109,
TASK-0154/0155/0156) → Production hardening (TASK-0161…0163).
Status-аудит 2026-10-24: M16 и M18 оказались реализованы глубже, чем значилось
(roadmap показывал 1/4 и 0/4) — см. PROJECT_STATUS «Status-аудит 2026-10-24».

---

## M16: Notifications & Reporting (0.18.0)

**Goal:** Auto-generate notifications from workflow events, add email/webhook channels, build analytics dashboard.
**Spec:** SPEC-0019
**Sprints:** 4
**Status:** ✅ DONE (2026-10-25 — все 4 спринта закрыты: S18.1/S18.2 при аудите,
S18.3 gaps → TASK-0102, S18.4 gaps → TASK-0103)

| Sprint | TASK | Focus | Points | Status |
|--------|------|-------|--------|--------|
| S18.1 ✅ | TASK-0100 | NotificationTrigger + event hooks | 8 | DONE (audit 2026-10-24) |
| S18.2 ✅ | TASK-0101 | NotificationChannel + EmailChannel + WebhookChannel + migration 0020 | 8 | DONE (audit 2026-10-24) |
| S18.3 ✅ | TASK-0102 | AnalyticsService + 6 API endpoints | 8 | DONE (TASK-0102 closed 2026-10-25: pagination + API-тесты) |
| S18.4 ✅ | TASK-0103 | Analytics dashboard frontend + Channel Settings UI | 8 | DONE (TASK-0103 closed 2026-10-25: nav-item /analytics + тесты) |

**Exit criteria:**
- Notifications auto-generated from all 8 workflow events ✅
- Email channel sends via SMTP, webhook via HTTP ✅
- Analytics dashboard shows trends, velocity, agent performance ✅
- Channel config UI in Settings ✅
- 705+ backend tests, 260+ frontend tests ✅ (сейчас ~944 / ~433)

---

## M17: Security & Stability (0.19.0)

**Goal:** Fix all critical/high findings from M16 audit. Harden security, fix bugs, add DB indexes.
**Spec:** SPEC-0020
**Sprints:** 4
**Source:** Audit findings S1-S10, U1, U5, U6, A4-A7, Q2

| Sprint | TASK | Focus | Points |
|--------|------|-------|--------|
| S19.1 | TASK-0104 | Critical bug fixes: query string, Project Settings route, TopBar no-ops, Settings version | 5 |
| S19.2 | TASK-0105 | Security hardening: MCP auth, LLM providers, CSP, agent middleware | 8 |
| S19.3 | TASK-0106 | Database hardening: migration 0020 (indexes + ondelete), N+1 fixes | 5 |
| S19.4 | TASK-0107 | Architecture cleanup: notification error logging, dead auth module, agent inbox stub | 5 |

**Exit criteria:**
- MCP endpoints require authentication
- LLM providers either removed or properly implemented
- All FK columns have indexes + ondelete
- Query string bug fixed, Project Settings route works
- TopBar Profile/Settings navigate correctly
- Dead `auth/` module removed
- Agent inbox returns real events

---

## M18: UX Polish, Accessibility & Settings (0.20.0)

**Goal:** Fix accessibility gaps, redesign settings, improve notification UX, enhance project dashboard.
**Spec:** SPEC-0021
**Sprints:** 4
**Status:** ✅ DONE (2026-10-25 — все 4 спринта закрыты: S20.3/S20.4 при аудите,
S20.1 gaps → TASK-0108, S20.2 gaps → TASK-0109)

| Sprint | TASK | Focus | Points | Status |
|--------|------|-------|--------|--------|
| S20.1 ✅ | TASK-0108 | Accessibility: keyboard DnD, ARIA on accordions, breadcrumb UUID resolution | 8 | DONE (TASK-0108 closed 2026-10-25: name-resolution, keyboard/ARIA-тесты) |
| S20.2 ✅ | TASK-0109 | Settings redesign: tabbed settings with Profile, Notifications, Channels, About | 8 | DONE (TASK-0109 closed 2026-10-25: PATCH channel + edit-диалог, evidence) |
| S20.3 ✅ | TASK-0110 | Notification UX: full /notifications page, click-to-navigate, error handling | 5 | DONE (audit 2026-10-24) |
| S20.4 ✅ | TASK-0111 | Project dashboard: health chart, velocity chart, overview tab enhancement | 5 | DONE (audit 2026-10-24) |

**Exit criteria:**
- BoardView fully keyboard-accessible ✅ (KeyboardSensor + keyboard-тесты, TASK-0108)
- All interactive elements have ARIA attributes ✅
- Settings page has 4 tabs (Profile, Notifications, Channels, About) ✅ (фактически 5: +Appearance)
- /notifications page with filters and grouping ✅
- Notification click navigates to entity ✅
- Breadcrumbs show resolved entity names (not UUIDs) ✅ (name-resolution, TASK-0108)
- Project overview shows health score + mini charts ✅

---

## M19: Test Quality & Architecture (0.21.0)

**Goal:** Unify test infrastructure, add service-layer tests, improve coverage, implement event bus.
**Spec:** SPEC-0022
**Sprints:** 3
**Status:** ✅ DONE (2026-10-25 — S21.2/S21.3 при аудите; S21.1 закрыт TASK-0112:
engine dedup + enforcement-тест red 17 → green)

| Sprint | TASK | Focus | Points | Status |
|--------|------|-------|--------|--------|
| S21.1 ✅ | TASK-0112 | Test infrastructure: conftest unification, pytest markers, model imports | 5 | DONE (TASK-0112 closed 2026-10-25: engine dedup + enforcement-тест) |
| S21.2 | TASK-0113 | Service-layer tests + notification endpoint tests + lifecycle integration test | 8 | ✅ DONE (audit 2026-10-24) |
| S21.3 | TASK-0114 | Event bus implementation + frontend test coverage | 8 | ✅ DONE (audit 2026-10-24) |

**Exit criteria:**
- All test files use shared conftest fixtures ✅ (engine dedup — TASK-0112; hermetic drop-first sweep — TASK-0159)
- Service-layer unit tests for delivery, quality, reporting ✅
- Full lifecycle integration test (create → claim → evidence → review → complete) ✅
- Event bus replaces direct trigger calls ✅
- Frontend has coverage reporting (@vitest/coverage-v8) ✅
- `as any` hygiene ✅ (TASK-0155: 90 → 0 + enforcement-бюджет)

---

## M20: Extended Features (0.22.0)

**Goal:** Add missing components for production readiness: real-time notifications, file uploads, bulk ops.
**Spec:** SPEC-0023
**Sprints:** 4
**Source:** Audit §7 Missing Components

| Sprint | TASK | Focus | Points | Status |
|--------|------|-------|--------|--------|
| S22.1 | TASK-0115 | SSE notification push | 8 | ✅ DONE |
| S22.2 | TASK-0116 | File uploads for evidence | 8 | ✅ DONE |
| S22.3 | TASK-0117 | Bulk task operations | 5 | ✅ DONE |
| S22.4 | TASK-0118 | Task comments + audit export | 8 | ✅ DONE |

**Exit criteria:**
- Real-time notifications via SSE (no more 30s polling for critical events)
- Evidence can include file attachments (not just URLs)
- Multiple tasks can be selected and bulk-updated
- Tasks have threaded comments
- Audit trail exportable as CSV/JSON
- All 800+ backend tests pass
- All 300+ frontend tests pass

---

## Version Summary

| Version | Milestone | Sprints | Status | Key Deliverable |
|---------|-----------|---------|--------|-----------------|
| 0.17.0 | M15 ✅ | 4/4 | DONE | Agent Workflow |
| 0.18.0 | M16 | 4/4 | DONE (gaps закрыты 2026-10-25) | Notifications + Analytics |
| 0.19.0 | M17 ✅ | 4/4 | DONE | Security + Stability |
| 0.20.0 | M18 | 4/4 | DONE (gaps закрыты 2026-10-25) | UX + A11y + Settings |
| 0.21.0 | M19 ✅ | 3/3 | DONE | Tests + Architecture |
| 0.22.0 | M20 ✅ | 4/4 | DONE | Extended Features |

### After M20 (remaining work)

1. ~~**Этап 1 — находки SPEC-0024**~~ ✅ закрыт (security TASK-0145…0148,
   perf TASK-0149…0153 — 2026-10-24/25)
2. ~~**Gaps-батч M16/M18/M19**~~ ✅ закрыт (TASK-0102/0103/0108/0109/0112,
   TASK-0154/0155/0156 — 2026-10-25)
3. ~~**M18/M16 закрытие + версии**~~ ✅ закрыт TASK-0160: VERSIONING
   синхронизирован без бампа (0.18.0/0.20.0 delivered в 0.19.0–0.22.0)
4. **Production hardening (следующий)** — E2E coverage (TASK-0161),
   deployment guide (TASK-0162), performance benchmarks (TASK-0163);
   хвосты закрыты (TASK-0128 ✅, TASK-0154 ✅, TASK-0156 ✅)

---

## Critical Path

```
M16 S18.2 (channels) ──▶ S18.3 (analytics) ──▶ S18.4 (frontend)
M17 S19.1 (bugs) ──▶ S19.2 (security) ──▶ S19.3 (DB) ──▶ S19.4 (cleanup)
M18 S20.1 (a11y) ──▶ S20.2 (settings) ──▶ S20.3 (notifications) ──▶ S20.4 (dashboard)
M19 S21.1 (test infra) ──▶ S21.2 (service tests) ──▶ S21.3 (event bus)
M20 S22.1 (WebSocket) ──▶ S22.2 (uploads) ──▶ S22.3 (bulk) ──▶ S22.4 (comments)
```

## Parallelism

- M17 S19.1 (bug fixes) can start immediately — no dependency on M16
- M18 S20.1 (a11y) can start in parallel with M17 S19.3-S19.4
- M19 S21.1 (test infra) can start in parallel with M18 S20.3-S20.4

## Model Allocation

| Milestone | Routine (MiMo/DeepSeek) | Pro |
|-----------|------------------------|-----|
| M16 | S18.2-S18.4 (all) | — |
| M17 | S19.1, S19.3, S19.4 | S19.2 (security review) |
| M18 | S20.1, S20.3, S20.4 | S20.2 (settings architecture) |
| M19 | S21.1, S21.2 | S21.3 (event bus design) |
| M20 | S22.3, S22.4 | S22.1 (WebSocket), S22.2 (S3) |

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| M17 security changes break existing auth | High | Feature flags, test-first, gradual rollout |
| M18 settings redesign breaks existing layout | Medium | Keep current settings as fallback tab |
| M19 event bus is over-engineered | Medium | Start with simple in-process pub/sub, not full message queue |
| M20 WebSocket complexity | Medium | SSE as fallback, start with polling + toast |
| Scope creep in M20 | High | Strict sprint boundaries, defer non-critical items |
