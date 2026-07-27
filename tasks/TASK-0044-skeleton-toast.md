# TASK-0044: Skeleton Loading + Toast System

**Status**: done
**Spec**: SPEC-0013 §3
**Phase**: 0 (Foundation)
**Blocks**: All page tasks
**Estimated effort**: 1 hour

---

## Problem

ProjectList uses a spinner instead of skeleton screens. `sonner` is installed but the `<Toaster>` is not mounted and no toast helpers exist.

## Acceptance Criteria

- [ ] `frontend/src/components/ui/PageSkeleton.tsx` exists with configurable skeleton layout
- [ ] `ProjectList` loading state uses `PageSkeleton` instead of spinner
- [ ] `<Toaster />` mounted in `AppShell.tsx`
- [ ] `frontend/src/lib/toast.ts` exports helper functions: `showSuccess(msg)`, `showError(msg)`, `showCreated(entity)`, `showUpdated(entity)`, `showDeleted(entity)`
- [ ] Toast pattern: `{Action} {entity} successfully` e.g. "Project created successfully"
- [ ] Toast position: bottom-right
- [ ] `npm run build` passes

## Technical Notes

- `sonner` is already in package.json dependencies
- Import: `import { Toaster } from '@/components/ui/sonner'` and `import { toast } from 'sonner'`
- Skeleton should match the card/table layout of the page it replaces
