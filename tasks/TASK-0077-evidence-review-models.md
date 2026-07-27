# TASK-0077 Evidence + Review Models & Migration

Status: pending
Milestone: M10
Spec: SPEC-0015
Depends: TASK-0076

## Goal

Add Evidence, ReviewRound, ReviewFinding models and migration 0015.

## Acceptance Criteria

- Evidence model with all fields per SPEC-0015.
- ReviewRound model with state machine fields.
- ReviewFinding model with severity/category.
- DoDItem gets required_evidence_type column.
- Migration 0015_create_evidence_review.py.
- Unit tests for model creation and constraints.
