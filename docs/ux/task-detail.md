# Task Detail UX

Detailed task view with tabs for all aspects of execution.

---

## 1. Overview

Two modes:
- **Sheet (slide-over)** — default, opened when clicking on a task.
- **Full page** — via deep link `/projects/:id/tasks/:tid`.

---

## 2. Header

```
┌──────────────────────────────────────────────────┐
│ TASK-0042                              [×]       │
│ Add User model with RBAC                         │
│ Status: in_progress │ Priority: P1 │ Assignee:   │
│ claude-builder                                   │
│ Feature: Auth System │ Component: Backend Core   │
└──────────────────────────────────────────────────┘
```

---

## 3. Tabs

### 3.1 Details

Core information: Title, Description (markdown), Status, Priority, Feature, Component, Module, Assignee, Created/Updated at.

---

### 3.2 Execution

**Claim Info:** Agent name, Claimed at, Expires at, Last heartbeat.

**Stale Warning:** If heartbeat > 7 min:
```
⚠️ Agent heartbeat is stale (last: 15m ago). Claim may expire.
[Release Claim]
```

**Progress Timeline:** List of progress reports — summary, timestamp, progress bar.

**Actions:** [Release Claim], [Reassign], [Move to Backlog].

---

### 3.3 Clarifications

Filters: Open | Answered | All.

```
┌─────────────────────────────────────────────────┐
│ 🔒 Blocking · claude-builder · 30m ago          │
│ "Should due_date use ISO 8601 or Unix format?"  │
│ [Type your answer...]              [Send]       │
└─────────────────────────────────────────────────┘
```

---

### 3.4 Evidence

```
┌─────────────────────────────────────────────────┐
│ 📋 test_output · claude-builder · 1h ago        │
│ pytest: 47 passed in 3.2s                       │
│ ✅ Verified                                     │
│ [Verify] [Reject]                       [🗑️]   │
└─────────────────────────────────────────────────┘
```

**Actions:** Verify, Reject, Attach Evidence. Filters: verified/pending/rejected/all.

---

### 3.5 DoD

```
☐ Write unit tests     [pending]
☑ Create migration     [passed]
☐ Update docs          [pending]
☑ Run linter           [passed]

Progress: 2/4 (50%) ████████░░░░░░░░
Quality Gate: ❌ NOT PASSED
```

**Actions:** Toggle status, Add Item.

---

### 3.6 Subtasks

```
☐ Create SQLAlchemy model  [pending]
☑ Write Alembic migration  [done]
☐ Add CRUD service         [in_progress]
```

**Actions:** Toggle status, Add, Edit.

---

### 3.7 Reviews

```
▼ Round 1 · gpt-4-reviewer · needs_changes · 2 findings
──────────────────────────────────────────────────────
[medium] code_quality: Missing error handling in create()
         backend/app/users/service.py:42-58

[info] code_quality: Unused import
       backend/app/users/service.py:3

Verdict: needs_changes — "Fix error handling and remove unused import."
```

**Human confirmation buttons:** [Confirm & Approve] [Request Changes] [Reject].

---

### 3.8 Git

```
Branch:  feature/task-0042-user-model
Commit:  abc1234 — feat: add User model (2h ago)
PR/MR:   !42 "Add User model" — merged
```

---

### 3.9 Audit

Timeline of all actions:

```
12:00  task.created      — by system
12:05  task.claimed      — by claude-builder
12:10  evidence.attached — test_output by claude-builder
12:30  task.submitted    — for review
12:45  review.finding    — medium by gpt-4
12:45  review.verdict    — needs_changes by gpt-4
```

---

## 4. Sheet vs Page

| Aspect | Sheet | Page |
|--------|-------|------|
| URL | `?task=:tid` | `/projects/:id/tasks/:tid` |
| Opening | Click in delivery | Deep link |
| Closing | Esc / click outside | Back navigation |
| Context | Delivery page visible on the left | Full screen |
| Width | `w-full sm:max-w-2xl` | 100% |

---

## 5. Responsive

| Breakpoint | Sheet | Tabs |
|-----------|-------|------|
| < 640px | Full width overlay | Scrollable tabs |
| 640–1023px | 512px | All visible |
| ≥ 1024px | 672px | All visible |
