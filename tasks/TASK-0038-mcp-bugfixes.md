# TASK-0038: MCP Critical Bug Fixes

Spec: SPEC-0011 (MCP)
Status: done
Priority: 1
Model: routine
Milestone: M5

## Goal

Fix critical bugs found during MCP QA audit. BUG-1 is a blocker — tools cannot function without fixing session architecture.

## Bugs to Fix

### BUG-1 (CRITICAL): Session bypass in `call_tool()`

**File**: `backend/app/mcp/tools.py:236`
**Problem**: `call_tool()` creates its own `SessionLocal()` session, bypassing FastAPI dependency injection. Each tool call creates a new DB connection instead of sharing the request session.
**Impact**: Tools fail in isolation, potential connection pool exhaustion.
**Fix**: Refactor `call_tool()` to accept a session parameter from the request context.

### BUG-2 (CRITICAL): Semantic mismatch in `task_list`

**File**: `backend/app/mcp/tools.py:174-185`
**Problem**: Tool accepts `project_id` parameter but internally maps it to `feature_id`. Users calling `task_list` with a project ID get wrong results.
**Fix**: Either accept `feature_id` directly or implement proper project-to-tasks mapping via a service method.

### BUG-3: Serialization crash in `_serialize_task()`

**File**: `backend/app/mcp/tools.py:127`
**Problem**: `int(str(t.priority))` crashes with `ValueError` when `priority` is `None`.
**Fix**: Handle None values gracefully: `int(str(t.priority)) if t.priority is not None else None`.

### BUG-4: Context pack session bypass

**File**: `backend/app/mcp/context_pack.py:14`
**Problem**: Same as BUG-1 — `ContextPackGenerator` creates its own `SessionLocal()`.
**Fix**: Accept session parameter in constructor.

### BUG-5: `_get_int_arg` silent failures

**File**: `backend/app/mcp/tools.py:82-90`
**Problem**: Boolean `true`/`false` silently becomes default value. Float values silently become default.
**Fix**: Proper type coercion: bool → 1/0, float → int(), validate input type.

### BUG-6: No input validation

**Problem**: No maximum limit enforcement, no negative offset/limit validation.
**Fix**: Add validation: max limit=100, min offset=0.

## TDD Steps

1. Write failing tests for each bug.
2. Fix BUG-1: Refactor session architecture.
3. Fix BUG-2: Fix task_list semantics.
4. Fix BUG-3: Handle None in serialization.
5. Fix BUG-4: Fix context pack session.
6. Fix BUG-5: Fix integer arg parsing.
7. Fix BUG-6: Add input validation.
8. Run all MCP tests.
9. Verify coverage increased.

## Acceptance Criteria

- `call_tool()` accepts session parameter from request context.
- `task_list` correctly maps project_id to tasks (not feature_id).
- `_serialize_task()` handles None priority without crash.
- `ContextPackGenerator` accepts session parameter.
- `_get_int_arg` properly coerces booleans and floats.
- Input validation: max limit=100, min offset=0.
- All 8 existing MCP tests pass.
- New tests added for each bug fix.
- Coverage for tools.py > 70%.
- `make test` passes.

## DoD

- all critical bugs fixed;
- regression tests added;
- coverage increased;
- build passes;
- task file status updated.
