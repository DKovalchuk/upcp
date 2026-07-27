# SPEC-0015 Evidence & Review Engine

Status: draft
Owner: project-owner
Milestone: M10
Related tasks: TASK-0077 through TASK-0082

## Problem

Tasks can be marked done without evidence or review. No traceability for quality decisions.

## Goal

1. Evidence model with verification states (unverified → agent_verified → human_accepted / rejected).
2. ReviewRound and ReviewFinding models for structured review.
3. Evidence API: attach, list, verify, accept, reject.
4. Review API: create round, start, add findings, submit verdict.
5. Submit-for-review gate: blocks if evidence or DoD incomplete.
6. MCP tools: list_evidence, list_review_rounds, attach_evidence, submit_review_verdict.

## Requirements

### Evidence

- Evidence: id, task_id (FK), dod_item_id? (FK), type, title, description?, url?, content_snippet?, artifact_ref?, created_by_type, created_by_id, verification_state, verified_by_type?, verified_by_id?, verified_at?, created_at, updated_at.
- Evidence types: commit, test_output, screenshot, log, manual, other.
- Verification states: unverified → agent_verified → human_accepted / rejected / stale.
- Indexes: task_id, verification_state.

### ReviewRound

- ReviewRound: id, task_id (FK), requested_by_type, requested_by_id, reviewer_type?, reviewer_id?, state, verdict?, confidence?, summary?, created_at, started_at?, completed_at.
- States: pending → in_progress → completed / cancelled.
- Verdict: approve | reject | needs_changes.
- Indexes: task_id, state.

### ReviewFinding

- ReviewFinding: id, review_round_id (FK), severity, category, message, evidence_id? (FK), dod_item_id? (FK), suggestion?, created_at.
- Severity: critical | major | minor | nit.
- Category: correctness | completeness | security | performance | style | other.

### DoDItem update

- Add `required_evidence_type` column (nullable string). When set, task cannot submit for review unless at least one evidence of that type is attached.

### Submit for review gate

- POST /tasks/{id}/submit-review checks:
  - All DoDItems passed OR no DoDItems exist.
  - If any DoDItem has required_evidence_type, at least one evidence of that type exists.
  - No blocking clarification requests open.
  - Task is in claimable/in_progress state.

### Evidence Verification

- Agent can verify own evidence: unverified → agent_verified.
- Human can accept: any → human_accepted.
- Human can reject with reason: any → rejected.

## Acceptance Criteria

- Evidence CRUD with verification state machine.
- ReviewRound + ReviewFinding CRUD with state machine.
- Submit-for-review gate blocks when criteria not met.
- All API endpoints return correct status codes and errors.
- MCP tools for evidence and review.
- TDD: failing tests before implementation.
- Tests pass, lint passes.

## DoD

- Spec approved.
- Models, migrations, services, API, MCP tools implemented.
- All tests pass.
- PROJECT_STATUS.md updated.
