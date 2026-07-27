# TASK-0069 Seed Default Roles

Spec: SPEC-0014
Status: done
Priority: 10
Model: routine
Milestone: M7

## Goal

Seed default roles and permissions on first setup.

## Default Roles

| Role | Scope | Permissions |
|------|-------|-------------|
| Owner | global | Full access (all actions on all resources) |
| Admin | global | manage, create, read, update, delete (except user management) |
| Member | org | create, read, update (tasks, features, components) |
| Viewer | org | read only |

## Acceptance Criteria

- [ ] seed_roles() function creates default roles.
- [ ] Default permissions created.
- [ ] RolePermission links created.
- [ ] Idempotent (safe to run multiple times).
- [ ] Tests cover seeding.
- [ ] Commands pass.

## DoD

- tests added and passing;
- implementation complete;
- commands pass;
- status updated.
