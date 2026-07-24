# TASK-0056: Pagination Component + URL Sync

**Status**: done
**Spec**: SPEC-0013 §3
**Phase**: 0 (Foundation)
**Depends on**: TASK-0043
**Blocks**: TASK-0045, TASK-0049, TASK-0052
**Estimated effort**: 2 hours

---

## Problem

Backend returns paginated responses (`{ items, total, offset, limit }`) but frontend ignores pagination. All list views fetch all data at once.

## Acceptance Criteria

- [x] `frontend/src/components/ui/DataTablePagination.tsx` exists
- [x] Shows: "Showing X-Y of Z results"
- [x] Page numbers with prev/next buttons
- [x] Page size selector: 10, 20, 50 (default 20)
- [x] URL sync: `?page=2&pageSize=20` in search params
- [x] Uses TanStack Router search params
- [x] Integrated with: ProjectList, Features list, Tasks list, Audit list, Reports list
- [x] `npm run build` passes

## Technical Notes

- Backend pagination: `offset` + `limit` (not page numbers)
- Frontend converts: `offset = (page - 1) * pageSize`
- URL params: `page` (1-indexed), `pageSize`
- Use shadcn Pagination component
- Each list page needs to pass pagination params to API calls

## Implementation

- `use-url-pagination.ts` hook reads/writes `page` + `pageSize` from URL search params
- `DataTablePagination` component accepts `offset`, `limit`, `total`, `onPageChange`, `onPageSizeChange`
- All list pages use `useUrlPagination(20)` and pass `{ offset, limit }` to their respective hooks
- Pages: ProjectList, DeliveryPage, AuditPage, ReportsPage — all render DataTablePagination when `total > limit`
