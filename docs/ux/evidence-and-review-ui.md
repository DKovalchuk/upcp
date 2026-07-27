# Evidence and Review UI

Interface specification for the evidence and review workflow.

---

## 1. Evidence Panel

### 1.1 Location

The **Evidence** tab in Task Detail.

### 1.2 Evidence Card

```
┌─────────────────────────────────────────────────────┐
│ test_output                                1h ago   │
│ by claude-opus-builder                              │
│                                                     │
│ pytest backend/tests/ -v                            │
│ 47 passed, 0 failed, 0 warnings in 3.2s            │
│                                                     │
│ Verified by human-reviewer                          │
│                                                     │
│ [Verify] [Reject]                           [🗑️]   │
└─────────────────────────────────────────────────────┘
```

**Elements:** Type badge, Author, Timestamp, Content preview (5 lines, expandable), URL link, Verified status, Actions.

### 1.3 Attach Evidence

[+] button → Dialog:

- **Type:** select (test_output, screenshot, log, url, file)
- **Content:** textarea
- **URL:** input (for url type)

### 1.4 Verify / Reject

- **Verify:** Status → `verified`.
- **Reject:** Requires a reason. Status → `rejected`.

### 1.5 States

```
pending → verified
pending → rejected
```

### 1.6 Filters

All | Pending | Verified | Rejected

---

## 2. Review Panel

### 2.1 Location

The **Reviews** tab in Task Detail.

### 2.2 Review Round

Collapsible section:

```
▼ Round 1 · gpt-4-reviewer · needs_changes · 2 findings · 30m ago
```

**Verdict badge colors:**
| Verdict | Color |
|---------|-------|
| `approve` | Green |
| `needs_changes` | Yellow |
| `reject` | Red |

### 2.3 Finding Card

```
┌─────────────────────────────────────────────────────┐
│ medium · code_quality                               │
│                                                     │
│ Missing error handling in UserService.create()      │
│ Uncaught IntegrityError will return 500 to client   │
│                                                     │
│ backend/app/users/service.py:42-58                  │
│                                                     │
│ Suggestion:                                         │
│ Wrap db.add() in try/except IntegrityError,         │
│ raise Conflict("User already exists")               │
└─────────────────────────────────────────────────────┘
```

**Severity:**
| Level | Badge |
|-------|-------|
| `info` | Blue |
| `low` | Green |
| `medium` | Yellow |
| `high` | Orange |
| `critical` | Red |

**Category:** `code_quality`, `security`, `performance`, `correctness`.

### 2.4 Verdict Section

```
Verdict: needs_changes
"Two medium findings. Fix before approve."
by gpt-4-reviewer · 30m ago
```

### 2.5 Human Confirmation

For agent verdicts:

```
Agent recommends: needs_changes
[Confirm & Approve] [Request Changes] [Reject]
```

### 2.6 Auto-round

On `needs_changes` and resubmission → a new round is created automatically.

---

## 3. Quality Gate Display

### 3.1 Location

The **DoD** tab in Task Detail + Quality page.

### 3.2 Gate UI

```
Quality Gate
████████████░░░░░░░░ 3/5 items passed

☑ Create model + migration    passed
☑ Write unit tests            passed
☑ Update API docs             passed
☐ Run linter                  pending
☐ Code review approved        pending

Gate: NOT PASSED

[Submit for Review] (disabled)
```

### 3.3 Gate States

| State | Condition | Color |
|-------|-----------|-------|
| PASSED | All `passed` | Green |
| NOT PASSED | Any `pending`/`failed` | Red |
| IN PROGRESS | Partially complete | Gray |

### 3.4 Submit Button

Available when: gate PASSED + no blocking clarifications + at least one evidence. Disabled → tooltip with the reason.

---

## 4. Empty States

| Panel | Message |
|-------|---------|
| Evidence | "No evidence attached. [Attach Evidence]" |
| Reviews | "No reviews yet. Submit task for review to start." |
| Quality Gate | "No DoD items defined. [Add Item]" |
| Findings | "No findings in this round." |
