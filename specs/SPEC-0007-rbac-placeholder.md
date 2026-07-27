# SPEC-0007 RBAC Placeholder

Status: approved
Owner: project-owner
Milestone: M1
Related tasks: TASK-0008

## Problem

No user or permission model exists. Every future module needs actor identity.

## Goal

Provide placeholder models for User, Role, Permission and a `current_user` dependency.

## Non-goals

- No real auth (JWT, sessions).
- No permission enforcement.
- No user registration/login.

## Requirements

1. User model: id, username, email, is_active, created_at.
2. Role model: id, name.
3. Permission model: id, name.
4. user_role and role_permission association tables.
5. `current_user` dependency returns a placeholder user.
6. Migration generated.

## Acceptance Criteria

- Models exist and migration runs.
- `current_user` dependency works.
- Tests verify models and dependency.
- Coverage >= 80%.

## DoD

- Spec approved.
- Task implemented with TDD.
- All commands pass.
- Statuses updated.
