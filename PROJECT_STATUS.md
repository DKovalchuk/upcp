# PROJECT_STATUS

Updated: 2026-07-24
Milestone: M6+ (UI Polish)
Current Task: None
Next Task: TBD
Blockers: none

## Last Result

TASK-0060 completed: Git Integration UI.

- Git types, API functions, React hooks for git endpoints
- GitIntegrationPage with providers, branches, commits tables
- Git tab added to ProjectDetail, route /projects/:id/git
- 5 new tests, 140 total passing

TASK-0059 completed: Drag-and-drop for Board View.

- @dnd-kit/core for draggable cards + droppable columns
- DragOverlay shows card being dragged
- Column highlights on drag-over
- Dropping card on different column updates task status
- 2 new tests, 135 total passing

TASK-0058 completed: Command Palette (Cmd+K).

- Installed cmdk, created shadcn Command components
- CommandPalette with navigation + project-specific commands
- Global Cmd+K / Ctrl+K shortcut, TopBar search trigger
- Fuzzy search, keyboard navigation
- 7 new tests, 133 total passing

TASK-0056 completed: Pagination wired into all list pages.

- DataTablePagination integrated into ProjectList, DeliveryPage, AuditPage, ReportsPage
- useUrlPagination hook manages page/pageSize URL search params
- All API hooks pass offset/limit to backend
- Build passes, 126 tests passing

TASK-0057 completed: Board/Kanban view for Delivery page.

- BoardView component with 4 status columns (Backlog, In Progress, Review, Done)
- View toggle (List / Board) in DeliveryPage header
- Tasks fetched via useQueries for all features in parallel
- Click status badge to cycle task status
- Click task card to open TaskDetailSheet
- Search filter works in board view
- 7 new tests, 126 total passing

### Phase 0 (Foundation) — DONE
- TASK-0043: Fix type mismatches + sidebar navigation
- TASK-0044: Skeleton loading + toast system
- TASK-0056: Pagination component + URL sync (integrated into all list pages)

### Phase 1 (Core Pages) — DONE
- TASK-0045: Dashboard page with stats cards, recent projects, activity feed
- TASK-0046: Project detail page with tabbed layout (Overview, Structure, Delivery, Quality, Audit, Settings)
- TASK-0047: Create/edit form dialogs (EntityFormDialog for all entities)
- TASK-0048: Structure page (components + modules with expand)
- TASK-0049: Delivery page (features + task tables with search)
- TASK-0050: Task detail sheet (slide-over with tabs: Details, AC, DoD, Subtasks)

### Phase 2 (Extended) — DONE
- TASK-0051: Quality page (stats cards, progress bars, quality gate)
- TASK-0052: Audit timeline page (filterable timeline)
- TASK-0053: Reports page (list, generate daily, export markdown)
- TASK-0054: Health page (backend status with auto-refresh)

### Phase 3 (Polish) — DONE
- TASK-0055: Dark mode toggle (Sun/Moon/Monitor via next-themes)

### Key Decisions (ADRs)
- DEC-0006: Use URL pathname parsing instead of useParams for sub-routes
- DEC-0007: Sheet component for task detail (not a route)
- DEC-0008: Tabbed layout for project detail (URL-synced tabs)
- DEC-0009: EntityFormDialog pattern for all CRUD forms
- DEC-0010: 6-color palette with CSS variables for dark mode
- DEC-0011: sonner for toast notifications
- DEC-0012: PageSkeleton for loading states
- DEC-0013: URL-synced pagination with search params
- DEC-0014: Design system components (StatusBadge, PriorityDot, EmptyState, ErrorState, ConfirmDialog)

### Test Coverage
- Frontend: 119 tests across 19 test files, all passing
- Backend: 189 tests, 90% coverage

## M5 Completed (Previous)
- MCP server scaffold with JSON-RPC endpoint
- MCP tools: project_list, project_get, task_list, task_get, feature_list, feature_get
- MCP write tools: feature_update, task_update (TASK-0042)
- Context pack generator
- CLI with project, task, status commands
- Dashboard Stats, Quality Stats, Audit List API endpoints

## Remaining Work

### Future Backlog (from SPEC-0013 §6)
- Global search (needs backend search endpoint)
- Notifications system
- Auth/RBAC UI

## Important Notes

- Use non-standard Docker ports.
- Use TDD.
- Keep context small.
- Read `AGENTS.md` before any task.
- All work via feature branches → merge to `develop`.
