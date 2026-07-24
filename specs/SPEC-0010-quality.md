# SPEC-0010 Quality: Acceptance Criteria, DoD, Quality Gate

Status: approved
Owner: project-owner
Milestone: M2
Related tasks: TASK-0011, TASK-0012

## Problem

No quality control exists. Tasks can be marked done without verification.

## Goal

1. AcceptanceCriterion and DoDItem models (TASK-0011).
2. Quality gate: task done only if all DoD items pass (TASK-0012).

## Requirements

1. AcceptanceCriterion: id, task_id (FK), description, status (pending/passed/failed).
2. DoDItem: id, task_id (FK), name, status (pending/passed/failed).
3. CRUD for both.
4. Quality gate: TaskService.done() checks all DoDItem passed.
5. If any DoDItem is not passed, raise error.

## Acceptance Criteria

- CRUD for acceptance criteria and DoD items.
- Quality gate blocks task completion.
- Tests for all scenarios.
- Coverage >= 80%.

## DoD

- Spec approved.
- Task implemented with TDD.
- All commands pass.
- Statuses updated.
