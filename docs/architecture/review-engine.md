# Review Engine — UPCP v2

## Overview

The Review Engine manages the process of verifying completed tasks. It supports three review policies, automatic closure, and human override.

---

## Review Policies

### `human_only`

Only humans conduct reviews. An agent can neither conduct a review nor automatically close a task.

```
Agent completes a task
  → submit_task_for_review
    → ReviewRound(pending, reviewer_type=human)
      → Owner opens UI, conducts review
        → submit_review_verdict(approved/rejected)
```

**Use case:** Critical tasks, security-sensitive changes.

### `agent_review_then_human`

An agent reviewer conducts the initial review. A mandatory human confirmation follows.

```
Agent completes a task
  → submit_task_for_review
    → ReviewRound(pending, reviewer_type=agent)
      → Agent reviewer checks, delivers verdict
        → If approved:
          → ReviewRound(completed, verdict=approved)
            → New ReviewRound(pending, reviewer_type=human) created
              → Owner confirms / rejects
        → If rejected:
          → Task → changes_requested
```

**Use case:** Standard tasks where initial agent review speeds up the process.

### `agent_auto_close_if_allowed`

An agent reviewer can automatically close a task without human review (when conditions are met).

```
Agent completes a task
  → submit_task_for_review
    → ReviewRound(pending, reviewer_type=agent)
      → Agent reviewer checks
        → If approved AND task is low/medium priority:
          → Task → done (automatically)
        → If approved AND task is high/critical priority:
          → Human review round created (as in agent_review_then_human)
        → If rejected:
          → Task → changes_requested
```

**Use case:** Routine tasks, low-risk changes.

---

## ReviewRound and ReviewFinding Models

### ReviewRound

```
ReviewRound(
    id: UUID,
    task_id: UUID FK → Task,
    round_number: INT,          # Sequential number (1, 2, 3...)
    policy: VARCHAR(32),        # Applied policy
    status: VARCHAR(16),        # pending → in_progress → completed | cancelled
    verdict: VARCHAR(16),       # approved | rejected (null until completed)
    reviewer_type: VARCHAR(16), # human | agent
    reviewer_id: UUID,          # User ID or Agent ID
    summary: TEXT,              # Final review summary
    started_at: TIMESTAMPTZ,
    completed_at: TIMESTAMPTZ,
    created_at: TIMESTAMPTZ
)
```

### ReviewFinding

```
ReviewFinding(
    id: UUID,
    review_round_id: UUID FK → ReviewRound,
    severity: VARCHAR(16),      # critical | major | minor | nit
    category: VARCHAR(32),      # correctness | security | performance | style | missing
    description: TEXT,
    file_path: TEXT,            # File path (optional)
    line_number: INT,           # Line number (optional)
    status: VARCHAR(16),        # open | addressed | dismissed
    created_at: TIMESTAMPTZ
)
```

### Severity Semantics

> **NOTE**: These match the actual implementation in `quality/schemas.py`.

| Severity | Description | Impact on Verdict |
|----------|-------------|-------------------|
| `nit` | Minor style/naming suggestion | No impact |
| `minor` | Small improvement, non-blocking | Non-blocking |
| `major` | Significant issue, should fix | Blocking if unresolved |
| `critical` | Blocking finding | Automatically → `rejected` |

### Category Taxonomy

| Category | Description |
|----------|-------------|
| `correctness` | Logical errors, edge cases |
| `security` | Vulnerabilities, OWASP |
| `performance` | N+1, inefficient algorithms |
| `style` | Code style, naming, formatting |
| `missing` | Missing tests, documentation, error handling |

---

## Agent Reviewer Constraints

### Constraints

1. **Scope**: An agent reviewer can only review tasks in assigned projects
2. **Self-review prohibited**: An agent cannot review its own tasks
3. **Capabilities**: The agent must have the `review.submit` capability
4. **Finding format**: The agent reviewer MUST attach findings with categories
5. **Summary required**: A brief text summary is mandatory

### Automatic Checks by Agent Reviewer

Before delivering a verdict, the agent reviewer must check:

1. **Evidence**: Is there evidence covering the acceptance criteria?
2. **Tests**: Is there test output? Do tests pass?
3. **Code quality**: Are there obvious anti-patterns?
4. **Security**: Are there obvious vulnerabilities?
5. **Completeness**: Are all acceptance criteria met?

### Finding Requirements

The agent reviewer must:

- Set severity for each finding
- Set category
- Describe the finding in text
- Provide `file_path` and `line_number` if relevant
- Critical findings MUST result in `rejected`

---

## Auto-Close Conditions

### Conditions for auto-close (policy `agent_auto_close_if_allowed`)

All conditions must be true simultaneously:

```python
def can_auto_close(task, review_round, findings):
    return (
        task.priority in ("low", "medium")              # 1. Low/medium priority
        and review_round.reviewer_type == "agent"        # 2. Review by agent
        and not any(                                     # 3. No critical findings
            f.severity == "critical"
            for f in findings
        )
        and task.evidence.count >= 1                     # 4. At least one evidence item
        and task.acceptance_criteria.all_met             # 5. All AC met
    )
```

### Auto-Close Process

```
1. Agent reviewer calls submit_review_verdict(approved)
2. System checks can_auto_close()
3. If YES:
   - ReviewRound → completed, verdict=approved
   - Task → done
   - AuditEvent: review.auto_closed
   - Notification → owner: "Task auto-approved by agent"
4. If NO (high/critical priority):
   - ReviewRound → completed, verdict=approved
   - New ReviewRound(pending, reviewer_type=human) created
   - Notification → owner: "Task needs your review"
```

---

## Human Override

### Rules

1. **Owner can at any time**:
   - Cancel the current review round → `cancelled`
   - Manually create a new review round
   - Override the agent's verdict (approve → reject or vice versa)
   - Skip review and immediately set `done` (force close)

2. **Force Close**:
   ```
   Owner calls force_close_task(task_id, reason)
   → Cancels all active review rounds
   → Task → done
   → AuditEvent: task.force_closed
   ```

3. **Override Agent Verdict**:
   ```
   Owner calls override_review(review_round_id, new_verdict, reason)
   → ReviewRound.verdict = new_verdict
   → AuditEvent: review.verdict_overridden
   → If new_verdict=approved → Task → done
   → If new_verdict=rejected → Task → changes_requested
   ```

---

## Review Round Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│                    Review Round Lifecycle                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Task: in_progress                                          │
│    │                                                        │
│    │ submit_task_for_review(summary, evidence[])            │
│    ▼                                                        │
│  Task: ready_for_review                                     │
│  ReviewRound #1: pending                                    │
│    │                                                        │
│    │ start_review()                                         │
│    ▼                                                        │
│  ReviewRound #1: in_progress                                │
│    │                                                        │
│    │ Adding findings...                                     │
│    │                                                        │
│    │ submit_review_verdict(approved|rejected, findings[])   │
│    ▼                                                        │
│  ReviewRound #1: completed                                  │
│    │                                                        │
│    ├── If approved (and can_auto_close)                     │
│    │   → Task: done                                         │
│    │                                                        │
│    ├── If approved (and !can_auto_close)                    │
│    │   → ReviewRound #2: pending (reviewer_type=human)      │
│    │                                                        │
│    └── If rejected                                          │
│        → Task: changes_requested                            │
│          → Agent performs rework                            │
│            → submit_task_for_review(summary)                │
│              → ReviewRound #2: pending                      │
│                → ...                                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Evidence Integration

### Requirements

1. For `submit_task_for_review`, attaching evidence is recommended but not required
2. The agent reviewer checks evidence as part of the review
3. For auto-close, evidence is mandatory (at least 1)
4. Evidence types supported by the review engine:
   - `test_output` — test output (pytest, jest, etc.)
   - `command_output` — command output (build, lint)
   - `screenshot` — result screenshot
   - `file_diff` — change diff
   - `url` — link to result (preview URL, PR)
   - `log` — execution log

### Evidence Validation

```python
def validate_evidence_for_review(task, evidence_list):
    """Checks that evidence is sufficient for review."""
    issues = []

    has_test_output = any(e.evidence_type == "test_output" for e in evidence_list)
    has_command_output = any(e.evidence_type == "command_output" for e in evidence_list)

    if not has_test_output and not has_command_output:
        issues.append("No test or build output provided")

    # Check that acceptance criteria are covered
    ac_count = task.acceptance_criteria.count()
    if ac_count > 0 and len(evidence_list) == 0:
        issues.append("Task has acceptance criteria but no evidence")

    return issues
```

---

## Configuration

### Per-Project Settings

```json
{
    "review_policy": "agent_review_then_human",
    "allow_agent_auto_close": false,
    "require_evidence_for_review": true,
    "auto_close_max_priority": "medium",
    "review_timeout_days": 3,
    "max_review_rounds": 5
}
```

### Per-Task Override

A task can override the project policy:

```json
{
    "review_policy": "human_only"  // Override at the task level
}
```
