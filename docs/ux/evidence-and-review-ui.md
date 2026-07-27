# Evidence and Review UI

Спецификация интерфейса для evidence и review workflow.

---

## 1. Evidence Panel

### 1.1 Location

Вкладка **Evidence** в Task Detail.

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

**Элементы:** Type badge, Author, Timestamp, Content preview (5 строк, expandable), URL link, Verified status, Actions.

### 1.3 Attach Evidence

Кнопка [+] → Dialog:

- **Type:** select (test_output, screenshot, log, url, file)
- **Content:** textarea
- **URL:** input (для url-типа)

### 1.4 Verify / Reject

- **Verify:** Статус → `verified`.
- **Reject:** Требует reason. Статус → `rejected`.

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

Вкладка **Reviews** в Task Detail.

### 2.2 Review Round

Collapsible секция:

```
▼ Round 1 · gpt-4-reviewer · needs_changes · 2 findings · 30m ago
```

**Verdict badge colors:**
| Verdict | Цвет |
|---------|------|
| `approve` | Зелёный |
| `needs_changes` | Жёлтый |
| `reject` | Красный |

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

Для agent verdicts:

```
Agent recommends: needs_changes
[Confirm & Approve] [Request Changes] [Reject]
```

### 2.6 Auto-round

При `needs_changes` и повторной отправке → автоматически новый раунд.

---

## 3. Quality Gate Display

### 3.1 Location

Вкладка **DoD** в Task Detail + Quality page.

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

| Состояние | Условие | Цвет |
|-----------|---------|------|
| PASSED | Все `passed` | Зелёный |
| NOT PASSED | Есть `pending`/`failed` | Красный |
| IN PROGRESS | Часть выполнена | Серый |

### 3.4 Submit Button

Доступна когда: gate PASSED + нет blocking clarifications + хотя бы один evidence. Disabled → tooltip с причиной.

---

## 4. Empty States

| Панель | Message |
|--------|---------|
| Evidence | "No evidence attached. [Attach Evidence]" |
| Reviews | "No reviews yet. Submit task for review to start." |
| Quality Gate | "No DoD items defined. [Add Item]" |
| Findings | "No findings in this round." |
