# UPCP Design System

## Overview

Professional design system for UPCP — a self-hosted engineering project control plane. Built on React 19, TypeScript, Tailwind CSS 4, and shadcn/ui.

**Design philosophy**: Clarity over cleverness, density without clutter, speed as a feature, keyboard-first UX.

---

## Design Tokens

### Colors

#### Brand
| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| `--color-primary` | `#2563eb` | `#60a5fa` | CTAs, links, active states |
| `--color-secondary` | `#64748b` | `#94a3b8` | Supporting elements |
| `--color-accent` | `#f59e0b` | `#fbbf24` | Highlights, badges |
| `--color-bg` | `#f8fafc` | `#0a0a0f` | Page background |
| `--color-surface` | `#ffffff` | `#111118` | Cards, modals |
| `--color-text` | `#0f172a` | `#f1f5f9` | Primary text |
| `--color-text-muted` | `#64748b` | `#94a3b8` | Secondary text |

#### Status (9 states)
| Status | Color | Usage |
|--------|-------|-------|
| `backlog` | slate | Tasks not yet started |
| `ready` | blue | Ready to be claimed |
| `in_progress` | blue | Being worked on |
| `blocked` | red | Cannot proceed |
| `done` | emerald | Completed |
| `cancelled` | gray | Abandoned |
| `needs_clarification` | amber | Waiting for answer |
| `ready_for_review` | violet | Awaiting review |
| `changes_requested` | orange | Needs rework |

#### Priority (4 levels)
| Level | Color | Label |
|-------|-------|-------|
| 0 | red | Critical |
| 1 | orange | High |
| 2 | amber | Medium |
| 3 | green | Low |

#### Actor Types
| Type | Color | Icon |
|------|-------|------|
| agent | violet | Bot |
| human | blue | User |
| system | gray | Cpu |

### Typography

- **Font**: Geist Variable (primary), Inter (fallback)
- **Mono**: JetBrains Mono
- **Scale**: xs(12) → sm(13) → base(14) → lg(16) → xl(18) → 2xl(20) → 3xl(24)
- **Body size**: 14px (not 16px)
- **Line heights**: tight(1.25) for headings, normal(1.5) for body

### Spacing

4px grid system via Tailwind spacing scale.

### Radius

| Token | Value | Usage |
|-------|-------|-------|
| `--radius-sm` | 4px | Badges, small elements |
| `--radius-md` | 6px | Buttons, inputs |
| `--radius-lg` | 8px | Cards, dropdowns |
| `--radius-xl` | 12px | Modals, sheets |

### Animation

| Token | Duration | Usage |
|-------|----------|-------|
| `--duration-instant` | 50ms | Hover states |
| `--duration-fast` | 100ms | Dropdowns, tooltips |
| `--duration-default` | 150ms | Buttons, inputs |
| `--duration-slow` | 200ms | Modals, tabs |
| `--duration-slower` | 300ms | Sheets, page transitions |

**Easing**: `--ease-default` (0.4, 0, 0.2, 1), `--ease-spring` (0.34, 1.56, 0.64, 1)

**Reduced motion**: All animations disabled when `prefers-reduced-motion: reduce`.

---

## Components

### StatusBadge

Renders a colored badge with dot indicator for task/project status.

```tsx
<StatusBadge status="in_progress" showDot size="sm" />
```

**Props**: `status`, `showDot` (default true), `size` ('sm' | 'default')

### PriorityDot

Renders a colored dot with tooltip for task priority.

```tsx
<PriorityDot priority={0} showLabel size="sm" />
```

**Props**: `priority` (0-3), `showLabel`, `size`

### AgentAvatar

Avatar with optional status indicator and heartbeat pulse.

```tsx
<AgentAvatar name="code-quality-guard" status="working" showPulse size="lg" />
```

**Props**: `name`, `avatarUrl?`, `status`, `size`, `showPulse`

### AgentStatusBadge

Badge showing agent status with optional pulse animation.

```tsx
<AgentStatusBadge status="working" showPulse />
```

### ActorBadge

Badge distinguishing agent/human/system actors.

```tsx
<ActorBadge actorType="agent" actorName="code-quality-guard" />
```

### ClarificationBanner

Alert-style component for agent clarification requests.

```tsx
<ClarificationBanner
  taskName="JWT Token Service"
  question="What is the expected behavior?"
  askedBy="code-quality-guard"
  askedAt={timestamp}
  isBlocking
  onAnswer={() => {}}
/>
```

### ReviewVerdictCard

Card showing agent review verdict with confidence and findings.

```tsx
<ReviewVerdictCard
  agentName="code-quality-guard"
  verdict="approve"
  confidence={0.92}
  findingsCount={0}
  summary="All criteria met."
  createdAt={timestamp}
/>
```

### DataTable

Reusable data table with density toggle, sorting, filtering.

```tsx
<DataTable
  columns={columns}
  data={data}
  total={100}
  offset={0}
  limit={20}
  onPageChange={handlePage}
  onPageSizeChange={handleSize}
  onSortChange={handleSort}
  onFilterChange={handleFilter}
  filterable
  sortable
  density="compact"
  onRowClick={handleRowClick}
/>
```

### ShortcutsDialog

Modal showing all keyboard shortcuts.

```tsx
<ShortcutsDialog open={open} onOpenChange={setOpen} />
```

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+K` | Command palette |
| `Ctrl+J` | Toggle theme |
| `?` | Show shortcuts |
| `G D` | Go to Dashboard |
| `G P` | Go to Projects |
| `G R` | Go to Reports |
| `G S` | Go to Settings |

**Sequence shortcuts**: Press `G` then a letter within 1 second.

---

## Animations

| Animation | Class | Duration |
|-----------|-------|----------|
| Heartbeat pulse | `animate-heartbeat-pulse` | 2s infinite |
| Badge pop | `animate-badge-pop` | 200ms spring |
| Slide in right | `animate-slide-in-right` | 300ms |
| Fade in up | `animate-fade-in-up` | 200ms |
| Stagger children | `animate-stagger` | 30ms delay per child |

---

## File Structure

```
src/
├── components/
│   ├── ui/              # Reusable primitives
│   │   ├── AgentAvatar.tsx
│   │   ├── AgentStatusBadge.tsx
│   │   ├── ActorBadge.tsx
│   │   ├── ClarificationBanner.tsx
│   │   ├── DataTable.tsx
│   │   ├── ReviewVerdictCard.tsx
│   │   ├── ShortcutsDialog.tsx
│   │   ├── StatusBadge.tsx
│   │   ├── PriorityDot.tsx
│   │   └── ... (shadcn components)
│   ├── dashboard/       # Dashboard-specific
│   │   ├── AttentionCards.tsx
│   │   ├── AgentActivitySummary.tsx
│   │   └── LiveActivityFeed.tsx
│   ├── layouts/         # App shell
│   │   ├── AppShell.tsx
│   │   ├── AppSidebar.tsx
│   │   ├── TopBar.tsx
│   │   └── BreadcrumbBar.tsx
│   └── project/         # Project-specific
│       ├── ProjectDetail.tsx
│       ├── TaskDetailSheet.tsx
│       └── ...
├── hooks/
│   └── use-hotkeys.ts   # Global hotkey system
├── lib/
│   └── constants.ts     # Design tokens, nav, colors
└── index.css            # CSS variables, animations
```

---

## Implementation Notes

### Dark Mode

Uses `next-themes` with class-based switching. All colors defined as CSS variables with `.dark` overrides. Semantic colors (status, priority, agent) have explicit dark variants.

### Accessibility

- Skip links for main content
- Focus indicators on all interactive elements
- ARIA labels on icon-only buttons
- Keyboard navigation in all components
- Screen reader announcements for dynamic content
- Reduced motion support

### Performance

- Lazy-loaded route components
- Code-split by route
- Optimistic updates for mutations
- Skeleton loading for all async states
