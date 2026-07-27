# Evidence & Review — Specification

> Related: [UPCP v2 PRD](./upcp-v2.md) §3.3-3.4 | Milestone: M10

## 1. Overview

Evidence & Review ensures verifiability of results. Every task must pass quality gates and review before being considered complete.

## 2. Evidence

### 2.1 Types

| Type | MIME | Description |
|------|------|-------------|
| `test_result` | `application/json`, `text/plain` | Test output (JUnit XML, pytest output) |
| `log` | `text/plain` | Execution log (build, deploy, migration) |
| `screenshot` | `image/png`, `image/jpeg` | Screenshot of the result |
| `diff` | `text/plain` | Git diff of changes |
| `metric` | `application/json` | Metrics (coverage %, latency, bundle size) |
| `custom` | `*/*` | Arbitrary evidence |

### 2.2 Data Model

```python
class Evidence:
    id: str                    # UUID
    task_id: str               # FK → tasks
    step_id: str | None        # FK → dod_steps (nullable)
    type: EvidenceType         # enum
    title: str                 # brief description
    content: str | None        # inline content (up to 64KB)
    file_path: str | None      # file path (for binaries)
    hash: str                  # SHA-256 of content
    submitted_by: str          # agent_id or user_id
    submitted_at: datetime
    status: EvidenceStatus     # pending | accepted | rejected
```

### 2.3 Evidence statuses

| Status | Description |
|--------|-------------|
| `pending` | Uploaded, awaiting review |
| `accepted` | Reviewer accepted |
| `rejected` | Reviewer rejected (with reason) |

### 2.4 API

```
POST   /api/v1/tasks/{task_id}/evidence          # upload
GET    /api/v1/tasks/{task_id}/evidence            # list
GET    /api/v1/evidence/{id}                       # details
PATCH  /api/v1/evidence/{id}/accept                # accept
PATCH  /api/v1/evidence/{id}/reject                # reject
DELETE /api/v1/evidence/{id}                       # delete (admin+)
```

## 3. Definition of Done (DoD)

### 3.1 DoD Template

A project defines a DoD template — a set of steps that must be completed for every task.

```python
class DodTemplate:
    id: str
    project_id: str
    name: str
    steps: list[DodStep]

class DodStep:
    id: str
    order: int
    title: str                     # "Run unit tests"
    description: str               # "All tests pass with >80% coverage"
    evidence_type: EvidenceType    # expected evidence type
    required: bool                 # mandatory for completion
    auto_check: str | None         # auto-check command
```

### 3.2 DoD Example

```yaml
name: "Standard DoD"
steps:
  - title: "Unit tests pass"
    evidence_type: test_result
    required: true
    auto_check: "pytest --tb=short"
  - title: "Code coverage ≥ 80%"
    evidence_type: metric
    required: true
  - title: "Lint clean"
    evidence_type: log
    required: true
    auto_check: "ruff check ."
  - title: "Type check passes"
    evidence_type: log
    required: false
    auto_check: "mypy src/"
```

### 3.3 Evidence Completeness

```
completeness = required_steps_with_accepted_evidence / total_required_steps * 100
```

- A task may be submitted for review when completeness ≥ 100% for required steps
- Optional steps do not block review but affect the score

## 4. Quality Gates

### 4.1 Automated gates

Quality gates run automatically on `submit-review`:

| Gate | Command | Blocker |
|------|---------|---------|
| `lint` | `ruff check .` | yes |
| `test` | `pytest` | yes |
| `typecheck` | `mypy src/` | no |
| `build` | `docker build .` | no |

### 4.2 Behavior

1. Agent calls `POST /tasks/{id}/submit-review`
2. System runs quality gates from the playbook
3. If a blocker gate fails → task returns to `in_progress` with `changes_requested`
4. If all gates pass → task transitions to `in_review`
5. Gate results are saved as evidence

### 4.3 Custom gates

```yaml
quality_gates:
  - name: bundle_size
    command: "npm run build && du -sh dist/"
    threshold: "500K"
    blocker: false
```

## 5. Review

### 5.1 Review Rounds

```python
class ReviewRound:
    id: str
    task_id: str
    round_number: int         # 1, 2, 3...
    reviewer_type: Literal["agent", "human"]
    reviewer_id: str
    status: Literal["in_progress", "approved", "changes_requested"]
    started_at: datetime
    completed_at: datetime | None
    summary: str | None
```

### 5.2 Workflow

1. Task enters `in_review` → system assigns a reviewer
2. Reviewer checks evidence, code, result
3. Reviewer creates findings (remarks)
4. Reviewer decides: `approve` or `request_changes`
5. On `request_changes` → agent works on findings → new round
6. On `approve` → task → `done`

### 5.3 Findings

```python
class Finding:
    id: str
    review_round_id: str
    severity: Literal["info", "suggestion", "minor", "major", "critical"]
    file_path: str | None     # link to file
    line: int | None          # link to line
    description: str
    status: Literal["open", "addressed", "dismissed"]
    resolution: str | None
```

### 5.4 API

```
POST /api/v1/tasks/{task_id}/submit-review
POST /api/v1/tasks/{task_id}/review/{round_id}/approve
POST /api/v1/tasks/{task_id}/review/{round_id}/request-changes
POST /api/v1/tasks/{task_id}/review/{round_id}/findings
PATCH /api/v1/review/findings/{finding_id}/resolve
GET  /api/v1/tasks/{task_id}/reviews
```

## 6. Agent Review

An agent reviewer works similarly to a human:

1. Receives notification of a new task in `in_review`
2. Reads evidence, checks code (MCP tool: `review_task`)
3. Creates findings
4. Delivers verdict: `approve` or `request_changes`

### Agent review constraints
- An agent cannot review its own task
- Agent review is advisory for critical tasks (final approval by human)
- Maximum 3 rounds of agent review, then escalate to human

## 7. Human Approval

### 7.1 Requirements
- Tasks with severity `critical` require human approval
- Tasks involving auth/security/DB schema require human approval
- A project can configure `require_human_review: true` for all tasks

### 7.2 Escalation
- After 3 rounds without resolution → notification to admin
- After 5 rounds → task automatically enters `blocked` with escalation

## 8. Auto-Close Conditions

A task automatically transitions to `done` when:

1. All required DoD steps are accepted (evidence completeness = 100%)
2. All quality gates passed
3. Review status = `approved`
4. No open findings with severity ≥ `major`

## 9. Metrics

| Metric | Formula |
|--------|---------|
| Review turnaround | `avg(completed_at - started_at)` across rounds |
| First-pass approval rate | `rounds[0].approved / total_tasks * 100` |
| Finding density | `total_findings / total_review_rounds` |
| Evidence completeness | `avg(completeness)` across tasks |
| Agent review accuracy | `agent_approved ∩ human_approved / agent_approved` |
