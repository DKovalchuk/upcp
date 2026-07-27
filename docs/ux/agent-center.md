# Agent Center UX

AI agent management: profiles, tokens, scopes, assignments, activity.

---

## 1. Overview

Agent Center is a single page for managing all agents.

**URL:** `/agents`

---

## 2. Agent List

### Table Columns

| Column | Description |
|--------|-------------|
| Name | Name + type badge |
| Status | active / inactive / revoked |
| Role | reader / contributor / builder / reviewer |
| Active Tasks | Number of claimed tasks |
| Last Activity | Relative time |
| Token Status | active / expired / revoked |

### Toolbar

- Search by name
- Filter by status (active, inactive, revoked)
- Filter by type (llm, script, human_assisted)
- [New Agent] button

### Agent Row

```
┌─────────────────────────────────────────────────────────────────┐
│ claude-opus-builder │ active │ contributor │ 3 tasks │ 5m ago  │
│ llm                 │        │             │         │         │
└─────────────────────────────────────────────────────────────────┘
```

Click → Agent Detail.

---

## 3. Agent Detail

**URL:** `/agents/:id`

### Header

```
┌──────────────────────────────────────────────────┐
│ claude-opus-builder                        [Edit] │
│ Type: llm · Status: active                       │
│ "Code builder agent based on Claude Opus"        │
│ Created: 2026-07-20 · Last active: 5m ago        │
└──────────────────────────────────────────────────┘
```

### Tabs

#### 3.1 Profile

Name, Type, Description, Capabilities (tags), Status toggle.

#### 3.2 Tokens

| Column | Description |
|--------|-------------|
| Name | Token name |
| Prefix | First 12 characters + "..." |
| Scopes | Scope tags |
| Created | Date |
| Last Used | Date |
| Status | active / expired / revoked |

**Actions:** [Generate Token] (modal, shown once), [Revoke] (ConfirmDialog).

#### 3.3 Scopes

Checkbox grid:

```
                Read    Write
Projects         ✅      ❌
Structure        ✅      ❌
Delivery         ✅      ✅
Quality          ✅      ✅
Evidence         ✅      ✅
Review           ❌      ❌
Audit            ✅      ❌
Git              ✅      ❌
```

#### 3.4 Assignments

| Column | Description |
|--------|-------------|
| Project | Name |
| Role | Role |
| Assigned | Date |
| Tasks | done / total |

**Actions:** [Assign to Project], [Remove Assignment].

#### 3.5 Claims

| Column | Description |
|--------|-------------|
| Task | Title + link |
| Status | active / expired / released / completed |
| Claimed | Timestamp |
| Duration | Duration |
| Last Heartbeat | Relative time |

#### 3.6 Actions

Action feed:

```
12:05  claim_task       TASK-0042 "Add User model"
12:10  attach_evidence  TASK-0042 test_output
12:30  submit_review    TASK-0042
```

#### 3.7 Clarifications

Clarification requests from this agent. Filters: open | answered | blocking | all.

#### 3.8 Evidence

Evidence attached by this agent. Filters: verified | unverified | rejected | all.

#### 3.9 Reviews

Review rounds where this agent is the reviewer.

#### 3.10 Audit

Full audit trail for this agent.

---

## 4. New Agent Modal

```
┌──────────────────────────────────┐
│ Create New Agent                 │
│                                  │
│ Name: [                        ] │
│ Type: [llm ▾]                    │
│ Description: [                 ] │
│ Capabilities: [tag] [tag] [+ ]   │
│                                  │
│ [Cancel]              [Create]   │
└──────────────────────────────────┘
```

---

## 5. Empty States

| Tab | Message |
|-----|---------|
| Tokens | "No tokens generated. [Generate Token]" |
| Assignments | "Not assigned to any projects. [Assign]" |
| Claims | "No claims yet." |
| Actions | "No actions recorded." |
| Clarifications | "No clarification requests." |
| Evidence | "No evidence attached." |
| Reviews | "No reviews performed." |
| Audit | "No audit events." |
