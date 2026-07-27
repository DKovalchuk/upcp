# Review Agent Guide

Guide for reviewer agents: how to conduct reviews, create findings, and deliver verdicts.

---

## 1. Overview

A reviewer agent inspects completed tasks and provides a recommendation: approve, reject, or needs_changes. By default, the agent's verdict is a recommendation; the final decision rests with the human.

**Role:** `reviewer`
**Scope:** `review:read`, `review:write`, `evidence:read`, `delivery:read`, `quality:read`, `git:read`

---

## 2. Review Process

### 2.1 Receiving a Task for Review

A task is submitted for review via `submit_task_for_review`. Check the inbox:

```
tools/call → get_agent_inbox
  status: "open"
```

Or request the task directly:

```
tools/call → task_get
  task_id: "<uuid>"
```

### 2.2 Gathering Information

For the review, read the following:

1. **Task** — title, description, status
2. **Acceptance Criteria** — what must be delivered
3. **DoD Items** — readiness criteria
4. **Evidence** — proof of completion
5. **Git Links** — related commits, branches, PR/MR
6. **Clarifications** — questions and answers during work
7. **Context Snapshot** — the context the performing agent saw

```
tools/call → task_get             → task + AC + DoD + subtasks
tools/call → list_evidence        → agent evidence
tools/call → list_review_rounds   → previous rounds (if any)
```

### 2.3 Analysis

Check the following:

| Criterion       | What to Check                                |
|-----------------|----------------------------------------------|
| **Correctness** | Does the code solve the task? Does it meet the AC? |
| **Completeness**| Are all AC covered? Are all DoD items passed? |
| **Code Quality**| Readability, structure, errors               |
| **Security**    | Any vulnerabilities (OWASP Top 10)?          |
| **Performance** | Any N+1 queries, inefficient algorithms?     |
| **Tests**       | Are edge cases covered? Any mocks in prod code? |
| **Evidence**    | Is the evidence sufficient? Is it legitimate?|

### 2.4 Creating Findings

Each finding is a separate entry:

```
tools/call → create_review_finding
  review_round_id: "rr_001"
  severity: "medium"
  category: "code_quality"
  description: "Missing error handling in UserService.create() — uncaught IntegrityError will return 500"
  file_path: "backend/app/users/service.py"
  line_range: "42-58"
  suggestion: "Wrap db.add() in try/except IntegrityError, raise Conflict()"
```

**Severity levels:**

| Level      | Description                              | Blocks approve? |
|------------|------------------------------------------|-----------------|
| `info`     | Style, formatting                        | No              |
| `low`      | Minor improvements                       | No              |
| `medium`   | Noticeable issues                        | No (needs_changes) |
| `high`     | Serious issues                           | Yes (reject)    |
| `critical` | Vulnerabilities, data loss               | Yes (reject)    |

**Categories:**

| Category        | Description                                  |
|-----------------|----------------------------------------------|
| `code_quality`  | Readability, structure, DRY, naming          |
| `security`      | Vulnerabilities, injection, auth bypass      |
| `performance`   | N+1, memory leaks, inefficient queries       |
| `correctness`   | Logic errors, incorrect handling             |

### 2.5 Verdict

```
tools/call → submit_review_verdict
  review_round_id: "rr_001"
  verdict: "needs_changes"
  summary: "Two medium findings: missing error handling and unused import. Fix before approve."
```

---

## 3. Verdicts

### approve

Task is completed with quality. All AC and DoD satisfied. No medium+ findings.

**When:**
- No findings with severity ≥ medium
- All AC covered
- Evidence sufficient
- Code passes all checks

### needs_changes

Task is completed but has remarks.

**When:**
- Findings with medium severity exist
- Minor issues that don't affect functionality
- Missing tests for edge cases

**Next steps:** The performing agent receives the findings, fixes them, and resubmits.

### reject

Task is not completed or completed with poor quality.

**When:**
- Findings with high/critical severity exist
- Code does not solve the task
- Critical vulnerabilities
- Evidence is fabricated or unreliable

**Next steps:** Task is returned to `backlog` or `ready`.

---

## 4. Review Constraints

### Self-review is forbidden

An agent cannot review a task they performed themselves. The system checks `claim_history` and rejects such attempts.

```
Error: SELF_REVIEW_FORBIDDEN — agent agt_x performed task task_y
```

### Auto-close conditions

Auto-closing (approve without human confirmation) is possible ONLY when:

1. The project has explicitly enabled the `allow_agent_auto_close` flag.
2. All findings have severity ≤ `low`.
3. Verdict is `approve`.
4. Agent has the `reviewer` role with scope `review:auto_close`.

In all other cases, the verdict is a recommendation for the human.

### Round limits

- Maximum 5 review rounds per task.
- After 5 rounds, the task is escalated for manual review.

---

## 5. Multiple Findings

A single review round can contain multiple findings. Group related findings:

```
# Finding 1: Missing error handling
severity: high, category: correctness

# Finding 2: No test for error path
severity: medium, category: code_quality

# Finding 3: SQL injection risk in search
severity: critical, category: security
```

The verdict is determined by the most severe finding:
- `critical` → `reject`
- `high` → `reject`
- `medium` → `needs_changes`
- `low`/`info` → `approve` (with remarks)

---

## 6. Best Practices

1. **Read the context pack before reviewing** — understand the project context.
2. **Check git links** — code review via diff, not just description.
3. **Be specific** — provide file_path and line_range.
4. **Propose solutions** — don't just find problems, suggest fixes.
5. **Don't block on style** — use `info` for formatting issues.
6. **Verify evidence** — test_output can be fabricated; cross-check with git.
7. **Log your reasoning** — explain in the summary why you chose that verdict.
8. **Don't review too quickly** — give findings proper attention, don't rubber-stamp.
