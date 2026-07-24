# TASK-0056: Pagination Component + URL Sync

**Status**: pending
**Spec**: SPEC-0013 §3
**Phase**: 0 (Foundation)
**Depends on**: TASK-0043
**Blocks**: TASK-0045, TASK-0049, TASK-0052
**Estimated effort**: 2 hours

---

## Problem

Backend returns paginated responses (`{ items, total, offset, limit }`) but frontend ignores pagination. All list views fetch all data at once.

## Acceptance Criteria

- [ ] `frontend/src/components/ui/DataTablePagination.tsx` exists
- [ ] Shows: "Showing X-Y of Z results"
- [ ] Page numbers with prev/next buttons
- [ ] Page size selector: 10, 20, 50 (default 20)
- [ ] URL sync: `?page=2&pageSize=20` in search params
- [ ] Uses TanStack Router search params
- [ ] Integrated with: ProjectList, Features list, Tasks list, Audit list, Reports list
- [ ] `npm run build` passes

## Technical Notes

- Backend pagination: `offset` + `limit` (not page numbers)
- Frontend converts: `offset = (page - 1) * pageSize`
- URL params: `page` (1-indexed), `pageSize`
- Use shadcn Pagination component
- Each list page needs to pass pagination params to API calls
