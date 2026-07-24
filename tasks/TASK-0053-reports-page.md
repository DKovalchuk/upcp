# TASK-0053: Reports Page

**Status**: pending
**Spec**: SPEC-0012 §4.9, SPEC-0013 §3
**Phase**: 2 (Extended)
**Depends on**: TASK-0046
**Estimated effort**: 2-3 hours

---

## Problem

No Reports page exists. Backend has report generation, listing, export, and LLM summary endpoints.

## Acceptance Criteria

- [ ] Reports tab in Project Detail renders `ReportsPage`
- [ ] Table columns: Type, Summary (truncated), Created, Actions (View, Export, Summarize)
- [ ] "Generate Daily Report" button calls POST endpoint
- [ ] Click "View" → navigates to report detail (or opens in dialog)
- [ ] Report detail: formatted content rendered as cards/sections
- [ ] "Export Markdown" button → triggers file download
- [ ] "Summarize" button → calls LLM summarize endpoint, shows result
- [ ] Toast on generate/summarize success/error
- [ ] Loading: skeleton
- [ ] Empty: "No reports yet. Generate your first daily report."
- [ ] `npm run build` passes

## Technical Notes

- Use `useReports(projectId)` for list
- Use `useReport(id)` for detail
- Export: create blob from markdown string, trigger download via `<a>` click
- LLM summarize: POST to `/api/v1/reports/:id/summarize`, show summary in toast or inline
