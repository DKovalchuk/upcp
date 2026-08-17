# TASK-0106 — M17 Sprint 3: Database Hardening

**Spec:** SPEC-0020
**Milestone:** M17
**Sprint:** S19.3
**Status:** DONE
**Size:** M (5 points)

## Objective

Add missing database indexes, fix ForeignKey ondelete behavior, and resolve N+1 query in agent detail endpoint.

## Context

M16 audit found 17+ missing indexes on frequently queried FK columns, 27 ForeignKey columns without `ondelete` clauses, and an N+1 query in the agent detail endpoint. These cause full table scans at scale and prevent parent record deletion.

---

## Task 1: Create Migration 0020 — Indexes

**File:** `backend/alembic/versions/0020_add_indexes.py`

### Indexes to Add

```sql
-- Delivery context
CREATE INDEX IF NOT EXISTS ix_task_feature_id ON task(feature_id);
CREATE INDEX IF NOT EXISTS ix_task_status ON task(status);
CREATE INDEX IF NOT EXISTS ix_feature_project_id ON feature(project_id);

-- Structure context
CREATE INDEX IF NOT EXISTS ix_component_project_id ON component(project_id);
CREATE INDEX IF NOT EXISTS ix_module_component_id ON module(component_id);

-- Projects context
CREATE INDEX IF NOT EXISTS ix_project_status ON project(status);

-- Reporting context
CREATE INDEX IF NOT EXISTS ix_report_project_id ON report(project_id);

-- Delivery workflow
CREATE INDEX IF NOT EXISTS ix_task_claim_agent_id ON task_claim(agent_id);

-- Audit context
CREATE INDEX IF NOT EXISTS ix_audit_event_entity_id ON audit_event(entity_id);
CREATE INDEX IF NOT EXISTS ix_audit_event_event_type ON audit_event(event_type);
CREATE INDEX IF NOT EXISTS ix_audit_event_entity_type ON audit_event(entity_type);
CREATE INDEX IF NOT EXISTS ix_audit_event_timestamp ON audit_event(timestamp);

-- Gitread context
CREATE INDEX IF NOT EXISTS ix_git_provider_project_id ON git_provider(project_id);
CREATE INDEX IF NOT EXISTS ix_git_branch_provider_id ON git_branch(provider_id);
CREATE INDEX IF NOT EXISTS ix_git_commit_provider_id ON git_commit(provider_id);
CREATE INDEX IF NOT EXISTS ix_git_pull_request_provider_id ON git_pull_request(provider_id);
CREATE INDEX IF NOT EXISTS ix_git_link_entity ON git_link(entity_type, entity_id);
```

### Acceptance Criteria

- [ ] Migration 0020 creates all indexes
- [ ] Migration is reversible (downgrade drops indexes)
- [ ] Migration runs cleanly on existing data
- [ ] No duplicate index errors on re-run

---

## Task 2: Fix ForeignKey ondelete Behavior

**File:** All model files with ForeignKey definitions

### ondelete Rules

| Pattern | ondelete | Example |
|---------|----------|---------|
| Child table (owns lifecycle) | `CASCADE` | `subtask.task_id` → delete subtasks when task deleted |
| Required reference | `CASCADE` | `task.feature_id` → delete tasks when feature deleted |
| Optional reference | `SET NULL` | `task.component_id` → nullify when component deleted |
| Audit/log reference | `SET NULL` | `audit_event.entity_id` → keep audit even if entity deleted |

### Specific Changes

| File | ForeignKey | Current | New |
|------|-----------|---------|-----|
| `delivery/models.py` | `Task.feature_id` | none | `CASCADE` |
| `delivery/models.py` | `Task.component_id` | none | `SET NULL` |
| `delivery/models.py` | `Task.module_id` | none | `SET NULL` |
| `delivery/models.py` | `Subtask.task_id` | none | `CASCADE` |
| `delivery/models.py` | `ClarificationRequest.task_id` | none | `CASCADE` |
| `delivery/models.py` | `TaskDependency.task_id` | none | `CASCADE` |
| `delivery/models.py` | `TaskDependency.blocked_by_task_id` | none | `CASCADE` |
| `delivery/models.py` | `TaskClaim.task_id` | none | `CASCADE` |
| `delivery/models.py` | `Heartbeat.claim_id` | none | `CASCADE` |
| `delivery/models.py` | `Feature.project_id` | none | `CASCADE` |
| `delivery/models.py` | `Feature.component_id` | none | `SET NULL` |
| `structure/models.py` | `Component.project_id` | none | `CASCADE` |
| `structure/models.py` | `Module.component_id` | none | `CASCADE` |
| `quality/models.py` | `AcceptanceCriterion.task_id` | none | `CASCADE` |
| `quality/models.py` | `DoDItem.task_id` | none | `CASCADE` |
| `quality/models.py` | `Evidence.task_id` | none | `CASCADE` |
| `quality/models.py` | `Evidence.dod_item_id` | none | `SET NULL` |
| `quality/models.py` | `ReviewRound.task_id` | none | `CASCADE` |
| `quality/models.py` | `ReviewFinding.review_round_id` | none | `CASCADE` |
| `quality/models.py` | `ReviewFinding.evidence_id` | none | `SET NULL` |
| `quality/models.py` | `ReviewFinding.dod_item_id` | none | `SET NULL` |
| `reporting/models.py` | `Report.project_id` | none | `CASCADE` |
| `gitread/models.py` | `GitProvider.project_id` | none | `CASCADE` |
| `gitread/models.py` | `GitBranch.provider_id` | none | `CASCADE` |
| `gitread/models.py` | `GitCommit.provider_id` | none | `CASCADE` |
| `gitread/models.py` | `GitPullRequest.provider_id` | none | `CASCADE` |
| `gitread/models.py` | `GitLink.*` | none | `CASCADE` |

### Implementation

For each model file, add `ondelete` to the `ForeignKey` string:
```python
# Before
feature_id: Mapped[str] = mapped_column(String(36), ForeignKey("feature.id"), nullable=False)

# After
feature_id: Mapped[str] = mapped_column(String(36), ForeignKey("feature.id", ondelete="CASCADE"), nullable=False)
```

Alembic will generate `ALTER TABLE ... ADD CONSTRAINT ... ON DELETE CASCADE` in the migration.

### Acceptance Criteria

- [ ] All ForeignKeys have explicit `ondelete`
- [ ] Child tables use CASCADE
- [ ] Optional refs use SET NULL
- [ ] Migration 0020 includes ondelete changes
- [ ] Deleting a project cascades to features, tasks, subtasks, etc.

---

## Task 3: Fix N+1 in Agent Detail Endpoint

**File:** `backend/app/identity/agent_endpoints.py:157`

### Problem

```python
for c in claims:
    task = db.get(Task, c.task_id)  # N+1 query
```

Each claim triggers a separate query to look up the task title.

### Fix

Use a single IN clause:
```python
task_ids = [c.task_id for c in claims]
tasks = db.query(Task).filter(Task.id.in_(task_ids)).all()
task_map = {t.id: t for t in tasks}

for c in claims:
    task = task_map.get(c.task_id)
```

### Acceptance Criteria

- [ ] Agent claims endpoint uses batch query (not N+1)
- [ ] Response format unchanged
- [ ] Test verifies query count

### Acceptance Tests

```python
def test_agent_claims_no_n_plus_one():
    """Agent claims endpoint uses batch queries."""
    # Given: agent with 10 claims
    # When: GET /agents/{id}/claims
    # Then: response is 200, SQL query count <= 3 (claims + tasks + heartbeats)
```

---

## Files to Modify

| File | Action | Task |
|------|--------|------|
| `backend/alembic/versions/0020_add_indexes_ondelete.py` | CREATE | #1, #2 |
| `backend/app/delivery/models.py` | MODIFY | #2 |
| `backend/app/structure/models.py` | MODIFY | #2 |
| `backend/app/quality/models.py` | MODIFY | #2 |
| `backend/app/reporting/models.py` | MODIFY | #2 |
| `backend/app/gitread/models.py` | MODIFY | #2 |
| `backend/app/identity/agent_endpoints.py` | MODIFY | #3 |
| `backend/tests/test_agent_detail.py` | MODIFY | #3 |

## Dependencies

- Can run in parallel with TASK-0105 (security)
- Migration must be tested against existing data

## Definition of Done

- [ ] Migration 0020 created with all indexes + ondelete
- [ ] All model files updated with ondelete
- [ ] N+1 fix verified with query count test
- [ ] All 705+ existing backend tests pass
- [ ] Migration upgrades cleanly
- [ ] Migration downgrades cleanly
- [ ] mypy, ruff clean
