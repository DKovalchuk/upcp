# Attention Dashboard

The main page of UPCP. Focused on what requires the user's attention right now.

---

## 1. Overview

Dashboard is not a vanity statistics page, but an action-oriented inbox. Each section contains items that need action: review, answer, fix, or confirmation.

**URL:** `/`

---

## 2. Sections

### 2.1 Needs Your Review

**What:** Tasks submitted by agents for review and awaiting a decision.

**Data:** Task title, Agent name, Submitted at, Evidence count, Review round number.

**Action:** Click → task detail sheet on the Reviews tab.

**Empty state:** "No tasks awaiting review."

---

### 2.2 Open Agent Questions

**What:** Clarification requests from agents that require an answer.

**Data:** Task title, Agent name, Question (truncated), Blocking indicator, Created at.

**Action:** Click → task detail sheet on the Clarifications tab.

**Empty state:** "No open questions from agents."

**Sorting:** Blocking items first, then by date.

---

### 2.3 Blocked Tasks

**What:** Tasks in `blocked` status.

**Data:** Task title, Block reason, Blocked since, Assigned agent.

**Action:** Click → task detail sheet.

**Empty state:** "No blocked tasks."

---

### 2.4 Stale Agent Claims

**What:** Claim without heartbeat for > 7 minutes.

**Data:** Task title, Agent name, Last heartbeat, Claim age.

**Action:** Click → task detail sheet, Execution tab. "Release claim" button.

**Empty state:** "All agent claims are active."

**Indicator:** Yellow/orange badge for stale.

---

### 2.5 Failed Quality Gates

**What:** Tasks where DoD items failed.

**Data:** Task title, Failed count / Total, Specific failed items.

**Action:** Click → task detail sheet, DoD tab.

**Empty state:** "All quality gates passing."

---

### 2.6 Rejected Tasks

**What:** Tasks with a `reject` verdict in the last review round.

**Data:** Task title, Reviewer, Rejection summary, Rejected at.

**Action:** Click → task detail sheet, Reviews tab.

**Empty state:** "No rejected tasks."

---

### 2.7 Agent Verdicts Waiting Confirmation

**What:** Agent reviewer has issued a verdict, but a human has not confirmed it.

**Data:** Task title, Reviewer agent, Verdict, Summary.

**Action:** Click → task detail, Reviews tab with Approve/Reject buttons.

**Empty state:** "No verdicts awaiting confirmation."

---

### 2.8 Low Health Projects

**What:** Projects with a low health score.

**Metric:**
```
health = 100
  - (blocked_tasks * 15)
  - (stale_claims * 10)
  - (failed_dod * 10)
  - (open_clarifications * 5)
  - (rejected_tasks * 10)
```

**Threshold:** < 70 = low health.

**Data:** Project name, Health score (circular progress), Top issue.

**Action:** Click → project detail.

**Empty state:** "All projects healthy."

---

### 2.9 Recent Agent Activity

**What:** The last 10 agent actions.

**Data:** Agent name, Action type (badge), Target (task title), Timestamp.

**Action:** Click → task detail or agent detail.

**Empty state:** "No recent agent activity."

---

## 3. Layout

```
+------------------------------------------------------------------+
| Dashboard                                                        |
+------------------------------------------------------------------+
| [Needs Review: 3] [Open Questions: 2] [Blocked: 1] [Stale: 0]   |
+------------------------------------------------------------------+
| Needs Your Review (3)                    | Recent Agent Activity  |
| ┌────────────────────────────────────┐   | ┌──────────────────┐  |
| │ TASK-0042  by claude-builder       │   | │ claude-builder   │  |
| │ Submitted 15m ago · 3 evidence     │   | │ claimed TASK-045 │  |
| └────────────────────────────────────┘   | └──────────────────┘  |
+------------------------------------------+------------------------+
| Open Agent Questions (2)                 | Low Health Projects    |
| ┌────────────────────────────────────┐   | ┌──────────────────┐  |
| │ 🔒 TASK-0039  "Format for dates?"  │   | │ UPCP v2  [42%]   │  |
| └────────────────────────────────────┘   | └──────────────────┘  |
+------------------------------------------+------------------------+
```

**Layout:** Two-column. Left — action items. Right — activity + health.

**Summary cards** at the top — quick metrics with click-to-filter.

---

## 4. Data Fetching

TanStack Query with auto-refresh every 30 seconds. `useDashboardAttention()` hook. staleTime 15s.

---

## 5. Empty State

If all sections are empty:
```
All clear! No items need your attention right now.
[Go to Projects →]
```

---

## 6. Accessibility

- Each section is a `<section>` with `aria-label`.
- Summary cards — `role="status"` with `aria-live="polite"`.
- Clickable elements — `<a>` or `<button>` with focus ring.
- Blocking indicators — `aria-label="blocking"`.
