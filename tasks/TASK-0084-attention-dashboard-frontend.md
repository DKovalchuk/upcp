# TASK-0084 Attention Dashboard Frontend

Status: DONE (2026-10-31 — все AC сверены; deviations: двухколоночный layout → SPEC-0025 responsive rows, клик → drill-down навигация (не TaskDetailSheet, e2e-pinned); верификация в TASK-0160)
Milestone: M11
Spec: SPEC-0016
Depends: TASK-0083

## Goal

Action-oriented dashboard UI.

## Acceptance Criteria

- Summary cards with counts.
- Two-column layout with attention sections.
- Click items → task detail sheet.
- Auto-refresh via TanStack Query.
- Empty states for all sections.
