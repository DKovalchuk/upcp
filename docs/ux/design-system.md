# Design System Reference

UPCP design system reference. shadcn/ui + Tailwind CSS v4 + Lucide React.

---

## 1. Color Palette

### Base (CSS Variables)

| Token | Role | Light | Dark |
|-------|------|-------|------|
| `--color-primary` | CTAs, links | `#2563eb` | `#3b82f6` |
| `--color-secondary` | Secondary buttons | `#64748b` | `#94a3b8` |
| `--color-accent` | Highlights, warnings | `#f59e0b` | `#fbbf24` |
| `--color-bg` | Page background | `#ffffff` | `#0f172a` |
| `--color-surface` | Cards, panels | `#f8fafc` | `#1e293b` |
| `--color-text` | Primary text | `#1e293b` | `#f1f5f9` |
| `--color-text-muted` | Secondary text | `#64748b` | `#94a3b8` |

### Status Colors

| Status | Background | Text |
|--------|-----------|------|
| `active` / `passed` | `bg-emerald-500/10` | `text-emerald-700 dark:text-emerald-400` |
| `backlog` / `pending` | `bg-slate-500/10` | `text-slate-700 dark:text-slate-400` |
| `in_progress` | `bg-blue-500/10` | `text-blue-700 dark:text-blue-400` |
| `paused` / `blocked` | `bg-amber-500/10` | `text-amber-700 dark:text-amber-400` |
| `archived` / `failed` / `rejected` | `bg-red-500/10` | `text-red-700 dark:text-red-400` |
| `done` / `completed` / `approved` | `bg-violet-500/10` | `text-violet-700 dark:text-violet-400` |
| `ready` / `review` | `bg-cyan-500/10` | `text-cyan-700 dark:text-cyan-400` |

### Priority Colors

| Priority | Indicator | Label |
|----------|-----------|-------|
| 0 (P0) | `bg-red-500` dot | Critical |
| 1 (P1) | `bg-orange-500` dot | High |
| 2 (P2) | `bg-blue-500` dot | Medium |
| 3 (P3) | `bg-slate-400` dot | Low |

---

## 2. Typography

| Element | Class | Size | Weight |
|---------|-------|------|--------|
| Page title | `text-2xl font-bold tracking-tight` | 24px | 700 |
| Section heading | `text-lg font-semibold` | 18px | 600 |
| Card title | `text-base font-medium` | 16px | 500 |
| Body | `text-sm` | 14px | 400 |
| Caption | `text-xs text-muted-foreground` | 12px | 400 |
| Code/slug | `font-mono text-xs` | 12px | 400 |

**Font:** Inter, system fallback. Mono: JetBrains Mono.

---

## 3. Spacing

| Token | Value | Usage |
|-------|-------|-------|
| `xs` | 4px | Inline gaps |
| `sm` | 8px | Component padding |
| `md` | 16px | Card padding |
| `lg` | 24px | Section gaps |
| `xl` | 32px | Section spacing |
| `2xl` | 48px | Page sections |
| `3xl` | 64px | Page padding |

---

## 4. Dark Mode

`next-themes` with CSS class strategy. Toggle: Sun/Moon/Monitor in TopBar.

Rules: CSS variables only, dark-variants for status, `dark:invert` for images.

---

## 5. Custom Components

### StatusBadge

```tsx
<StatusBadge status="in_progress" />
```

Props: `status: string`, `size: "sm" | "md"`. Maps to status color table.

---

### PriorityDot

```tsx
<PriorityDot priority={1} />
```

Props: `priority: 0 | 1 | 2 | 3`. Accessibility: `role="img"`, `aria-label`.

---

### EmptyState

```tsx
<EmptyState
  icon={<FileCheck />}
  title="No evidence attached"
  description="Attach evidence to support task completion."
  action={<Button>Attach Evidence</Button>}
}
```

Centered, `py-12`, muted colors.

---

### ErrorState

Same props as EmptyState. Used for error conditions.

---

### ConfirmDialog

```tsx
<ConfirmDialog
  open={open}
  onOpenChange={setOpen}
  title="Revoke Token"
  description="This action cannot be undone."
  confirmLabel="Revoke"
  variant="destructive"
  onConfirm={handleRevoke}
/>
```

Async-aware: spinner during async onConfirm.

---

### PageHeader

```tsx
<PageHeader title="Delivery" description="..." actions={<Button>New</Button>} />
```

---

### PageSkeleton

Skeleton matching expected page layout.

---

### SearchInput

Debounce + clear button. Props: `value`, `onChange`, `placeholder`.

---

### DataTablePagination

Props: `page`, `pageSize`, `total`, `onPageChange`, `onPageSizeChange`.

---

## 6. shadcn/ui Components

| Component | Usage |
|-----------|-------|
| Button | Actions |
| Badge | Status, type labels |
| Card | Sections |
| Dialog | Modal forms |
| Sheet | Task detail |
| Tabs | Project/task tabs |
| Table | List views |
| Input | Forms, search |
| Select | Dropdowns |
| DropdownMenu | Menus |
| Command | Cmd+K palette |
| Tooltip | Hints |
| Separator | Dividers |
| Skeleton | Loading |
| Avatar | Avatars |
| Progress | Progress bars |
| Breadcrumb | Navigation |
| ScrollArea | Scrollable regions |
| Sonner | Toasts |
| Sidebar | App sidebar |

---

## 7. Layout Constants

```css
--sidebar-width: 240px;
--sidebar-collapsed: 64px;
--topbar-height: 56px;
--breadcrumb-height: 40px;
--content-max-width: 1400px;
--sheet-width: 672px;
```
