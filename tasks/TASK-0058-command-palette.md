# TASK-0058: Command Palette (Cmd+K)

**Status**: done
**Spec**: SPEC-0013 §6
**Phase**: 3 (Polish)
**Depends on**: TASK-0043, TASK-0046
**Estimated effort**: 2-3 hours

---

## Problem

No quick way to navigate the app or trigger common actions. Users must click through sidebar nav and menus.

## Scope

1. Install `cmdk` package (shadcn Command component foundation)
2. Create shadcn Command components: `command.tsx` (CommandDialog, CommandInput, CommandList, CommandGroup, CommandItem, CommandEmpty, CommandSeparator)
3. Create `CommandPalette.tsx` component with:
   - Navigation commands: Dashboard, Projects, Health, project-specific tabs
   - Action commands: New Project (on Projects page), New Feature/New Task (on Delivery page)
   - Fuzzy search filtering
   - Keyboard navigation (arrow keys, Enter to select)
4. Wire `Cmd+K` / `Ctrl+K` global shortcut to open/close
5. Add to `AppShell.tsx`

## Acceptance Criteria

- [x] `cmdk` installed
- [x] shadcn Command components exist in `components/ui/command.tsx`
- [x] `CommandPalette.tsx` renders with navigation + action commands
- [x] Cmd+K opens, Escape closes
- [x] Typing filters commands fuzzy
- [x] Enter navigates / triggers action
- [x] Clicking overlay or pressing Escape closes
- [x] Works in both light and dark mode
- [x] `npm run build` passes
- [x] Tests pass

## Technical Notes

- Use `cmdk` v1.x (React 19 compatible)
- Pattern: `CommandDialog` wraps `cmdk`'s Dialog + Command
- Global keydown listener for Cmd+K
- Commands are static (no backend search needed yet)
- Navigation uses `useNavigate` from TanStack Router
