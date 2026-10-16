# TASK-0128: Dashboard Maximum Test Coverage

**Spec:** SPEC-0025
**Status:** PARTIAL (updated 2026-10-16 — unit levels green, e2e/a11y/security parts remain)
**Priority:** HIGH
**Effort:** 13pts
**Depends on:** TASK-0120 through TASK-0127

## Objective

Maximum test coverage for the redesigned dashboard: positive, negative, boundary, edge cases, accessibility, performance, security. Automated (Vitest + pytest) + Playwright MCP E2E.

---

## Part A: Backend API Tests (pytest)

**File:** `backend/tests/api/test_dashboard.py`

### A1. GET /api/v1/dashboard/stats — Positive

| ID | Test | Description |
|----|------|-------------|
| A1.1 | returns all required fields | Response has `project_count`, `task_counts_by_status`, `recent_projects`, `recent_activity`, `done_this_week`, `blocked_count`, `claimed_count`, `health_score` |
| A1.2 | project_count matches DB | Count of projects with `status != 'archived'` |
| A1.3 | task_counts_by_status sums correctly | `backlog + in_progress + review + done + blocked == total tasks` |
| A1.4 | done_this_week = tasks completed in last7d | Only tasks with `status=done` AND `updated_at >= now()-7d` |
| A1.5 | blocked_count = tasks with status=blocked | Direct count match |
| A1.6 | claimed_count = tasks with active claims | Tasks with `task_claim` where `released_at IS NULL` |
| A1.7 | health_score in [0,100] | Integer range check |
| A1.8 | recent_projects limited to5 | Array length ≤5 |
| A1.9 | recent_projects sorted by updated_at DESC | Most recent first |
| A1.10 | recent_activity limited to10 | Array length ≤10 |
| A1.11 | stats with project_id filter | Only counts tasks/features belonging to that project |
| A1.12 | stats with project_id=nonexistent | Returns zeros, not error |
| A1.13 | stats with empty DB | All counts are0, arrays empty, no errors |
| A1.14 | response time <500ms | Performance check |

### A2. GET /api/v1/dashboard/stats — Negative

| ID | Test | Description |
|----|------|-------------|
| A2.1 | no auth token →401 | `Authorization` header missing |
| A2.2 | invalid token →401 | Malformed JWT |
| A2.3 | expired token →401 | Token with `exp < now()` |
| A2.4 | project_id not UUID →422 | Invalid UUID format |
| A2.5 | project_id integer →422 | Wrong type |

### A3. GET /api/v1/dashboard/stats — Boundary

| ID | Test | Description |
|----|------|-------------|
| A3.1 | done_this_week with task completed exactly at7d boundary | `updated_at = now()-7d` — include or exclude consistently |
| A3.2 | done_this_week with task completed1s after7d boundary | `updated_at = now()-7d+1s` — should NOT count |
| A3.3 | done_this_week with task completed1s before7d boundary | `updated_at = now()-7d-1s` — should count |
| A3.4 | health_score exactly0 | All issues maxed out |
| A3.5 | health_score exactly100 | No issues |
| A3.6 | task_counts with1000 tasks | Performance, correct counts |
| A3.7 | task_counts with tasks in ALL statuses | backlog, in_progress, claimed, blocked, review, ready_for_review, changes_requested, done |
| A3.8 | recent_projects with exactly5 projects | Returns5, not fewer |
| A3.9 | recent_projects with6 projects | Returns5 (most recent), drops oldest |
| A3.10 | recent_projects with0 projects | Returns empty array |

### A4. GET /api/v1/analytics/velocity — Positive

| ID | Test | Description |
|----|------|-------------|
| A4.1 | returns8 weeks by default | Array length =8 |
| A4.2 | returns custom weeks count | `?weeks=4` returns4 items |
| A4.3 | each item has week + count | Schema validation |
| A4.4 | weeks are ISO format | `"2026-W35"` pattern |
| A4.5 | weeks are consecutive | No gaps |
| A4.6 | counts are non-negative | `count >=0` |
| A4.7 | scoped to project_id | Only tasks from that project |
| A4.8 | empty project returns zeros | All counts =0 |
| A4.9 | counts only done tasks | Tasks with other statuses excluded |
| A4.10 | handles DST transitions | Weeks crossing daylight saving |

### A5. GET /api/v1/analytics/velocity — Negative/Boundary

| ID | Test | Description |
|----|------|-------------|
| A5.1 | no auth →401 | Missing token |
| A5.2 | weeks=0 →422 or empty | Edge case |
| A5.3 | weeks=100 →422 or caps at52 | Max reasonable value |
| A5.4 | weeks=-1 →422 | Negative not allowed |
| A5.5 | weeks=1.5 →422 | Float not allowed |
| A5.6 | project_id nonexistent → empty | Not an error |
| A5.7 | velocity with10000 tasks completed in1 week | Performance test |

### A6. GET /api/v1/dashboard/attention — Positive

| ID | Test | Description |
|----|------|-------------|
| A6.1 | returns all9 fields | `needs_review`, `open_questions`, `blocked_tasks`, `stale_claims`, `failed_dod`, `rejected_tasks`, `agent_verdicts_waiting`, `low_health_projects`, `recent_activity` |
| A6.2 | needs_review only pending rounds | `state='pending'` review rounds |
| A6.3 | open_questions only open clarifications | `state='open'` |
| A6.4 | blocked_tasks only blocked status | `status='blocked'` |
| A6.5 | stale_claims have stale heartbeats | `last_heartbeat_at < now()-5min` |
| A6.6 | failed_dod only failed items | `status='failed'`, not `pending` |
| A6.7 | low_health_projects have score <80 | Threshold check |
| A6.8 | attention scoped to project_id | Only items for that project |
| A6.9 | each item has required fields | `task_id`, `title`, `project_id` present |

### A7. GET /api/v1/dashboard/attention — Negative/Boundary

| ID | Test | Description |
|----|------|-------------|
| A7.1 | no auth →401 | Missing token |
| A7.2 | project_id nonexistent → all empty | Not error |
| A7.3 | attention with50 stale claims | Performance, pagination? |
| A7.4 | attention with stale claim at exactly5min boundary | `last_heartbeat_at = now()-5min` |
| A7.5 | attention with stale claim at4m59s | NOT stale |
| A7.6 | attention with stale claim at5m01s | IS stale |

### A8. GET /api/v1/portfolio/overview — Positive

| ID | Test | Description |
|----|------|-------------|
| A8.1 | returns all projects | Count matches DB |
| A8.2 | each project has health_score | Integer0-100 |
| A8.3 | each project has task counts | `tasks_done`, `tasks_total` |
| A8.4 | each project has top_issue | String, may be empty |
| A8.5 | total_tasks sums all projects | Cross-project validation |
| A8.6 | tasks_by_status aggregated | Matches sum of per-project counts |

### A9. GET /api/v1/portfolio/overview — Negative/Boundary

| ID | Test | Description |
|----|------|-------------|
| A9.1 | no auth →401 | Missing token |
| A9.2 |0 projects → empty array | Not error |
| A9.3 |1 project → array of1 | Works correctly |
| A9.4 |50 projects → performance | Response time <1s |

---

## Part B: Frontend Unit Tests (Vitest + React Testing Library)

### B1. KPI Cards — Positive

**File:** `frontend/src/components/dashboard/KPICards.test.tsx`

| ID | Test | Description |
|----|------|-------------|
| B1.1 | renders5 cards | All5 KPI cards visible |
| B1.2 | shows correct labels | "Projects", "Active Tasks", "Done This Week", "Blocked", "Health" |
| B1.3 | shows correct values | Numbers match mock data |
| B1.4 | each card has icon | Lucide icon rendered |
| B1.5 | variant colors correct | Primary, info, success, warning, danger |
| B1.6 | health score green ≥80 | CSS class check |
| B1.7 | health score amber50-79 | CSS class check |
| B1.8 | health score red <50 | CSS class check |
| B1.9 | health score exactly80 → green | Boundary |
| B1.10 | health score exactly79 → amber | Boundary |
| B1.11 | health score exactly50 → amber | Boundary |
| B1.12 | health score exactly49 → red | Boundary |
| B1.13 | health score0 → red | Minimum |
| B1.14 | health score100 → green | Maximum |

### B2. KPI Cards — Navigation (Drill-Down)

| ID | Test | Description |
|----|------|-------------|
| B2.1 | Projects card → /projects | Link href check |
| B2.2 | Active Tasks → /delivery?status=in_progress,claimed,blocked | URL params |
| B2.3 | Done This Week → /delivery?status=done&since=7d | Time filter |
| B2.4 | Blocked → /delivery?status=blocked | Status filter |
| B2.5 | Health (no project) → /projects | Falls back to projects list |
| B2.6 | Health (project selected) → /projects/:id | Project-specific link |
| B2.7 | hover shows pointer cursor | CSS cursor check |
| B2.8 | keyboard Enter activates link | Accessibility |
| B2.9 | keyboard Space activates link | Accessibility |

### B3. KPI Cards — Negative/Edge

| ID | Test | Description |
|----|------|-------------|
| B3.1 | loading state → skeletons | `data-slot="skeleton"` elements |
| B3.2 | error state → error message | "Failed to load" visible |
| B3.3 | all counts =0 | Cards render with "0" values |
| B3.4 | very large counts (99999) | No overflow, displays correctly |
| B3.5 | negative count → shows0 | Cannot be negative |
| B3.6 | health_score undefined → fallback | Shows "N/A" or0 |
| B3.7 | API returns null fields → safe render | No crash |

### B4. Donut Chart — Positive

**File:** `frontend/src/components/dashboard/TaskDistributionDonut.test.tsx`

| ID | Test | Description |
|----|------|-------------|
| B4.1 | renders SVG pie chart | `<svg>` element with paths |
| B4.2 | correct number of sectors | One per non-zero status |
| B4.3 | center label shows total | Sum of all counts |
| B4.4 | legend shows all statuses | Each name + count |
| B4.5 | colors match design | backlog=slate, in_progress=blue, review=amber, done=emerald, blocked=red |
| B4.6 | single status → single sector | Only1 non-zero |
| B4.7 | all statuses equal | Equal proportions |

### B5. Donut Chart — Navigation

| ID | Test | Description |
|----|------|-------------|
| B5.1 | click backlog sector → /delivery?status=backlog | Navigation |
| B5.2 | click in_progress sector → /delivery?status=in_progress | Navigation |
| B5.3 | click review sector → /delivery?status=review | Navigation |
| B5.4 | click done sector → /delivery?status=done | Navigation |
| B5.5 | click blocked sector → /delivery?status=blocked | Navigation |
| B5.6 | keyboard accessible sectors | Tab + Enter |

### B6. Donut Chart — Edge Cases

| ID | Test | Description |
|----|------|-------------|
| B6.1 | all counts =0 → empty state | "No tasks yet" message |
| B6.2 | single task (all in one status) | Renders correctly |
| B6.3 |10000 tasks | Performance, no lag |
| B6.4 | counts with decimals → rounded | Integer display |
| B6.5 | missing status field → fallback | Default to0 |

### B7. Velocity Chart — Positive

**File:** `frontend/src/components/dashboard/VelocityChart.test.tsx`

| ID | Test | Description |
|----|------|-------------|
| B7.1 | renders line chart | `<svg>` with path elements |
| B7.2 |8 data points (default weeks) | Correct count |
| B7.3 | custom weeks count | `weeks=4` →4 points |
| B7.4 | X-axis shows week labels | "W35", "W36", etc. |
| B7.5 | Y-axis shows counts | Correct scale |
| B7.6 | hover shows tooltip | Week + count |
| B7.7 | gradient fill below line | Area chart styling |
| B7.8 | data point click navigates | `/delivery?status=done&week=W35` |

### B8. Velocity Chart — Edge Cases

| ID | Test | Description |
|----|------|-------------|
| B8.1 | empty data → flat line at0 | Not an error |
| B8.2 | all weeks have0 count | Flat line |
| B8.3 | single week has spike (100 tasks) | Y-axis scales correctly |
| B8.4 | consecutive weeks with0 then spike | Line renders correctly |
| B8.5 | weeks span year boundary | W52 → W1 transition |
| B8.6 | API error → error state | Graceful fallback |
| B8.7 | loading → skeleton | Loading indicator |

### B9. Attention Cards — Positive

**File:** `frontend/src/components/dashboard/AttentionCards.test.tsx`

| ID | Test | Description |
|----|------|-------------|
| B9.1 | renders all7 sections | Review, Questions, Blocked, Stale, Failed DoD, Rejected, Verdicts |
| B9.2 | plus LowHealth section |8 total |
| B9.3 | each section has count badge | Badge shows item count |
| B9.4 | count badge hidden when0 | No badge for empty sections |
| B9.5 | items show title/text | Truncated task title or question |
| B9.6 | items show metadata | Author, timestamp, severity |

### B10. Attention Cards — Navigation

| ID | Test | Description |
|----|------|-------------|
| B10.1 | review item → task detail | Click navigates |
| B10.2 | question item → task clarifications | Click navigates |
| B10.3 | blocked item → task detail | Click navigates |
| B10.4 | stale item → task execution | Click navigates |
| B10.5 | failed DoD item → task quality | Click navigates |
| B10.6 | rejected item → task detail | Click navigates |
| B10.7 | verdict item → review detail | Click navigates |
| B10.8 | low health project → /projects/:id | Click navigates |
| B10.9 | "View all →" when >3 items | Link appears |
| B10.10 | "View all →" correct URL | Filtered view URL |
| B10.11 | keyboard Enter on item | Accessible |
| B10.12 | keyboard Space on item | Accessible |

### B11. Attention Cards — Edge Cases

| ID | Test | Description |
|----|------|-------------|
| B11.1 | all sections empty | "No items" for each |
| B11.2 | one section has50 items | Performance, virtualized? |
| B11.3 | item with very long title | Truncated with ellipsis |
| B11.4 | item with empty title | Fallback display |
| B11.5 | item with missing task_id | Graceful fallback |
| B11.6 | stale claim with NULL heartbeat | Handled correctly |
| B11.7 | failed DoD with empty item list | Shows "No failed items" |

### B12. Portfolio Table — Positive

**File:** `frontend/src/components/dashboard/PortfolioTable.test.tsx`

| ID | Test | Description |
|----|------|-------------|
| B12.1 | renders project rows | All projects listed |
| B12.2 | columns: Name, Health, Tasks, Status, Top Issue | All columns present |
| B12.3 | health score progress bar | Visual indicator |
| B12.4 | health color: ≥80 green | Correct class |
| B12.5 | health color:50-79 amber | Correct class |
| B12.6 | health color: <50 red | Correct class |
| B12.7 | tasks show "done/total" format | "30/36" style |
| B12.8 | status badge renders | "Active", "Paused" |
| B12.9 | click row → /projects/:id | Navigation |

### B13. Portfolio Table — Edge Cases

| ID | Test | Description |
|----|------|-------------|
| B13.1 |0 projects → component hidden | Not rendered |
| B13.2 |1 project → component hidden | Only show for >1 |
| B13.3 |2 projects → shows table | Minimum to display |
| B13.4 |5 projects → shows all | No pagination |
| B13.5 |6 projects → "Show more" button | Pagination |
| B13.6 | "Show more" click → reveals all | Expands list |
| B13.7 | project with0 tasks | "0/0" display |
| B13.8 | project with NULL description | No crash |
| B13.9 | project with very long name | Truncated |
| B13.10 | health=0 edge case | Red bar renders |

### B14. Project Selector — Positive

**File:** `frontend/src/components/dashboard/ProjectSelector.test.tsx`

| ID | Test | Description |
|----|------|-------------|
| B14.1 | default "All Projects" | Initial selection |
| B14.2 | lists all projects | Options match API data |
| B14.3 | select project → URL updates | `?project_id=xxx` in URL |
| B14.4 | select "All Projects" → URL clears | No project_id param |
| B14.5 | URL with project_id → correct selection | Initial load with param |
| B14.6 | selected project scopes KPI | KPI hooks receive project_id |
| B14.7 | selected project scopes attention | Attention hooks receive project_id |
| B14.8 | selected project scopes velocity | Velocity hook receives project_id |
| B14.9 | portfolio always global | Not affected by selector |

### B15. Project Selector — Edge Cases

| ID | Test | Description |
|----|------|-------------|
| B15.1 |0 projects → selector hidden | Not rendered |
| B15.2 |1 project → selector with2 options | "All" + that project |
| B15.3 | project_id in URL doesn't exist | Falls back to "All" |
| B15.4 | project_id is not UUID | Falls back to "All" |
| B15.5 | rapid selection changes | Debounced, no race conditions |
| B15.6 | project deleted while viewing | Falls back gracefully |

### B16. Activity Feed — Positive

**File:** `frontend/src/components/dashboard/LiveActivityFeed.test.tsx`

| ID | Test | Description |
|----|------|-------------|
| B16.1 | renders event list | Events visible |
| B16.2 | events sorted by timestamp DESC | Newest first |
| B16.3 | event shows actor name | "Commander", "admin" |
| B16.4 | event shows action | "claimed task", "changed status" |
| B16.5 | event shows entity name | Task title |
| B16.6 | event shows relative time | "2m ago" |
| B16.7 | colored dot per actor type | Violet=agent, primary=human |
| B16.8 | click event → entity detail | Navigation |
| B16.9 | SSE connected indicator | Green dot |

### B17. Activity Feed — Edge Cases

| ID | Test | Description |
|----|------|-------------|
| B17.1 |0 events → "No recent activity" | Empty state |
| B17.2 | event with missing actor | Fallback to "System" |
| B17.3 | event with missing entity | Fallback display |
| B17.4 | event with very long payload | Truncated |
| B17.5 | SSE disconnected → polling fallback |30s polling active |
| B17.6 | SSE reconnects → indicator updates | Green dot returns |
| B17.7 | duplicate events from SSE | Deduplication |

### B18. Agent Activity Summary — Positive

**File:** `frontend/src/components/dashboard/AgentActivitySummary.test.tsx`

| ID | Test | Description |
|----|------|-------------|
| B18.1 | renders agent list | All agents shown |
| B18.2 | agent shows avatar | Initials or icon |
| B18.3 | agent shows name | "Commander" etc. |
| B18.4 | agent shows task title | Current task |
| B18.5 | progress bar with percentage | "67%" |
| B18.6 | active agent → emerald bar | Green progress |
| B18.7 | stale agent → orange bar | Warning color |
| B18.8 | pulse animation on active | CSS animation |
| B18.9 | stale indicator | Clock icon or warning |
| B18.10 | click agent → /agents/:id | Navigation |

### B19. Agent Activity — Edge Cases

| ID | Test | Description |
|----|------|-------------|
| B19.1 |0 agents → "No active agents" | Empty state |
| B19.2 | agent with0% progress | Bar at start |
| B19.3 | agent with100% progress | Bar full |
| B19.4 | agent with NULL task | "Idle" display |
| B19.5 | agent with NULL heartbeat | "Unknown" status |
| B19.6 | all agents stale | All orange bars |
| B19.7 | agent with progress >100 | Capped at100 |

### B20. Dashboard Integration — Full Component

**File:** `frontend/src/components/Dashboard.test.tsx` (update existing)

| ID | Test | Description |
|----|------|-------------|
| B20.1 | renders all5 rows | KPI, Charts, Attention, Activity+Agents, Portfolio |
| B20.2 | loading → full skeleton | All sections show skeletons |
| B20.3 | error → error boundary | Graceful error display |
| B20.4 | empty DB → empty states | All sections show empty messages |
| B20.5 | partial data (stats ok, attention error) | Stats render, attention shows error |
| B20.6 | SSE indicator visible | Connected/disconnected state |
| B20.7 | project selector renders | Dropdown visible |
| B20.8 | responsive grid classes | Correct Tailwind classes |
| B20.9 | stagger animations applied | CSS classes present |
| B20.10 | dark mode classes | `dark:` variants applied |

---

## Part C: Playwright MCP E2E Tests

### C1. Dashboard Full Visual Verification

| Step | Action | Verify |
|------|--------|--------|
| C1.1 | Login as admin | Redirect to `/` |
| C1.2 | Wait for dashboard load | No loading skeletons |
| C1.3 | Snapshot: KPI row |5 cards with numbers |
| C1.4 | Snapshot: Charts row | Donut + Velocity visible |
| C1.5 | Snapshot: Attention row | Cards with counts |
| C1.6 | Snapshot: Activity+Agents | Feed + agent list |
| C1.7 | Snapshot: Portfolio | Table with projects |
| C1.8 | Verify no console errors | No red errors in console |
| C1.9 | Verify no "Something went wrong" | No error boundaries triggered |

### C2. KPI Drill-Down Navigation

| Step | Action | Verify |
|------|--------|--------|
| C2.1 | Click "Projects" card | URL = `/projects` |
| C2.2 | Verify projects page loads | Table visible |
| C2.3 | Navigate back to `/` | Dashboard loads |
| C2.4 | Click "Active Tasks" card | URL contains `/delivery` |
| C2.5 | Verify filtered tasks | Only active statuses shown |
| C2.6 | Navigate back, click "Done" card | URL has `status=done` |
| C2.7 | Navigate back, click "Blocked" card | URL has `status=blocked` |
| C2.8 | Navigate back, click "Health" card | URL = `/projects/:id` |
| C2.9 | Verify project detail loads | Overview tab visible |

### C3. Donut Chart Interaction

| Step | Action | Verify |
|------|--------|--------|
| C3.1 | Locate donut chart | SVG visible |
| C3.2 | Hover over "done" sector | Tooltip shows count |
| C3.3 | Click "done" sector | URL has `status=done` |
| C3.4 | Verify delivery filtered | Only done tasks |
| C3.5 | Navigate back, click "backlog" sector | URL has `status=backlog` |
| C3.6 | Check legend | All statuses listed |

### C4. Attention Item Navigation

| Step | Action | Verify |
|------|--------|--------|
| C4.1 | Locate attention section | Section visible |
| C4.2 | Click first review item | Task detail opens |
| C4.3 | Verify task detail shows | Title, status, tabs visible |
| C4.4 | Navigate back, click blocked item | Task detail opens |
| C4.5 | Navigate back, click low health project | Project page loads |
| C4.6 | Click "View all →" (if visible) | Filtered view loads |

### C5. Project Selector

| Step | Action | Verify |
|------|--------|--------|
| C5.1 | Locate selector dropdown | "All Projects" selected |
| C5.2 | Open dropdown | Project list appears |
| C5.3 | Select "UPCP" | URL has `?project_id=xxx` |
| C5.4 | Verify KPI numbers change | Scoped to UPCP |
| C5.5 | Verify attention updates | Only UPCP items |
| C5.6 | Select "All Projects" | Aggregate numbers return |
| C5.7 | Copy URL with `?project_id=xxx` | Paste in new tab → scoped |

### C6. Responsive Layout

| Step | Action | Verify |
|------|--------|--------|
| C6.1 | Set viewport1440x900 | Desktop layout |
| C6.2 | Verify5-col KPI row | Cards in one row |
| C6.3 | Verify3-col attention | Grid layout |
| C6.4 | Set viewport768x1024 | Tablet layout |
| C6.5 | Verify2-col KPI | Cards wrap to2 rows |
| C6.6 | Verify2-col attention | Grid adjusts |
| C6.7 | Set viewport375x812 | Mobile layout |
| C6.8 | Verify single column | Everything stacked |
| C6.9 | Verify no horizontal scroll | No overflow |
| C6.10 | Charts resize | Donut + velocity fit |

### C7. SSE Real-Time Updates

| Step | Action | Verify |
|------|--------|--------|
| C7.1 | Open dashboard | SSE indicator green |
| C7.2 | Note current activity count | Baseline |
| C7.3 | Create task via API (`curl`) | New event appears |
| C7.4 | Verify activity feed updated | New event visible |
| C7.5 | Change task status via API | Status change event |
| C7.6 | Verify notification bell count | Unread increased |
| C7.7 | Check console for SSE errors | No errors |

### C8. Error & Edge Cases

| Step | Action | Verify |
|------|--------|--------|
| C8.1 | Login with fresh user (no projects) | Empty dashboard |
| C8.2 | Verify "Create project" CTA | Button visible |
| C8.3 | Create project, reload | Dashboard populates |
| C8.4 | Toggle dark mode | All sections render |
| C8.5 | Verify colors in dark mode | Contrast correct |
| C8.6 | Navigate rapidly between pages | No crashes |
| C8.7 | Check accessibility | Tab navigation works |

### C9. Performance Verification

| Step | Action | Verify |
|------|--------|--------|
| C9.1 | Open DevTools Network tab | Note API call count |
| C9.2 | Dashboard initial load | <3s total |
| C9.3 | Verify refetch intervals | Stats:60s, Attention:30s |
| C9.4 | Check for unnecessary re-renders | React DevTools |
| C9.5 | Large dataset (100 projects) | No performance degradation |

---

## Part D: Accessibility Tests

| ID | Test | Description |
|----|------|-------------|
| D1 | KPI cards have aria-labels | "Projects: 2, click to view" |
| D2 | Donut sectors have aria-labels | "Done:30 tasks, click to filter" |
| D3 | Attention items keyboard navigable | Tab + Enter |
| D4 | Portfolio rows keyboard navigable | Tab + Enter |
| D5 | Color not sole indicator | Health uses icon + text, not just color |
| D6 | Screen reader: all sections announced | Heading hierarchy correct |
| D7 | Focus visible on all interactive elements | Focus ring visible |
| D8 | Chart data available as text | Table fallback for screen readers |

---

## Part E: Security Tests

| ID | Test | Description |
|----|------|-------------|
| E1 | stats endpoint requires auth |401 without token |
| E2 | velocity endpoint requires auth |401 without token |
| E3 | attention endpoint requires auth |401 without token |
| E4 | portfolio endpoint requires auth |401 without token |
| E5 | project_id SQL injection attempt | Input sanitized |
| E6 | XSS in project name | Escaped in HTML |
| E7 | XSS in task title | Escaped in HTML |
| E8 | rate limiting on stats endpoint |429 after threshold |
| E9 | CORS headers correct | Only allowed origins |

---

## Execution Matrix

| Phase | When | Command | Expected |
|-------|------|---------|----------|
| Unit | After each task | `npm run test` | All green |
| Backend | After backend changes | `pytest backend/tests/api/test_dashboard.py` | All green |
| Lint | After each file | `ruff check .` | No errors |
| Type | After frontend changes | `npm run build` | No TS errors |
| E2E | After all tasks | Playwright MCP (manual steps B1-B9) | All pass |
| Regression | Final | `npx playwright test` (existing21) | All pass |

## Acceptance Criteria

- [ ] A1-A9:42 backend tests pass — *partial: `tests/test_dashboard.py` + `tests/test_attention_dashboard.py` = 31 pass (incl. new stats/attention coverage); velocity negative/boundary (A5) and portfolio (A8/A9) rows still untested*
- [ ] B1-B20:65+ frontend unit tests pass — *partial: dashboard unit tests green (Dashboard, Donut, Velocity, AttentionCards, PortfolioTable, AgentActivitySummary); full suite 336/336 pass; not all B-matrix rows have dedicated cases*
- [ ] C1-C9:45+ Playwright MCP steps verified — *not done*
- [ ] D1-D8:8 accessibility checks pass — *not done*
- [ ] E1-E9:9 security checks pass — *not done (generic 401 coverage exists in `test_auth_middleware_protection`, not dashboard-specific)*
- [ ] Existing21 Playwright tests: no regressions — *not re-run*
- [x] `npm run build`: clean — *tsc --noEmit exit 0, lint 0 errors*
- [x] `ruff check`: clean
- [ ] Dark mode: all components verified — *not done*
- [ ] Responsive:375px,768px,1440px verified — *not done*

### Status evidence (2026-10-16)

- Frontend: `npx vitest run` → **47 files, 336/336 pass** (incl. fixing 34 regression failures caused by filter-system/sprint commits — router/AuthProvider mock gaps in test files, verified against develop baseline).
- Backend: `pytest tests/test_dashboard.py tests/test_attention_dashboard.py -q` → **31 passed**; `ruff check app tests` clean; `mypy app` clean (112 files).
- Remaining before DONE: Parts C (E2E), D (a11y), E (security matrix rows), dark-mode/responsive visual verification.
