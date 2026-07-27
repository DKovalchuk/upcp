# Agent Center UX

Управление ИИ-агентами: профили, токены, scope, назначения, активность.

---

## 1. Обзор

Agent Center — единая страница для управления всеми агентами.

**URL:** `/agents`

---

## 2. Agent List

### Table Columns

| Колонка | Описание |
|---------|----------|
| Name | Имя + type badge |
| Status | active / inactive / revoked |
| Role | reader / contributor / builder / reviewer |
| Active Tasks | Количество claimed задач |
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

Клик → Agent Detail.

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

| Колонка | Описание |
|---------|----------|
| Name | Имя токена |
| Prefix | Первые 12 символов + "..." |
| Scopes | Теги scope |
| Created | Дата |
| Last Used | Дата |
| Status | active / expired / revoked |

**Действия:** [Generate Token] (modal, показывает один раз), [Revoke] (ConfirmDialog).

#### 3.3 Scopes

Grid с чекбоксами:

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

| Колонка | Описание |
|---------|----------|
| Project | Название |
| Role | Роль |
| Assigned | Дата |
| Tasks | done / total |

**Действия:** [Assign to Project], [Remove Assignment].

#### 3.5 Claims

| Колонка | Описание |
|---------|----------|
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

Clarification requests от этого агента. Фильтры: open | answered | blocking | all.

#### 3.8 Evidence

Evidence, прикреплённые этим агентом. Фильтры: verified | unverified | rejected | all.

#### 3.9 Reviews

Review rounds, где агент — reviewer.

#### 3.10 Audit

Полный audit trail для агента.

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
