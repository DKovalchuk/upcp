# Agent Workflow UI Design

Comprehensive UI specification for agent workflow features. Builds on existing UX docs (`agent-center.md`, `task-detail.md`, `evidence-and-review-ui.md`, `notifications.md`) and adds implementation-level detail: component trees, API wiring, state management, responsive behavior, accessibility, and animation.

---

## Table of Contents

1. [Agent Center Page](#1-agent-center-page)
2. [Enhanced Task Detail Sheet](#2-enhanced-task-detail-sheet)
3. [Attention Dashboard Enhancements](#3-attention-dashboard-enhancements)
4. [Task Board Enhancements](#4-task-board-enhancements)
5. [Workflow Notifications](#5-workflow-notifications)
6. [Command Palette Extensions](#6-command-palette-extensions)
7. [Shared Components](#7-shared-components)
8. [State Management](#8-state-management)
9. [API Integration Map](#9-api-integration-map)
10. [Responsive Breakpoints](#10-responsive-breakpoints)
11. [Accessibility](#11-accessibility)
12. [Animation & Motion](#12-animation--motion)
13. [Error & Empty States](#13-error--empty-states)
14. [Dark Mode](#14-dark-mode)

---

## 1. Agent Center Page

**Route:** `/agents`
**Nav:** Add to `NAV_GROUPS[0].items` in `constants.ts` (Main group, after Projects)

### 1.1 Navigation Registration

```ts
// constants.ts — add to NAV_GROUPS[0].items
{ title: 'Agents', icon: Bot, path: '/agents' },
```

Add `agentsRoute` to `router.tsx`, lazy-loading `AgentCenterPage`.

Hotkey already defined: `{ key: 'a', sequence: 'g' }`.

### 1.2 Page Layout — ASCII Wireframe

```
┌─────────────────────────────────────────────────────────────────────┐
│  Agents                              [+ New Agent]                  │
├─────────────────────────────────────────────────────────────────────┤
│  [Search...]  [Status ▾]  [Type ▾]  [View: Grid|Table]            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │ ● claude-    │  │ ● gpt-4-     │  │ ○ codex-     │             │
│  │   builder    │  │   reviewer   │  │   helper     │             │
│  │              │  │              │  │              │             │
│  │ Working      │  │ Working      │  │ Idle         │             │
│  │ ──────────   │  │ ──────────   │  │ ──────────   │             │
│  │ TASK-0042    │  │ TASK-0039    │  │ No task      │             │
│  │ 67% ██████░░ │  │ 12% █░░░░░░░ │  │              │             │
│  │              │  │              │  │              │             │
│  │ 3 tasks done │  │ 1 task done  │  │ 0 tasks done │             │
│  │ 95% success  │  │ 100% success │  │ --           │             │
│  │ HB: 2m ago   │  │ HB: 30s ago  │  │ Last: 2h ago │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
│                                                                     │
│  ── Stale / Offline ──                                              │
│  ┌──────────────┐                                                  │
│  │ ○ deepseek-  │                                                  │
│  │   explorer   │                                                  │
│  │              │                                                  │
│  │ Stale        │                                                  │
│  │ TASK-0045    │                                                  │
│  │ HB: 15m ago  │                                                  │
│  │ [Release]    │                                                  │
│  └──────────────┘                                                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.3 Component Tree

```
AgentCenterPage
├── PageHeader ("Agents", description, actions: [NewAgentButton])
├── AgentToolbar
│   ├── SearchInput (reuse existing)
│   ├── StatusFilter (Select: all/working/idle/blocked/stale/offline)
│   ├── TypeFilter (Select: all/llm/script/human_assisted)
│   └── ViewToggle (reuse List/Grid pattern from DeliveryPage)
├── AgentGrid (when viewMode === 'grid')
│   └── AgentCard[] (mapped from agents)
└── AgentTable (when viewMode === 'table')
    └── DataTable (reuse TanStack Table pattern)
```

### 1.4 AgentCard Component

**File:** `frontend/src/components/agents/AgentCard.tsx`

```
Props:
  agent: AgentProfile
  onSelect: (agentId: string) => void
  onRelease: (taskId: string) => void

Layout: Card with left border color by status (reuse STAT_CARD_STYLES pattern)
  - Top: AgentAvatar (lg) + Name + AgentStatusBadge
  - Middle: Current task title + progress bar (reuse pattern from AgentActivitySummary)
  - Bottom: Metrics row (tasks done, success rate, last heartbeat)

Interactions:
  - Click card → navigate to /agents/:id (Agent Detail page)
  - [Release] button → ConfirmDialog → releaseTask() mutation
  - Hover → ring-1 ring-ring/20 (reuse existing hover pattern)
```

### 1.5 Agent Detail Page

**Route:** `/agents/$agentId`

```
┌─────────────────────────────────────────────────────────────────────┐
│  ← Agents / claude-opus-builder                            [Edit]  │
├─────────────────────────────────────────────────────────────────────┤
│  [AgentAvatar lg]  claude-opus-builder                              │
│  Type: llm · Status: active · Scopes: delivery, quality             │
│  "Code builder agent based on Claude Opus"                          │
│  Created: 2026-07-20 · Last active: 2m ago                         │
├─────────────────────────────────────────────────────────────────────┤
│  [Overview] [Tokens] [Scopes] [Claims] [Activity] [Evidence]       │
│  [Reviews] [Clarifications] [Audit]                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  (tab content — see agent-center.md for full tab spec)             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Component Tree:**

```
AgentDetailPage
├── Breadcrumb: Agents / <agent-name>
├── AgentProfileHeader
│   ├── AgentAvatar (lg)
│   ├── Name, Type badge, StatusBadge
│   ├── Description
│   └── Meta: created, last active
├── Tabs
│   ├── OverviewTab — summary cards
│   ├── TokensTab — token table + generate/revoke
│   ├── ScopesTab — checkbox grid
│   ├── ClaimsTab — TanStack Table with claim history
│   ├── ActivityTab — event feed (reuse LiveActivityFeed pattern)
│   ├── EvidenceTab — evidence list (reuse EvidenceCard)
│   ├── ReviewsTab — review rounds (reuse ReviewVerdictCard)
│   ├── ClarificationsTab — clarification list (reuse ClarificationBanner)
│   └── AuditTab — timeline
```

### 1.6 Agent Table Columns

| Column | Cell | Sort | Filter |
|--------|------|------|--------|
| Status dot | `AgentAvatar` + colored dot | No | By status |
| Name | Text, bold | Yes | Search |
| Type | Badge (llm/script/human_assisted) | Yes | Dropdown |
| Status | `AgentStatusBadge` | Yes | Dropdown |
| Active Task | Task title + progress bar | No | — |
| Tasks Done | Number | Yes | — |
| Success Rate | Percentage | Yes | — |
| Last Activity | `formatRelativeTime()` | Yes | — |

### 1.7 API Integration

```
// New file: frontend/src/lib/api/agents.ts

GET  /api/v1/agents                              → fetchAgents()
GET  /api/v1/agents/:id                          → fetchAgent(id)
POST /api/v1/agents                              → createAgent(data)
PATCH /api/v1/agents/:id                         → updateAgent(id, data)
DELETE /api/v1/agents/:id                        → deleteAgent(id)
POST /api/v1/agents/:id/activate                 → activateAgent(id)
POST /api/v1/agents/:id/deactivate               → deactivateAgent(id)
GET  /api/v1/agents/:id/claims                   → fetchAgentClaims(id)
GET  /api/v1/agents/:id/activity                 → fetchAgentActivity(id)
GET  /api/v1/agents/:id/evidence                 → fetchAgentEvidence(id)
GET  /api/v1/agents/:id/reviews                  → fetchAgentReviews(id)
GET  /api/v1/agents/:id/clarifications           → fetchAgentClarifications(id)
```

### 1.8 New Types

```ts
// frontend/src/types/agent.ts

export interface AgentProfile {
  id: string;
  name: string;
  type: 'llm' | 'script' | 'human_assisted';
  description: string | null;
  is_active: boolean;
  scopes: Record<string, unknown> | null;
  created_at: string;
  last_active_at: string | null;
}

export interface AgentMetrics {
  tasks_completed: number;
  tasks_failed: number;
  success_rate: number;
  avg_cycle_time_hours: number;
  current_task_id: string | null;
  current_task_title: string | null;
  current_progress_percent: number;
  last_heartbeat_at: string | null;
  is_stale: boolean;
  status: 'working' | 'idle' | 'blocked' | 'offline' | 'stale';
}

export interface AgentListResponse {
  items: (AgentProfile & AgentMetrics)[];
  total: number;
}
```

### 1.9 New Hooks

```ts
// frontend/src/hooks/use-agents.ts

export function useAgents(filters?: { status?: string; type?: string }) { ... }
export function useAgent(agentId: string) { ... }
export function useAgentMetrics(agentId: string) { ... }   // polling: 10s
export function useCreateAgent() { ... }
export function useUpdateAgent() { ... }
export function useActivateAgent() { ... }
export function useDeactivateAgent() { ... }
```

### 1.10 Activation / Deactivation

Toggle in Agent Detail header:

```
[Deactivate Agent]  → ConfirmDialog("Deactivate this agent? Active claims will be released.")
                      → POST /agents/:id/deactivate
                      → Toast: "Agent deactivated"
                      → Invalidate agents queries

[Activate Agent]    → POST /agents/:id/activate
                      → Toast: "Agent activated"
```

### 1.11 Responsive Behavior

| Breakpoint | Grid Columns | Sidebar |
|-----------|-------------|---------|
| < 640px | 1 column, cards stack | Sidebar collapsed |
| 640–1023px | 2 columns | Sidebar collapsed |
| ≥ 1024px | 3 columns | Sidebar expanded |

On mobile (< 640px): table view becomes a card list. Sort/filter in a bottom sheet.

---

## 2. Enhanced Task Detail Sheet

**File:** `frontend/src/components/project/TaskDetailSheet.tsx` (enhance existing)

### 2.1 Enhanced Tab Structure

Current tabs: Details, Execution, AC, DoD, Subtasks.

New/enhanced tabs:

```
[Details] [Execution] [Clarifications] [Evidence] [Reviews] [AC] [DoD] [Subtasks] [Git]
```

Move Clarifications, Evidence, and Reviews out of Execution into dedicated tabs. The Execution tab becomes focused on agent heartbeat/claim state.

### 2.2 Execution Tab — Enhanced

**ASCII Wireframe:**

```
┌─────────────────────────────────────────────────────────────┐
│ Execution                                                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─ Claim ───────────────────────────────────────────────┐  │
│  │ [AgentAvatar] claude-builder     ● Working (pulsing)  │  │
│  │                                                       │  │
│  │ Claimed: 12:05 (35m ago)                             │  │
│  │ Last heartbeat: 2m ago                                │  │
│  │                                                       │  │
│  │ ████████████████░░░░░░░░░ 67%                        │  │
│  │ Current: Writing unit tests                           │  │
│  │ Next: Run linter                                      │  │
│  │ ETA: ~15m                                             │  │
│  │                                                       │  │
│  │ [Release Claim]  [Send Message]                       │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─ State Timeline ──────────────────────────────────────┐  │
│  │ ○ backlog · 12:00                                     │  │
│  │ │                                                     │  │
│  │ ● ready · 12:03                                       │  │
│  │ │                                                     │  │
│  │ ◉ claimed · 12:05 · claude-builder                   │  │
│  │ │                                                     │  │
│  │ ◉ in_progress · 12:08                                │  │
│  │ │                                                     │  │
│  │ ◌ (current)                                           │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Component: ClaimInfoCard**

```tsx
// NEW: frontend/src/components/agents/ClaimInfoCard.tsx

interface ClaimInfoCardProps {
  claim: TaskClaim;                   // from useTaskClaims
  heartbeat: Heartbeat | null;        // latest from useTaskHeartbeats
  onRelease: () => void;
  onSendMessage: () => void;
  isReleasing: boolean;
}
```

**Heartbeat Indicator Logic:**

```ts
function getHeartbeatStatus(lastHeartbeatAt: string | null): 'green' | 'yellow' | 'red' {
  if (!lastHeartbeatAt) return 'red';
  const minutesAgo = (Date.now() - new Date(lastHeartbeatAt).getTime()) / 60000;
  if (minutesAgo < 3) return 'green';    // fresh
  if (minutesAgo < 7) return 'yellow';   // aging
  return 'red';                           // stale (matches STALE_HEARTBEAT_MINUTES = 7)
}
```

**Stale Warning (reuse ClarificationBanner pattern):**

```tsx
{heartbeatStatus === 'red' && (
  <div className="flex items-center gap-2 rounded-lg border border-amber-500/30 bg-amber-500/5 p-3">
    <AlertTriangle className="h-4 w-4 text-amber-600" />
    <div className="flex-1">
      <p className="text-sm font-medium">Agent heartbeat is stale</p>
      <p className="text-xs text-muted-foreground">
        Last heartbeat {formatRelativeTime(claim.last_heartbeat_at)}
      </p>
    </div>
    <Button variant="outline" size="sm" onClick={onRelease}>
      Release
    </Button>
  </div>
)}
```

**Component: StateTimeline**

```tsx
// NEW: frontend/src/components/agents/StateTimeline.tsx

interface StateTimelineProps {
  events: StateEvent[];    // derived from claims + heartbeats + status changes
}

interface StateEvent {
  state: string;
  timestamp: string;
  actor_id?: string;
  actor_type?: 'agent' | 'human' | 'system';
}
```

Visual: vertical line with colored dots. Active state = pulsing dot. Current state = larger dot. Each dot uses the matching `STATUS_COLORS` from `constants.ts`.

**Quick Actions:**

- **Release Claim:** `useReleaseTask()` mutation → toast → invalidate claims/heartbeats queries
- **Send Message:** Opens `SendMessageDialog` (simple Dialog with textarea) → creates clarification request or inbox message

### 2.3 Clarifications Tab — Enhanced

Move out of Execution tab. New dedicated tab.

**ASCII Wireframe:**

```
┌─────────────────────────────────────────────────────────────┐
│ Clarifications                                   Filter: [▾] │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─ Thread 1 ────────────────────────────────────────────┐  │
│  │ 🔒 Blocking · claude-builder · 30m ago                │  │
│  │                                                       │  │
│  │ "Should due_date use ISO 8601 or Unix timestamp?"     │  │
│  │                                                       │  │
│  │ ┌─ Answer ──────────────────────────────────────────┐ │  │
│  │ │ You (human-reviewer) · 5m ago                     │ │  │
│  │ │ "Use ISO 8601 with timezone. e.g. 2026-07-20T..." │ │  │
│  │ └───────────────────────────────────────────────────┘ │  │
│  │                                                       │  │
│  │ Status: ✓ Answered                                    │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─ Thread 2 ────────────────────────────────────────────┐  │
│  │ 🔒 Blocking · gpt-4-reviewer · 15m ago               │  │
│  │                                                       │  │
│  │ "Which auth strategy: JWT or session cookies?"        │  │
│  │                                                       │  │
│  │ ⏳ Waiting: 15m                                       │  │
│  │                                                       │  │
│  │ ┌───────────────────────────────────────────────────┐ │  │
│  │ │ [Type your answer...]                   [Send]    │ │  │
│  │ └───────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  ── Answered ──                                               │
│                                                              │
│  ┌─ Thread 3 ────────────────────────────────────────────┐  │
│  │ 💬 Non-blocking · codex-helper · 2h ago               │  │
│  │ "Should we add pagination to the list endpoint?"      │  │
│  │ ✓ Answered · "Yes, use cursor-based pagination."      │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Component: ClarificationThread**

```tsx
// NEW: frontend/src/components/agents/ClarificationThread.tsx

interface ClarificationThreadProps {
  clarification: ClarificationRequest;
  onAnswer: (id: string, answer: string) => void;
  isAnswering: boolean;
}
```

**Inline Answer:** Textarea + Send button, hidden when already answered. Uses `useMutation` → `answerClarification(clarificationId, answer)` → invalidate clarifications query → toast.

**Waiting Indicator:** Shows time since question was asked. Color coding: < 10m = normal, 10-30m = yellow, > 30m = red. Uses `formatRelativeTime()`.

**Filters:** Open | Answered | Blocking | All — via `TabsTrigger` or `Select`.

### 2.4 Evidence Tab — New

**ASCII Wireframe:**

```
┌─────────────────────────────────────────────────────────────┐
│ Evidence (3)                               [Attach Evidence] │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─ Evidence 1 ──────────────────────────────────────────┐  │
│  │ 📋 test_output · 1h ago                               │  │
│  │ by claude-builder                                      │  │
│  │                                                        │  │
│  │ pytest backend/tests/ -v                               │  │
│  │ 47 passed, 0 failed, 0 warnings in 3.2s               │  │
│  │                                                        │  │
│  │ ✓ Verified by human-reviewer                           │  │
│  │                                                        │  │
│  │ [View Details]                              [Accept]   │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─ Evidence 2 ──────────────────────────────────────────┐  │
│  │ 🖼️ screenshot · 45m ago                               │  │
│  │ by claude-builder                                      │  │
│  │                                                        │  │
│  │ [screenshot thumbnail preview]                         │  │
│  │                                                        │  │
│  │ ○ Unverified                                           │  │
│  │                                                        │  │
│  │ [Verify]  [Reject]                          [View]     │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─ Evidence 3 ──────────────────────────────────────────┐  │
│  │ 🔗 url · 30m ago                                      │  │
│  │ by gpt-4-reviewer                                      │  │
│  │                                                        │  │
│  │ https://example.com/api-docs                           │  │
│  │                                                        │  │
│  │ ○ Unverified                                           │  │
│  │                                                        │  │
│  │ [Verify]  [Reject]                          [View]     │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Component: EvidenceCard**

```tsx
// NEW: frontend/src/components/agents/EvidenceCard.tsx

interface EvidenceCardProps {
  evidence: Evidence;
  onVerify: (id: string) => void;
  onAccept: (id: string) => void;
  onReject: (id: string, reason: string) => void;
  onViewDetails: (id: string) => void;
}
```

**Type Icons:**

```ts
const EVIDENCE_TYPE_ICONS: Record<string, LucideIcon> = {
  test_output: FlaskConical,
  screenshot: Image,
  log: ScrollText,
  url: Link,
  file: FileText,
  artifact: Package,
};
```

**Verification State Badges:**

```ts
const VERIFICATION_STYLES = {
  unverified: { bg: 'bg-slate-500/10', text: 'text-slate-600 dark:text-slate-400', label: 'Unverified' },
  agent_verified: { bg: 'bg-blue-500/10', text: 'text-blue-600 dark:text-blue-400', label: 'Agent Verified' },
  human_accepted: { bg: 'bg-emerald-500/10', text: 'text-emerald-600 dark:text-emerald-400', label: 'Accepted' },
  rejected: { bg: 'bg-red-500/10', text: 'text-red-600 dark:text-red-400', label: 'Rejected' },
};
```

**Evidence Detail Preview:** Expandable content snippet (5 lines default, click to expand). For URLs: show link + title. For screenshots: thumbnail with zoom.

**Attach Evidence Dialog:**

```tsx
// Uses EntityFormDialog pattern
<EntityFormDialog
  open={showAttach}
  onOpenChange={setShowAttach}
  title="Attach Evidence"
  fields={[
    { name: 'type', label: 'Type', type: 'select', options: ['test_output', 'screenshot', 'log', 'url', 'file'] },
    { name: 'title', label: 'Title', type: 'text' },
    { name: 'description', label: 'Description', type: 'textarea' },
    { name: 'url', label: 'URL', type: 'text', showWhen: { type: 'url' } },
    { name: 'content_snippet', label: 'Content', type: 'textarea', showWhen: { type: ['test_output', 'log'] } },
  ]}
  onSubmit={handleAttachEvidence}
  submitLabel="Attach"
/>
```

**Action Buttons:**

| State | Verify | Accept | Reject | View |
|-------|--------|--------|--------|------|
| unverified | ✅ | ❌ | ✅ | ✅ |
| agent_verified | ❌ | ✅ | ✅ | ✅ |
| human_accepted | ❌ | ❌ | ❌ | ✅ |
| rejected | ❌ | ❌ | ❌ | ✅ |

### 2.5 Reviews Tab — New

**ASCII Wireframe:**

```
┌─────────────────────────────────────────────────────────────┐
│ Reviews                                        [Submit for  │
│                                                  Review]    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ── Round 2 (in progress) ─────────────────────────────────  │
│  Requested by human-reviewer · 10m ago                       │
│  Reviewer: gpt-4-reviewer                                    │
│  Status: In Progress                                         │
│                                                              │
│  ┌─ Finding 1 ────────────────────────────────────────────┐  │
│  │ [!] medium · code_quality                              │  │
│  │ Missing error handling in UserService.create()         │  │
│  │                                                        │  │
│  │ Suggestion: Wrap db.add() in try/except                │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ── Round 1 (completed) ───────────────────────────────────  │
│  Reviewer: gpt-4-reviewer · 2h ago                           │
│  Verdict: Changes Requested · Confidence: 85%                │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ ⚠️ Changes Requested                                   │  │
│  │ Confidence: ████████░░ 85%                             │  │
│  │                                                        │  │
│  │ "Two medium findings. Fix error handling and remove    │  │
│  │  unused import before re-submitting."                  │  │
│  │                                                        │  │
│  │ by gpt-4-reviewer · 2h ago                             │  │
│  │                                                        │  │
│  │ [Confirm Approve] [Request Changes] [Reject]          │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  Findings (2):                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ [medium] code_quality                                  │  │
│  │ Missing error handling in create()                     │  │
│  │ backend/app/users/service.py:42-58                     │  │
│  ├────────────────────────────────────────────────────────┤  │
│  │ [info] code_quality                                    │  │
│  │ Unused import                                          │  │
│  │ backend/app/users/service.py:3                         │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Component: ReviewRoundSection**

```tsx
// NEW: frontend/src/components/agents/ReviewRoundSection.tsx

interface ReviewRoundSectionProps {
  round: ReviewRound;
  findings: ReviewFinding[];
  onSubmitVerdict: (roundId: string, verdict: string, confidence: number, summary: string) => void;
}
```

**Component: FindingCard**

```tsx
// NEW: frontend/src/components/agents/FindingCard.tsx

interface FindingCardProps {
  finding: ReviewFinding;
}

// Severity badges using existing badge pattern:
const FINDING_SEVERITY_STYLES = {
  info:     { bg: 'bg-blue-500/10', text: 'text-blue-600 dark:text-blue-400' },
  low:      { bg: 'bg-emerald-500/10', text: 'text-emerald-600 dark:text-emerald-400' },
  medium:   { bg: 'bg-amber-500/10', text: 'text-amber-600 dark:text-amber-400' },
  high:     { bg: 'bg-orange-500/10', text: 'text-orange-600 dark:text-orange-400' },
  critical: { bg: 'bg-red-500/10', text: 'text-red-600 dark:text-red-400' },
};
```

**Submit for Review Button:** Disabled when quality gate not passed. Tooltip shows reason:

```tsx
<Button
  disabled={!gatePassed}
  title={!gatePassed ? getGateFailureReason() : undefined}
>
  Submit for Review
</Button>
```

Uses `submitForReview(taskId)` mutation → creates review round → invalidate review rounds → toast.

**Human Verdict Actions:** Reuse `ReviewVerdictCard` component with `onAccept`/`onReject` props. Uses `submitReviewVerdict(roundId, { verdict, confidence, summary })`.

### 2.6 Tab Badge Counts

Show counts on tab triggers (reuse existing pattern from AC/DoD/Subtabs):

```tsx
<TabsTrigger value="clarifications">
  <MessageCircle className="mr-1 h-3 w-3" />
  Clarifications ({openClarificationsCount})
</TabsTrigger>
<TabsTrigger value="evidence">
  <FileText className="mr-1 h-3 w-3" />
  Evidence ({evidenceCount})
</TabsTrigger>
<TabsTrigger value="reviews">
  <CheckCircle className="mr-1 h-3 w-3" />
  Reviews ({reviewRoundsCount})
</TabsTrigger>
```

---

## 3. Attention Dashboard Enhancements

**File:** `frontend/src/components/dashboard/AttentionCards.tsx` (enhance existing)

### 3.1 Enhanced Section Cards

Each attention section gains inline actions. Current implementation shows static `TaskLink` items. Enhancement:

**StaleAgentsSection — Add quick release:**

```
┌─ Stale Agent Claims ──────────────────────────────────────┐
│                                                            │
│  TASK-0045 · claude-builder                               │
│  Last heartbeat: 15m ago                                   │
│  [Release Claim]                                           │
│                                                            │
│  TASK-0039 · gpt-4-reviewer                               │
│  Last heartbeat: 9m ago                                    │
│  [Release Claim]                                           │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**OpenClarificationsSection — Add inline answer:**

```
┌─ Open Questions ──────────────────────────────────────────┐
│                                                            │
│  "Should due_date use ISO 8601..."                        │
│  claude-builder · 30m ago                                  │
│  [Answer inline...]                              [→]       │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

Click [Answer inline...] → expand to textarea + send. Click [→] → navigate to task detail clarifications tab.

**NeedsReviewSection — Add verdict actions:**

```
┌─ Needs Your Review ───────────────────────────────────────┐
│                                                            │
│  TASK-0042 · requested by claude-builder                  │
│  [Start Review]  [→]                                      │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**AgentVerdictsSection — Add confirm/reject:**

```
┌─ Verdicts Waiting ────────────────────────────────────────┐
│                                                            │
│  TASK-0042 · approve · 92% confidence                     │
│  [Confirm]  [Reject]  [→]                                 │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 3.2 Component Changes

Each section item becomes interactive instead of static `TaskLink`:

```tsx
// StaleAgentsSection — enhance renderItem
renderItem={(item) => (
  <div className="flex items-center justify-between rounded-lg border p-2">
    <div className="min-w-0">
      <p className="text-sm font-medium truncate">{item.task_id?.slice(0, 8)}</p>
      <p className="text-xs text-muted-foreground">
        {item.agent_id} · {formatRelativeTime(item.last_heartbeat as string)}
      </p>
    </div>
    <Button
      variant="ghost"
      size="sm"
      className="h-7 text-xs text-destructive"
      onClick={() => releaseClaim(item.task_id as string)}
    >
      Release
    </Button>
  </div>
)}
```

### 3.3 Live Heartbeat Section (New)

Add to Dashboard below `AgentActivitySummary`:

**Component: `LiveHeartbeatPanel`**

```tsx
// NEW: frontend/src/components/dashboard/LiveHeartbeatPanel.tsx

// Shows all active claims with real-time heartbeat status
// Polls every 10s via useQuery with refetchInterval
// Layout: compact rows (reuse AgentActivitySummary pattern)
```

### 3.4 API Changes

No new endpoints needed. Enhancement uses existing:
- `releaseTask(taskId)` for quick release
- `answerClarification(id, answer)` for inline answers
- `submitReviewVerdict(roundId, data)` for inline verdicts

---

## 4. Task Board Enhancements

**File:** `frontend/src/components/project/BoardView.tsx` (enhance existing)

### 4.1 Enhanced Task Card

**ASCII Wireframe:**

```
┌─────────────────────────────────────┐
│ ● Add User model        P1         │
│   Auth System                       │
│                                     │
│ [in-progress]                       │
│                                     │
│ ┌─────────────────────────────┐     │
│ │ [AgentAvatar sm] claude-    │     │
│ │ builder · ██░░ 67%          │     │
│ └─────────────────────────────┘     │
│                                     │
│ Evidence: 2/3 ████░░░░              │
└─────────────────────────────────────┘
```

**Enhanced DraggableTaskCard:**

```tsx
function DraggableTaskCard({ task, featureName, claim, heartbeat, evidenceStats, onSelectTask }) {
  return (
    <div className="...">
      {/* Existing: title, feature name, priority dot, status badge */}

      {/* NEW: Agent info when claimed */}
      {claim && claim.state === 'active' && (
        <div className="mt-2 flex items-center gap-2">
          <AgentAvatar
            name={claim.agent_id}
            status={getHeartbeatStatus(heartbeat?.created_at)}
            size="sm"
            showPulse={getHeartbeatStatus(heartbeat?.created_at) === 'green'}
          />
          <span className="text-xs text-muted-foreground truncate">
            {claim.agent_id}
          </span>
          {heartbeat && (
            <span className="ml-auto text-xs tabular-nums text-muted-foreground">
              {heartbeat.progress_percent}%
            </span>
          )}
        </div>
      )}

      {/* NEW: Evidence completeness */}
      {evidenceStats && evidenceStats.total > 0 && (
        <div className="mt-2 flex items-center gap-2">
          <div className="flex-1 h-1 rounded-full bg-muted">
            <div
              className="h-full rounded-full bg-emerald-500"
              style={{ width: `${(evidenceStats.verified / evidenceStats.total) * 100}%` }}
            />
          </div>
          <span className="text-[10px] tabular-nums text-muted-foreground">
            {evidenceStats.verified}/{evidenceStats.total}
          </span>
        </div>
      )}
    </div>
  );
}
```

### 4.2 Quick Claim/Release from Board

Long-press or right-click on task card → context menu:

```tsx
<DropdownMenu>
  <DropdownMenuTrigger>...</DropdownMenuTrigger>
  <DropdownMenuContent>
    {!claim && <DropdownMenuItem onClick={() => claimTask(task.id)}>Claim</DropdownMenuItem>}
    {claim && claim.state === 'active' && (
      <DropdownMenuItem onClick={() => releaseTask(task.id)} className="text-destructive">
        Release Claim
      </DropdownMenuItem>
    )}
    <DropdownMenuItem onClick={() => onSelectTask(task.id)}>View Details</DropdownMenuItem>
  </DropdownMenuContent>
</DropdownMenu>
```

### 4.3 Data Loading Strategy

Board already fetches all project tasks. Enhancement requires fetching claims for all visible tasks:

```ts
// In BoardView:
const { data: claimsData } = useQuery({
  queryKey: ['project-tasks-claims', projectId],
  queryFn: () => fetchProjectTaskClaims(projectId),  // NEW API: batch fetch claims
  enabled: !!projectId,
});

// Map: taskId → TaskClaim
const claimMap = useMemo(() => {
  const map = new Map<string, TaskClaim>();
  for (const claim of claimsData?.items ?? []) {
    if (claim.state === 'active') map.set(claim.task_id, claim);
  }
  return map;
}, [claimsData]);
```

**New API endpoint needed:**

```
GET /api/v1/projects/:projectId/claims → { items: TaskClaim[] }
```

Returns all active claims for tasks in the project. Efficient single query.

### 4.4 Board Column Enhancement

Add heartbeat summary to column headers:

```
In Progress (5)  ● 3 active agents
```

### 4.5 Responsive Behavior

| Breakpoint | Columns | Card Detail |
|-----------|---------|-------------|
| < 640px | 1 (horizontal scroll) | Minimal: title + status |
| 640–1023px | 2 | Title + status + agent name |
| ≥ 1024px | 4 | Full: agent + progress + evidence |

---

## 5. Workflow Notifications

**File:** `frontend/src/components/notifications/NotificationBell.tsx` (enhance existing)

### 5.1 Toast Patterns

**File:** `frontend/src/lib/toast.ts` — add workflow-specific toasts:

```ts
// Add to showToast object:
export const showToast = {
  // ... existing ...

  // Workflow toasts
  claimStale: (taskId: string) =>
    toast.warning(`Agent heartbeat stale on ${taskId}`, {
      description: 'Consider releasing the claim.',
      action: { label: 'Release', onClick: () => releaseTask(taskId) },
    }),

  clarificationBlocking: (taskId: string, question: string) =>
    toast.error(`Blocking question on ${taskId}`, {
      description: question.slice(0, 100),
      action: { label: 'Answer', onClick: () => navigateToTask(taskId, 'clarifications') },
    }),

  reviewSubmitted: (taskId: string) =>
    toast.info(`${taskId} submitted for review`, {
      action: { label: 'Review', onClick: () => navigateToTask(taskId, 'reviews') },
    }),

  reviewApproved: (taskId: string) =>
    toast.success(`${taskId} approved`, {
      description: 'Quality review passed.',
    }),

  reviewRejected: (taskId: string, summary: string) =>
    toast.error(`${taskId} rejected`, {
      description: summary.slice(0, 100),
      action: { label: 'View', onClick: () => navigateToTask(taskId, 'reviews') },
    }),

  evidenceRejected: (taskId: string) =>
    toast.warning(`Evidence rejected on ${taskId}`, {
      action: { label: 'View', onClick: () => navigateToTask(taskId, 'evidence') },
    }),

  agentVerdictWaiting: (taskId: string, verdict: string) =>
    toast.info(`Agent verdict on ${taskId}: ${verdict}`, {
      action: { label: 'Confirm', onClick: () => navigateToTask(taskId, 'reviews') },
    }),
};
```

### 5.2 Notification Item Enhancement

Enhance `NotificationItem` in `NotificationBell.tsx` to show action buttons:

```tsx
function NotificationItem({ notification, onRead }) {
  const icon = NOTIFICATION_TYPE_ICONS[notification.type];
  const Icon = icon ?? Bell;

  return (
    <DropdownMenuItem
      className={`flex flex-col items-start gap-1 p-3 ${!notification.is_read ? 'bg-primary/5' : ''}`}
      onClick={() => { ... }}
    >
      <div className="flex w-full items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <Icon className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
          <p className="text-sm font-medium leading-tight">{notification.title}</p>
        </div>
        {!notification.is_read && <span className="... bg-primary" />}
      </div>
      <p className="text-xs text-muted-foreground line-clamp-2 pl-5">
        {notification.message}
      </p>
      <div className="flex w-full items-center justify-between pl-5">
        <p className="text-[10px] text-muted-foreground">
          {formatRelativeTime(notification.created_at)}
        </p>
        {/* NEW: inline action buttons for actionable notifications */}
        {NOTIFICATION_ACTIONS[notification.type]?.map((action) => (
          <Button
            key={action.label}
            variant="ghost"
            size="sm"
            className="h-6 text-xs"
            onClick={(e) => {
              e.stopPropagation();
              action.handler(notification);
            }}
          >
            {action.label}
          </Button>
        ))}
      </div>
    </DropdownMenuItem>
  );
}
```

### 5.3 Notification Action Map

```ts
const NOTIFICATION_ACTIONS: Record<string, Array<{ label: string; handler: (n: Notification) => void }>> = {
  clarification_open: [
    { label: 'Answer', handler: (n) => navigateToTask(n.entity_id, 'clarifications') },
  ],
  review_submitted: [
    { label: 'Review', handler: (n) => navigateToTask(n.entity_id, 'reviews') },
  ],
  claim_stale: [
    { label: 'Release', handler: (n) => releaseTask(n.entity_id) },
  ],
  agent_verdict: [
    { label: 'Confirm', handler: (n) => navigateToTask(n.entity_id, 'reviews') },
  ],
};
```

### 5.4 Notification Type Icons

```ts
const NOTIFICATION_TYPE_ICONS: Record<string, LucideIcon> = {
  review_submitted: FileCheck,
  clarification_open: MessageCircleQuestion,
  clarification_answered: MessageCircleCheck,
  claim_expired: Clock,
  claim_stale: AlertTriangle,
  review_approved: CheckCircle,
  review_rejected: XCircle,
  review_needs_changes: AlertCircle,
  quality_gate_failed: ShieldX,
  agent_verdict: Bot,
  task_blocked: Lock,
  task_completed: CheckCheck,
  evidence_rejected: FileX,
};
```

---

## 6. Command Palette Extensions

### 6.1 Agent Commands

Add to command palette (cmdk):

```ts
// In the command palette component, add a new group:

const AGENT_COMMANDS = [
  {
    id: 'agent-center',
    label: 'Go to Agent Center',
    icon: Bot,
    action: () => router.navigate({ to: '/agents' }),
    shortcut: 'g a',
  },
  {
    id: 'release-stale-claims',
    label: 'Release all stale claims',
    icon: Clock,
    action: () => releaseAllStaleClaims(),
    category: 'workflow',
  },
  {
    id: 'answer-clarifications',
    label: 'Open clarification queue',
    icon: MessageCircle,
    action: () => router.navigate({ to: '/agents', search: { tab: 'clarifications' } }),
    category: 'workflow',
  },
  {
    id: 'review-queue',
    label: 'Open review queue',
    icon: CheckCircle,
    action: () => router.navigate({ to: '/agents', search: { tab: 'reviews' } }),
    category: 'workflow',
  },
];
```

### 6.2 Per-Task Quick Actions

When a task is selected or context is available:

```ts
const TASK_WORKFLOW_COMMANDS = [
  {
    id: 'claim-task',
    label: 'Claim this task',
    icon: Hand,
    action: () => claimTask(selectedTaskId),
    visible: () => !currentClaim,
  },
  {
    id: 'release-task',
    label: 'Release claim',
    icon: HandMetal,
    action: () => releaseTask(selectedTaskId),
    visible: () => currentClaim?.state === 'active',
  },
  {
    id: 'submit-for-review',
    label: 'Submit for review',
    icon: Send,
    action: () => submitForReview(selectedTaskId),
    visible: () => gatePassed,
  },
  {
    id: 'attach-evidence',
    label: 'Attach evidence',
    icon: Paperclip,
    action: () => openAttachEvidenceDialog(),
  },
];
```

---

## 7. Shared Components

### 7.1 New Components to Create

| Component | File | Purpose |
|-----------|------|---------|
| `ClaimInfoCard` | `agents/ClaimInfoCard.tsx` | Claim + heartbeat display |
| `StateTimeline` | `agents/StateTimeline.tsx` | Vertical state transition timeline |
| `ClarificationThread` | `agents/ClarificationThread.tsx` | Threaded Q&A with inline answer |
| `EvidenceCard` | `agents/EvidenceCard.tsx` | Evidence display with verification actions |
| `ReviewRoundSection` | `agents/ReviewRoundSection.tsx` | Review round with findings |
| `FindingCard` | `agents/FindingCard.tsx` | Individual finding display |
| `AgentCard` | `agents/AgentCard.tsx` | Agent summary card for grid view |
| `AgentGrid` | `agents/AgentGrid.tsx` | Grid layout for agent list |
| `HeartbeatIndicator` | `agents/HeartbeatIndicator.tsx` | Colored dot with pulse animation |
| `QualityGateProgress` | `agents/QualityGateProgress.tsx` | DoD pass/fail progress bar |
| `SendMessageDialog` | `agents/SendMessageDialog.tsx` | Dialog for sending message to agent |
| `LiveHeartbeatPanel` | `dashboard/LiveHeartbeatPanel.tsx` | Dashboard heartbeat status panel |

### 7.2 Reused Existing Components

| Component | From | Used In |
|-----------|------|---------|
| `AgentAvatar` | `ui/AgentAvatar.tsx` | AgentCard, ClaimInfoCard, TaskBoard |
| `AgentStatusBadge` | `ui/AgentStatusBadge.tsx` | AgentCard, AgentTable |
| `StatusBadge` | `ui/StatusBadge.tsx` | StateTimeline, BoardView |
| `ReviewVerdictCard` | `ui/ReviewVerdictCard.tsx` | Reviews Tab |
| `ClarificationBanner` | `ui/ClarificationBanner.tsx` | Clarifications Tab |
| `SearchInput` | `ui/SearchInput.tsx` | AgentToolbar |
| `EmptyState` | `ui/EmptyState.tsx` | All empty states |
| `ConfirmDialog` | `ui/ConfirmDialog.tsx` | Release, deactivate |
| `EntityFormDialog` | `forms/EntityFormDialog.tsx` | Attach evidence |
| `DataTablePagination` | `ui/DataTablePagination.tsx` | Agent Table |
| `Skeleton` | `ui/skeleton.tsx` | Loading states |
| `PageSkeleton` | `ui/PageSkeleton.tsx` | Agent Center loading |

---

## 8. State Management

### 8.1 TanStack Query Keys

```ts
// Query key hierarchy:
['agents']                                      // agent list
['agents', agentId]                             // single agent
['agents', agentId, 'metrics']                  // agent metrics (polling)
['agents', agentId, 'claims']                   // agent claim history
['agents', agentId, 'activity']                 // agent activity feed

['tasks', taskId, 'claims']                     // existing
['tasks', taskId, 'heartbeats']                 // existing
['tasks', taskId, 'clarifications']             // existing
['tasks', taskId, 'evidence']                   // existing
['tasks', taskId, 'review-rounds']              // existing
['tasks', taskId, 'review-rounds', roundId, 'findings']  // NEW

['project-tasks-claims', projectId]             // NEW: batch claims for board

['dashboard', 'attention']                      // existing
['notifications']                               // existing
['notifications', 'unread-count']               // existing
```

### 8.2 Polling Strategy

| Data | Interval | staleTime | When |
|------|---------|-----------|------|
| Agent metrics | 10s | 5s | Agent detail page |
| Heartbeats | 10s | 0 | Task detail (execution tab) |
| Attention dashboard | 30s | 15s | Dashboard page |
| Notifications | 30s | 15s | Always (badge count) |
| Agent list | 30s | 15s | Agent center page |
| Clarifications | 15s | 5s | Task detail (clarifications tab) |

### 8.3 Mutation → Invalidation Map

| Mutation | Invalidates |
|----------|-------------|
| `releaseTask(id)` | `[tasks, id, 'claims']`, `[tasks, id, 'heartbeats']`, `['dashboard', 'attention']`, `['project-tasks-claims', projectId]` |
| `answerClarification(id)` | `[tasks, taskId, 'clarifications']`, `['dashboard', 'attention']`, `['notifications']` |
| `verifyEvidence(id)` | `[tasks, taskId, 'evidence']` |
| `acceptEvidence(id)` | `[tasks, taskId, 'evidence']` |
| `rejectEvidence(id)` | `[tasks, taskId, 'evidence']` |
| `submitForReview(taskId)` | `[tasks, taskId, 'review-rounds']`, `['dashboard', 'attention']`, `['notifications']` |
| `submitReviewVerdict(roundId)` | `[tasks, taskId, 'review-rounds']`, `['dashboard', 'attention']`, `['notifications']` |
| `claimTask(taskId)` | `[tasks, taskId, 'claims']`, `['project-tasks-claims', projectId]` |
| `activateAgent(id)` | `['agents']`, `['agents', id]` |
| `deactivateAgent(id)` | `['agents']`, `['agents', id]` |

---

## 9. API Integration Map

### 9.1 New Endpoints Required

| Endpoint | Method | Purpose | Returns |
|----------|--------|---------|---------|
| `/api/v1/agents` | GET | List all agents with metrics | `AgentListResponse` |
| `/api/v1/agents/:id` | GET | Single agent detail | `AgentProfile & AgentMetrics` |
| `/api/v1/agents` | POST | Create agent | `AgentProfile` |
| `/api/v1/agents/:id` | PATCH | Update agent | `AgentProfile` |
| `/api/v1/agents/:id/activate` | POST | Activate agent | `{ ok: true }` |
| `/api/v1/agents/:id/deactivate` | POST | Deactivate agent | `{ ok: true }` |
| `/api/v1/agents/:id/claims` | GET | Agent claim history | `{ items: TaskClaim[] }` |
| `/api/v1/agents/:id/activity` | GET | Agent event feed | `{ items: AgentEvent[] }` |
| `/api/v1/projects/:id/claims` | GET | All active claims for project | `{ items: TaskClaim[] }` |
| `/api/v1/review-rounds/:id/findings` | GET | Findings for a review round | `{ items: ReviewFinding[] }` |
| `/api/v1/clarifications/:id/answer` | POST | Answer a clarification | `ClarificationRequest` |

### 9.2 Existing Endpoints Used

Already implemented, consumed by the new UI:

| Endpoint | Used By |
|----------|---------|
| `GET /tasks/:id/claims` | Execution tab, Board |
| `GET /tasks/:id/heartbeats` | Execution tab, HeartbeatIndicator |
| `GET /tasks/:id/clarifications` | Clarifications tab |
| `GET /tasks/:id/evidence` | Evidence tab |
| `GET /tasks/:id/review-rounds` | Reviews tab |
| `POST /tasks/:id/claim` | Board quick claim, Command palette |
| `POST /tasks/:id/release` | Execution tab, Board, Attention dashboard |
| `POST /evidence/:id/agent-verify` | Evidence tab |
| `POST /evidence/:id/human-accept` | Evidence tab |
| `POST /evidence/:id/reject` | Evidence tab |
| `POST /tasks/:id/submit-review` | Reviews tab |
| `POST /review-rounds/:id/verdict` | Reviews tab, Attention dashboard |
| `GET /dashboard/attention` | Attention dashboard |
| `GET /notifications` | Notification bell |
| `GET /agent/me` | Agent self-service |

---

## 10. Responsive Breakpoints

Follow existing Tailwind breakpoint convention:

| Breakpoint | Min Width | Name | Behavior |
|-----------|----------|------|----------|
| `sm` | 640px | Mobile landscape | Single column, collapsed sidebar |
| `md` | 768px | Tablet | 2 columns for grids |
| `lg` | 1024px | Desktop | Full layout, 3-4 column grids |
| `xl` | 1280px | Wide | Max-width container |

### 10.1 Sheet Width

Current: `w-full sm:max-w-[600px]`. Enhancement for new tabs:

```
Mobile:    Full width overlay
Tablet:    600px (current)
Desktop:   672px (increase by 72px for richer tab content)
```

Update `SheetContent`:

```tsx
<SheetContent className="w-full sm:max-w-[600px] lg:max-w-[672px] overflow-y-auto">
```

### 10.2 Agent Center Responsive

| Breakpoint | Agent Grid | Agent Table | Detail Tabs |
|-----------|-----------|-------------|-------------|
| < 640px | 1 col cards | Card list | Scrollable tabs |
| 640–1023px | 2 col cards | Table visible | Scrollable tabs |
| ≥ 1024px | 3 col cards | Table visible | All tabs visible |

### 10.3 Board View Responsive

Already handled: `grid-cols-1 sm:grid-cols-2 lg:grid-cols-4`. Enhancement adds agent info which is hidden on mobile:

```tsx
<div className="hidden sm:flex items-center gap-2 mt-2">
  <AgentAvatar ... />
  <span>...</span>
</div>
```

---

## 11. Accessibility

### 11.1 ARIA Labels

All interactive elements require ARIA labels:

```tsx
// Heartbeat indicator
<span
  role="status"
  aria-label={`Agent heartbeat: ${heartbeatStatus}`}
  className={`h-2 w-2 rounded-full ${dotColor} ${pulse ? 'animate-heartbeat-pulse' : ''}`}
/>

// Evidence verification badge
<span
  role="status"
  aria-label={`Evidence verification: ${verification_state}`}
  className={...}
>
  {label}
</span>

// Quality gate progress
<div
  role="progressbar"
  aria-valuenow={passedCount}
  aria-valuemin={0}
  aria-valuemax={totalCount}
  aria-label={`Quality gate: ${passedCount} of ${totalCount} items passed`}
/>

// State timeline
<ol role="list" aria-label="Task state transitions">
  <li aria-current={isCurrent ? 'step' : undefined}>
    <span aria-label={`${state} at ${timestamp}`}>...</span>
  </li>
</ol>

// Send message dialog
<Textarea aria-label="Message to agent" placeholder="..." />
```

### 11.2 Keyboard Navigation

| Element | Keys |
|---------|------|
| Agent cards (grid) | Tab between cards, Enter to open detail |
| Agent table rows | Arrow Up/Down to navigate, Enter to open |
| Evidence card actions | Tab between Verify/Reject/View |
| Review verdict buttons | Tab between Accept/Reject |
| Clarification answer | Enter to send (Ctrl+Enter for multiline) |
| Tab triggers | Arrow Left/Right to switch tabs |
| Board cards | Tab between cards in a column |

### 11.3 Screen Reader

- All state changes announced via `aria-live="polite"` on heartbeat status
- Tab badge counts announced: `aria-label="Clarifications (2 open)"`
- Toast announcements handled by Sonner (already `aria-live`)
- Loading states: `aria-busy="true"` on containers during refetch

### 11.4 Focus Management

- Sheet open: focus moves to SheetContent (handled by shadcn)
- Dialog open: focus trapped in dialog (handled by Radix)
- Tab switch: focus stays on tab trigger
- Quick action completion: focus returns to triggering element

---

## 12. Animation & Motion

### 12.1 Existing Animations (reuse)

From `constants.ts` and existing CSS:

| Animation | Class | Usage |
|-----------|-------|-------|
| Heartbeat pulse | `animate-heartbeat-pulse` | AgentAvatar dot, AgentStatusBadge |
| Badge pop | `animate-badge-pop` | Notification badge |
| Fade in up | `animate-fade-in-up` | Dashboard page entrance |
| Stagger | `animate-stagger` | Stat cards cascade |

### 12.2 New Animations

**State Timeline Entry:**

```css
@keyframes timeline-dot-enter {
  from { transform: scale(0); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}

.animate-timeline-dot {
  animation: timeline-dot-enter 0.3s ease-out;
}
```

**Evidence Card Enter:**

```css
@keyframes slide-in-right {
  from { transform: translateX(8px); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

.animate-slide-in-right {
  animation: slide-in-right 0.2s ease-out;
}
```

**Progress Bar Smooth:**

```css
.progress-bar-fill {
  transition: width 0.5s ease-in-out;
}
```

**Clarification Thread Expand:**

```css
.animate-expand {
  animation: expand 0.2s ease-out;
  overflow: hidden;
}

@keyframes expand {
  from { max-height: 0; opacity: 0; }
  to { max-height: 500px; opacity: 1; }
}
```

### 12.3 Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  .animate-heartbeat-pulse,
  .animate-badge-pop,
  .animate-timeline-dot,
  .animate-slide-in-right,
  .animate-expand {
    animation: none;
  }
  .progress-bar-fill {
    transition: none;
  }
}
```

---

## 13. Error & Empty States

### 13.1 Error States

All follow existing `ErrorState` pattern:

```tsx
// Agent Center load failure
<ErrorState
  icon={Bot}
  title="Failed to load agents"
  description="Could not connect to the agent service."
  action={{ label: 'Retry', onClick: () => refetch() }}
/>

// Task detail sub-tab load failure
<div className="rounded-lg border border-destructive/20 bg-destructive/5 p-4">
  <p className="text-sm text-destructive">Failed to load evidence.</p>
  <Button variant="ghost" size="sm" onClick={refetch} className="mt-2">
    Retry
  </Button>
</div>
```

### 13.2 Empty States

| Context | Icon | Title | Description |
|---------|------|-------|-------------|
| Agent Center (no agents) | `Bot` | "No agents configured" | "Create an agent to start automated task execution." |
| Agent claims (none) | `Hand` | "No claims yet" | "This agent hasn't claimed any tasks." |
| Task execution (no claim) | `Bot` | "No agent claims" | "This task hasn't been claimed by an agent." |
| Clarifications (none) | `MessageCircle` | "No clarifications" | "No questions have been asked about this task." |
| Evidence (none) | `FileText` | "No evidence attached" | "Attach evidence to support task completion." |
| Reviews (none) | `CheckCircle` | "No reviews yet" | "Submit for review to start the quality review process." |
| Findings (none in round) | `ShieldCheck` | "No findings" | "This review round has no findings." |
| Board (no claimed tasks) | — | (no special state) | Show board normally without agent info |

### 13.3 Inline Errors

For mutation failures, use toast + keep dialog/form open:

```ts
try {
  await releaseTask.mutateAsync(taskId);
  showToast.success('Claim released');
} catch (error) {
  showToast.error('Failed to release claim');
  // Dialog stays open, form state preserved
}
```

---

## 14. Dark Mode

All new components follow the existing dark mode pattern:

### 14.1 Rules

- Use CSS custom properties and Tailwind `dark:` variants (see `constants.ts`)
- Never use hardcoded colors — always map through `STATUS_COLORS`, `AGENT_STATUS_COLORS`, `VERIFICATION_STYLES`, etc.
- Heartbeat dot colors:
  - Green: `bg-emerald-500` (works in both modes)
  - Yellow: `bg-amber-500`
  - Red: `bg-red-500`
- Card borders: `border-border` (CSS variable)
- Card backgrounds: `bg-card` (CSS variable)
- Hover states: `hover:bg-muted/50`

### 14.2 Component-Specific

| Component | Light Mode | Dark Mode |
|-----------|-----------|-----------|
| ClaimInfoCard stale bg | `bg-amber-500/5` | `dark:bg-amber-500/5` (same) |
| Evidence rejected bg | `bg-red-500/10` | `dark:bg-red-500/10` (same) |
| Finding severity badges | Per-severity `bg-X-500/10` | Same (opacity-based) |
| State timeline line | `bg-border` | `bg-border` (same) |

All colors from `constants.ts` already have dark variants. New components must follow the same pattern.

---

## Implementation Priority

| Phase | Scope | Components | Files |
|-------|-------|------------|-------|
| **P1** | Enhanced Execution tab | ClaimInfoCard, HeartbeatIndicator, StateTimeline | `TaskDetailSheet.tsx`, `agents/ClaimInfoCard.tsx`, `agents/StateTimeline.tsx` |
| **P2** | Dedicated Clarifications tab | ClarificationThread | `agents/ClarificationThread.tsx`, update `TaskDetailSheet.tsx` |
| **P3** | Evidence tab | EvidenceCard, AttachEvidenceDialog | `agents/EvidenceCard.tsx`, update `TaskDetailSheet.tsx` |
| **P4** | Reviews tab | ReviewRoundSection, FindingCard | `agents/ReviewRoundSection.tsx`, `agents/FindingCard.tsx`, update `TaskDetailSheet.tsx` |
| **P5** | Board enhancements | DraggableTaskCard update, batch claims API | `BoardView.tsx`, new API endpoint |
| **P6** | Attention dashboard | Inline actions on all sections | `AttentionCards.tsx` |
| **P7** | Agent Center page | Full page + routing | `AgentCenterPage.tsx`, `AgentCard.tsx`, `router.tsx`, `constants.ts` |
| **P8** | Notifications enhancement | Action buttons, type icons | `NotificationBell.tsx`, `toast.ts` |
| **P9** | Command palette | Agent commands | Command palette component |
