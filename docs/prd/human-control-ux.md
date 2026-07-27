# Human Control UX — Specification

> Related: [UPCP v2 PRD](./upcp-v2.md) §3.6 | Milestone: M11

## 1. Overview

Human Control UX is the interface through which humans control AI agents and projects. Priorities: situational awareness (what needs attention right now?) and quick action (one click to result).

## 2. Attention Dashboard (Home)

### 2.1 Purpose
Home screen. Answers the question: "What needs my attention right now?"

### 2.2 Sections

| Section | Content | Priority |
|---------|---------|----------|
| 🔴 Blocked | Tasks awaiting clarification | urgent |
| 🟡 Stale | Tasks without heartbeat > 7 min | high |
| 🟠 In Review | Tasks under review | high |
| 🟢 Active | Agents currently working | normal |
| ⚪ Recent Done | Recently completed tasks | low |

### 2.3 Task card on attention dashboard

```
┌─────────────────────────────────────────────┐
│ 🔴 BLOCKED — Task #142                      │
│ "Implement user avatar upload"               │
│ Agent: claude-agent-3  •  Blocked: 23 min    │
│ Question: "Max file size for uploads?"        │
│ [Answer] [View Task] [Release]               │
└─────────────────────────────────────────────┘
```

### 2.4 Filters
- By project
- By agent
- By severity
- By status
- By date (today / week / all)

## 3. Portfolio Insights

### 3.1 All projects overview

```
┌──────────────┬──────────┬──────────┬──────────┬──────────┐
│ Project      │ Active   │ Blocked  │ Stale    │ Done/week│
├──────────────┼──────────┼──────────┼──────────┼──────────┤
│ upcp-core    │ 5 tasks  │ 1 task   │ 0        │ 12       │
│ upcp-web     │ 3 tasks  │ 0        │ 1 task   │ 8        │
│ upcp-docs    │ 1 task   │ 0        │ 0        │ 15       │
└──────────────┴──────────┴──────────┴──────────┴──────────┘
```

### 3.2 Portfolio metrics

- Velocity: tasks done per week (trend)
- Agent utilization: % of agents with active claims
- Quality score: % of tasks passing review on first attempt
- Average cycle time: from open to done

## 4. Project Drill-Down

### 4.1 View: Kanban Board

Columns by task statuses. Cards show:
- Task name
- Agent (avatar/name)
- Evidence completeness (progress bar)
- Heartbeat status (green/yellow/red)
- Priority badge

### 4.2 View: Table View

| ID | Title | Status | Agent | Evidence | Heartbeat | Actions |
|----|-------|--------|-------|----------|-----------|---------|
| 142 | Avatar upload | blocked | claude-3 | 60% | 🟡 stale | [view] [release] |

### 4.3 Filters and sorting
- Status, agent, priority, creation date
- Sort by: priority, created, updated, heartbeat

## 5. Agent Center

### 5.1 Agent list

| Agent | Status | Current Task | Claims | Done/week | Avg Cycle |
|-------|--------|--------------|--------|-----------|-----------|
| claude-agent-1 | 🟢 active | #142 | 1/3 | 8 | 22 min |
| gpt-agent-2 | ⚫ idle | — | 0/3 | 12 | 18 min |
| gemini-agent-3 | 🔴 stale | #156 | 1/3 | 5 | 35 min |

### 5.2 Agent details

- Profile: name, model, capabilities
- Active claims with heartbeat history
- Completed task history
- Settings: max_active_claims, heartbeat_interval
- API key (manage: rotate, revoke)

### 5.3 Actions
- Release claim (force release)
- Send message to inbox
- Deactivate agent
- View audit log

## 6. Notifications

### 6.1 Channels

| Channel | Type | When |
|---------|------|------|
| In-app toast | Real-time (WebSocket) | All events |
| In-app inbox | Persistent | Important events |
| Email | Async (future) | Critical: stale, blocked > 1 h |

### 6.2 Events

| Event | Priority | Description |
|-------|----------|-------------|
| `task.blocked` | high | Agent requested clarification |
| `task.stale` | high | No heartbeat > 7 min |
| `task.review_ready` | normal | Task ready for review |
| `task.changes_requested` | normal | Reviewer requested changes |
| `task.done` | low | Task completed |
| `task.auto_released` | high | Task automatically released |
| `agent.activated` | low | New agent connected |
| `review.approved` | low | Review approved |

### 6.3 API

```
GET  /api/v1/notifications?unread=true&limit=50
POST /api/v1/notifications/{id}/read
POST /api/v1/notifications/mark-all-read
```

## 7. Reports

### 7.1 Available reports

| Report | Period | Content |
|--------|--------|---------|
| Weekly Summary | weekly | tasks done, agents active, issues |
| Agent Performance | configurable | cycle time, success rate, evidence quality |
| Project Health | current | blocked, stale, velocity, quality score |
| Review Activity | weekly | reviews completed, findings, turnaround |

### 7.2 Export
- PDF (future)
- JSON API for integrations
- CSV for spreadsheets

## 8. Command Palette (Ctrl+K)

### 8.1 Purpose
Quick access to any action without navigation.

### 8.2 Commands

| Command | Action |
|---------|--------|
| `> task create` | Create a task |
| `> task find <query>` | Find a task |
| `> agent list` | List agents |
| `> project switch` | Switch project |
| `> review pending` | Show tasks pending review |
| `> blocked list` | Show blocked tasks |
| `> stale list` | Show stale tasks |
| `> report weekly` | Generate report |
| `> settings` | Open settings |

### 8.3 Navigation
- `↑↓` — navigate results
- `Enter` — execute/go to
- `Esc` — close
- `Tab` — autocomplete

## 9. Breadcrumbs

Navigation path is always visible:

```
Projects > upcp-core > Tasks > #142 "Avatar upload"
```

Every element is clickable. Allows quick return to the parent level.

## 10. Keyboard Navigation

| Combination | Action |
|-------------|--------|
| `Ctrl+K` | Command palette |
| `Ctrl+B` | Toggle sidebar |
| `Ctrl+1-5` | Switch tabs/views |
| `j/k` | Navigate list items (vim-style) |
| `Enter` | Open selected |
| `Esc` | Close modal / go back |
| `?` | Show keyboard shortcuts |

### Accessibility
- All elements accessible via Tab
- ARIA labels on all interactive elements
- Focus visible indicators
- Screen reader announcements for toast notifications
- Minimum contrast ratio 4.5:1 (WCAG AA)
