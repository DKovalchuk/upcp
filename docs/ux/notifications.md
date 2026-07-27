# Notifications UX

UPCP notification system.

---

## 1. Bell Icon

**Location:** Top bar.

**Badge:** Number of unread notifications (max `99+`). Hidden when 0.

### Dropdown

Click → last 10 notifications.

```
┌──────────────────────────────────────────────────┐
│ Notifications                        [Mark all ✓]│
├──────────────────────────────────────────────────┤
│ TASK-0042 submitted for review                   │
│ claude-builder · 5m ago                          │
│                                                  │
│ Blocking question on TASK-0039                   │
│ claude-builder · 30m ago                         │
│                                                  │
│ Agent claim expired: TASK-0045                   │
│ gpt-4 · 1h ago                                  │
│                                                  │
│                    [View All Notifications →]     │
└──────────────────────────────────────────────────┘
```

Unread indicator: filled/empty dot. Click → navigate to resource + mark read.

---

## 2. Notification Types

| Type | Title | Icon | Action |
|-----|-------|--------|----------|
| `review_submitted` | "TASK-XXXX submitted for review" | `FileCheck` | Task Reviews tab |
| `clarification_open` | "Blocking question on TASK-XXXX" | `MessageCircleQuestion` | Task Clarifications |
| `clarification_answered` | "Question answered on TASK-XXXX" | `MessageCircleCheck` | Task Clarifications |
| `claim_expired` | "Agent claim expired: TASK-XXXX" | `Clock` | Task Execution |
| `claim_stale` | "Agent heartbeat stale: TASK-XXXX" | `AlertTriangle` | Task Execution |
| `review_approved` | "TASK-XXXX approved" | `CheckCircle` | Task Reviews |
| `review_rejected` | "TASK-XXXX rejected" | `XCircle` | Task Reviews |
| `review_needs_changes` | "TASK-XXXX needs changes" | `AlertCircle` | Task Reviews |
| `quality_gate_failed` | "Quality gate failed: TASK-XXXX" | `ShieldX` | Task DoD |
| `agent_verdict` | "Agent verdict: TASK-XXXX" | `Bot` | Task Reviews |
| `task_blocked` | "TASK-XXXX is blocked" | `Lock` | Task detail |
| `task_completed` | "TASK-XXXX completed" | `CheckCheck` | Task detail |
| `evidence_rejected` | "Evidence rejected on TASK-XXXX" | `FileX` | Task Evidence |

---

## 3. Notifications Page

**URL:** `/notifications`

### Layout

```
┌──────────────────────────────────────────────────────────┐
│ Notifications                            [Mark All Read] │
│                                                          │
│ Filter: [All ▾] [Unread ▾] [Project ▾]                  │
├──────────────────────────────────────────────────────────┤
│ Today                                                    │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ TASK-0042 submitted for review                       │ │
│ │ claude-builder · 5m ago                              │ │
│ │ "Implemented UserService CRUD with tests."           │ │
│ │                                    [Mark Read] [🗑️] │ │
│ ├──────────────────────────────────────────────────────┤ │
│ │ Blocking question on TASK-0039                       │ │
│ │ claude-builder · 30m ago                             │ │
│ │ "Should due_date use ISO 8601 or Unix format?"       │ │
│ │                                    [Mark Read] [🗑️] │ │
│ └──────────────────────────────────────────────────────┘ │
│                                                          │
│ Yesterday                                                │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ Agent claim expired: TASK-0045                       │ │
│ │ gpt-4 · 1d ago                                      │ │
│ │                                    [Mark Read] [🗑️] │ │
│ └──────────────────────────────────────────────────────┘ │
│                                                          │
│ [Load More]                                              │
└──────────────────────────────────────────────────────────┘
```

### Filters

| Filter | Options |
|--------|---------|
| Read status | All / Unread / Read |
| Type | All / Review / Clarification / Claim / Quality / Agent |
| Project | All / [project list] |

### Grouping

By day: Today, Yesterday, Older.

---

## 4. Interaction

- **Click** → mark read + navigate.
- **[Mark Read]** → mark without navigate.
- **[Mark All Read]** → all.
- **[🗑️]** → delete single (no confirmation).

---

## 5. Preferences

**URL:** `/settings/notifications`

```
Notification Preferences

Email Notifications              [Off]

Notify me about:
☑ Review submissions
☑ Blocking clarifications
☑ Claim expirations
☑ Quality gate failures
☐ Agent heartbeats (non-stale)
☑ Review verdicts
☐ Evidence attachments

Digest: [Instant ▾]
Quiet Hours: [22:00] — [08:00]

[Save Preferences]
```

---

## 6. Real-time

- Polling every 30 sec (TanStack Query).
- Badge updates in real-time.
- Toast (sonner) for critical events: blocking clarification, review submitted.

---

## 7. Data Model

```typescript
interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  read: boolean;
  actor_type: 'agent' | 'human' | 'system';
  actor_id: string;
  actor_name: string;
  entity_type: 'task' | 'project' | 'agent' | 'review';
  entity_id: string;
  project_id: string;
  created_at: string;
}
```
