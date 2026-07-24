# TASK-0061: Global Search

**Status**: done
**Spec**: SPEC-0013 §6
**Phase**: Future
**Estimated effort**: 2-3 hours

---

## Problem

No way to search across projects, features, and tasks from the UI.

## Scope

1. Backend: `/api/v1/search?q=...` endpoint searching projects, features, tasks
2. Frontend: `searchGlobal()` API function
3. CommandPalette: debounced search with results group
4. Entity-specific icons and navigation

## Acceptance Criteria

- [x] Backend search endpoint exists
- [x] Searches projects, features, tasks by name/description
- [x] Returns entity_type, id, title, subtitle, url
- [x] Frontend API function exists
- [x] CommandPalette shows search results
- [x] Clicking result navigates to entity
- [x] Backend tests pass
- [x] Frontend tests pass
- [x] Build passes
