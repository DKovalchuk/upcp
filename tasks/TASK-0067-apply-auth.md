# TASK-0067 Apply Auth to All Endpoints

Spec: SPEC-0014
Status: done
Priority: 10
Model: routine
Milestone: M7

## Goal

Protect all existing API endpoints with auth middleware.

## Approach

FastAPI middleware that checks JWT on all `/api/v1/` routes except public ones.
No changes to existing endpoint code.

## Public routes (no auth required):
- GET /health
- GET /api/v1/health
- POST /auth/setup
- POST /auth/login
- POST /auth/refresh
- GET /docs, /openapi.json

## Acceptance Criteria

- [ ] Middleware protects all /api/v1/ routes.
- [ ] Public routes exempt.
- [ ] 401 returned for missing/invalid token.
- [ ] Existing tests still pass (with auth bypass in test setup).
- [ ] Commands pass.

## DoD

- tests added and passing;
- implementation complete;
- commands pass;
- status updated.
