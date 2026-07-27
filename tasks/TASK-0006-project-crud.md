# TASK-0006 Project Model + CRUD API

Spec: SPEC-0006
Status: done
Priority: 10
Model: routine
Milestone: M1

## Goal

Implement Project entity with full CRUD API.

## Non-goals

- No RBAC.
- No audit integration yet.

## Files likely involved

```text
backend/app/projects/__init__.py
backend/app/projects/models.py
backend/app/projects/schemas.py
backend/app/projects/service.py
backend/app/api/__init__.py
backend/app/api/v1/__init__.py
backend/app/api/v1/projects.py
backend/app/main.py
backend/tests/test_project_crud.py
backend/alembic/versions/0003_add_project.py
```

## TDD Steps

1. Create failing tests for all CRUD endpoints.
2. Run tests, confirm failure.
3. Implement model, schemas, service, router.
4. Register router in main.py.
5. Generate migration.
6. Run tests, confirm pass.
7. Run coverage, lint, typecheck.

## Acceptance Criteria

- POST /api/v1/projects creates project.
- GET /api/v1/projects/{id} returns project.
- PATCH /api/v1/projects/{id} updates fields.
- DELETE /api/v1/projects/{id} removes project.
- GET /api/v1/projects returns paginated list.
- Slug uniqueness enforced.
- 404 on missing project.
- Coverage >= 80%.

## DoD

- tests added;
- implementation added;
- migration generated;
- coverage >= 80%;
- commands pass;
- statuses updated.
