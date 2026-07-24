# TASK-0055: Dark Mode Toggle + Theme Persistence

**Status**: pending
**Spec**: SPEC-0012 §9, SPEC-0013 §3
**Phase**: 3 (Polish)
**Depends on**: TASK-0044
**Estimated effort**: 1 hour

---

## Problem

Dark mode CSS is fully configured but there is no toggle UI. Users cannot switch themes.

## Acceptance Criteria

- [ ] Theme toggle button in TopBar (Sun/Moon/Monitor icons)
- [ ] Uses `next-themes` ThemeProvider (already in package.json)
- [ ] `<ThemeProvider>` wraps app in `main.tsx`
- [ ] Three options: Light, Dark, System
- [ ] Theme persisted in localStorage under key `upcp-theme`
- [ ] System default follows `prefers-color-scheme`
- [ ] All existing components render correctly in both themes
- [ ] Sidebar, cards, tables, badges all have correct dark mode styles
- [ ] `npm run build` passes

## Technical Notes

- `next-themes` already installed
- Import: `import { ThemeProvider } from 'next-themes'`
- Toggle: `import { useTheme } from 'next-themes'` + `const { theme, setTheme } = useTheme()`
- Icons: `Sun`, `Moon`, `Monitor` from lucide-react
- shadcn/ui already supports dark mode via CSS variables
