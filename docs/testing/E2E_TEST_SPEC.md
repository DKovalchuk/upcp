# E2E Test Specification — UPCP

> Comprehensive end-to-end test suite for Universal Project Control Plane.
> Framework: Playwright (TypeScript), base URL: `http://localhost:5173`.
> All tests use route-intercepted mock data via `fixtures/helpers.ts`.

## Conventions

### Test File Naming

`frontend/e2e/<suite-name>.spec.ts`

### Shared Helpers

All tests use `gotoPage(page, path)` from `fixtures/helpers.ts`, which:

1. Injects auth tokens via `addInitScript` (before page load)
2. Intercepts all known API routes with mock responses
3. Navigates to the target path
4. Waits for `domcontentloaded` + 500ms hydration

### Mock Data Patterns

Tests that need specific data states override individual routes:

```ts
await page.route('**/api/v1/tasks/task-1', (route) =>
  route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(customTask) })
);
```

Tests that need API errors override with error status codes:

```ts
await page.route('**/api/v1/projects', (route) =>
  route.fulfill({ status: 500, body: JSON.stringify({ detail: 'Internal Server Error' }) })
);
```

### Authentication Modes

| Mode | Method |
|------|--------|
| Authenticated | `gotoPage(page, path)` — injects tokens via `addInitScript` |
| Unauthenticated | `page.goto(path)` — no token injection, triggers redirect to `/login` |
| Setup-needed | Override `**/auth/me` to return 401, mock setup endpoint |

### Assertion Patterns

- `toBeVisible()` — element exists and is visible
- `toHaveURL(/pattern/)` — URL matches regex
- `toHaveAttribute(name, value)` — attribute check
- `toHaveText(text)` — exact text match
- `toBeFocused()` — element has focus

---

## Suite 1: Auth Flow

**File:** `frontend/e2e/auth.spec.ts` (expand existing)

**Description:** Tests first-run setup, login, logout, token refresh, protected route redirect, password change, and session expiry.

### Preconditions

- App loads at `http://localhost:5173`
- Backend mock or real at configured API URL

### Test Cases

#### 1.1 First-Run Setup — Happy Path

**Preconditions:** `**/auth/me` returns 401 (no user exists), `**/auth/setup` mock available.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/` | Redirected to `/setup` |
| 2 | Verify page has heading "Welcome to UPCP" | Visible |
| 3 | Verify page has subtitle "Create your admin account" | Visible |
| 4 | Fill Display Name field with `Admin` | Field accepts input |
| 5 | Fill Email field with `admin@upcp.dev` | Field accepts input |
| 6 | Fill Password field with `SecurePass123!` | Field accepts input (type=password) |
| 7 | Verify "Minimum 8 characters" hint | Visible below password |
| 8 | Click "Create account" button | Button is enabled |
| 9 | Wait for API call to `**/auth/setup` | Returns 201 with tokens + user |
| 10 | Verify redirect to `/` (dashboard) | URL is `/` |

**Mock Setup:**

```ts
await page.route('**/auth/setup', (route) =>
  route.fulfill({ status: 201, body: JSON.stringify({ ...MOCK_TOKENS, user: MOCK_USER }) })
);
```

**Edge Cases:**
- **1.1a — Setup already completed:** `**/auth/setup` returns 409. Error message "Setup has already been completed" displayed.
- **1.1b — Password too short (< 8 chars):** HTML validation prevents submit. Button disabled or form shows native validation.
- **1.1c — Empty required fields:** HTML `required` attribute prevents submit. Native validation fires.

#### 1.2 Login — Happy Path

**Preconditions:** User exists, `/login` page loads.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/login` | Login page renders |
| 2 | Verify email input exists (type=email) | Visible |
| 3 | Verify password input exists (type=password) | Visible |
| 4 | Verify "Sign in" button exists | Visible, enabled |
| 5 | Fill email: `admin@upcp.dev` | Field accepts input |
| 6 | Fill password: `SecurePass123!` | Field accepts input |
| 7 | Click "Sign in" | Button triggers API call |
| 8 | Verify `**/auth/login` called with correct body | Request body has email + password |
| 9 | Verify tokens stored in localStorage | `upcp_access_token` and `upcp_refresh_token` set |
| 10 | Verify redirect to `/` | URL is `/` |

**Edge Cases:**
- **1.2a — Invalid credentials:** `**/auth/login` returns 401. Error text matching `/invalid|incorrect|error/i` visible.
- **1.2b — Account locked (423):** `**/auth/login` returns 423. Error about "temporarily locked" displayed.
- **1.2c — Network error:** `**/auth/login` returns network failure. Error message displayed.

#### 1.3 Logout

**Preconditions:** User is authenticated (tokens in localStorage).

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/` (authenticated) | Dashboard loads |
| 2 | Open user avatar menu in topbar | Menu appears |
| 3 | Click "Logout" or equivalent | Logout action fires |
| 4 | Verify tokens removed from localStorage | `upcp_access_token` is null |
| 5 | Verify redirect to `/login` | URL contains `/login` |

**Note:** If no visible logout button exists in the UI, test the auth context `logout()` function directly via `page.evaluate`.

#### 1.4 Token Refresh

**Preconditions:** Access token expired, refresh token valid.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Set expired access token in localStorage | Done via `addInitScript` |
| 2 | Mock `**/auth/me` to return 401 first call, then 200 | Sequential response |
| 3 | Mock `**/auth/refresh` to return new tokens | Returns 200 |
| 4 | Navigate to `/` | App loads after refresh |
| 5 | Verify new tokens stored | localStorage updated |

**Implementation Note:** Test via intercept sequence:
```ts
let meCallCount = 0;
await page.route('**/auth/me', (route) => {
  meCallCount++;
  if (meCallCount === 1) return route.fulfill({ status: 401, body: '{"detail":"expired"}' });
  return route.fulfill({ status: 200, body: JSON.stringify(MOCK_USER) });
});
```

#### 1.5 Protected Route Redirect

**Preconditions:** No tokens in localStorage.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/` | Redirected to `/login` |
| 2 | Navigate to `/projects` | Redirected to `/login` |
| 3 | Navigate to `/projects/proj-1` | Redirected to `/login` |
| 4 | Navigate to `/projects/proj-1/delivery` | Redirected to `/login` |
| 5 | Navigate to `/settings` | Redirected to `/login` |
| 6 | Navigate to `/reports` | Redirected to `/login` |

**Edge Case:** `/health` is NOT protected (no AuthGuard). Should load without redirect.

#### 1.6 Password Change

**Preconditions:** User is authenticated. Settings page or profile has password change form.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/settings` | Settings page loads |
| 2 | Find password change section | Inputs for current + new password |
| 3 | Fill current password | Field accepts input |
| 4 | Fill new password (8+ chars) | Field accepts input |
| 5 | Submit | API call to `**/auth/password/change` |
| 6 | Mock success (200) | Success message or feedback |

**Edge Cases:**
- **1.6a — Wrong current password:** `**/auth/password/change` returns 400. Error "Current password is incorrect" displayed.
- **1.6b — New password too short:** HTML validation prevents submit.

#### 1.7 Session Expiry During Navigation

**Preconditions:** User starts authenticated, then tokens expire mid-session.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/` (authenticated) | Dashboard loads |
| 2 | Mock `**/auth/me` to return 401 | Token now invalid |
| 3 | Mock `**/auth/refresh` to return 401 | Refresh also fails |
| 4 | Trigger a navigation or API call | App detects expired session |
| 5 | Verify redirect to `/login` | URL contains `/login` |

#### 1.8 Password Visibility Toggle

**Preconditions:** Login or setup page loaded.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/login` | Page loads |
| 2 | Find password input | `type="password"` |
| 3 | Click "Show password" button (aria-label) | Input changes to `type="text"` |
| 4 | Verify "Hide password" button visible | aria-label changes |
| 5 | Click "Hide password" button | Input returns to `type="password"` |

**Accessibility:** Toggle must be keyboard accessible (Tab + Enter).

---

## Suite 2: Project CRUD

**File:** `frontend/e2e/projects.spec.ts` (expand existing)

**Description:** Tests project creation, editing, deletion, list pagination, detail tabs, search/filter.

### Preconditions

- User authenticated
- Mock projects API returns `MOCK_PROJECTS` (2 items)

### Test Cases

#### 2.1 Project List — Renders

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/projects` | Project list page loads |
| 2 | Verify "UPCP Core" project visible | Text present |
| 3 | Verify "Mobile App" project visible | Text present |
| 4 | Verify project count matches API response | 2 projects shown |

#### 2.2 Project List — Pagination

**Mock:** Return 25 projects with `total: 25, limit: 20`.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/projects` | Page loads with first 20 items |
| 2 | Verify pagination controls visible | "Next" or page numbers shown |
| 3 | Click next page | API called with `offset=20` |
| 4 | Verify remaining 5 items shown | 5 items on page 2 |

#### 2.3 Project List — Empty State

**Mock:** `**/api/v1/projects` returns `{ items: [], total: 0 }`.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/projects` | Page loads |
| 2 | Verify empty state shown | "No projects" or similar message |
| 3 | Verify "Create Project" CTA visible | Button or link present |

#### 2.4 Project List — Search/Filter

**Mock:** `**/api/v1/projects?search=Mobile` returns filtered results.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/projects` | Full list loads |
| 2 | Type "Mobile" in search input | Search fires |
| 3 | Verify only "Mobile App" shown | Filtered result |

#### 2.5 Project Detail — Overview Tab

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/projects/proj-1` | Detail page loads |
| 2 | Verify "Project Details" heading | Visible |
| 3 | Verify Name field shows "UPCP Core" | Text present |
| 4 | Verify Slug field shows "upcp-core" | Text present |
| 5 | Verify "Created" and "Updated" dates | Both visible |
| 6 | Verify "Overview" tab is active | Selected state |

#### 2.6 Project Detail — Tab Navigation

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/projects/proj-1` | Detail loads |
| 2 | Click "Structure" tab | URL changes to `/projects/proj-1/structure` |
| 3 | Click "Delivery" tab | URL changes to `/projects/proj-1/delivery` |
| 4 | Click "Quality" tab | URL changes to `/projects/proj-1/quality` |
| 5 | Click "Audit" tab | URL changes to `/projects/proj-1/audit` |
| 6 | Click "Overview" tab | URL returns to `/projects/proj-1` |

**Accessibility:** Tabs navigable via ArrowRight/ArrowLeft keys.

#### 2.7 Project Create

**Mock:** `**/api/v1/projects` POST returns 201 with new project.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/projects` | List loads |
| 2 | Click "New Project" button (or command palette action) | Create dialog opens |
| 3 | Fill name: "New Project" | Field accepts input |
| 4 | Fill slug: "new-project" | Field accepts input |
| 5 | Fill description: "Test project" | Field accepts input |
| 6 | Submit form | POST to `**/api/v1/projects` |
| 7 | Verify success toast | Toast shown |
| 8 | Verify dialog closed | Dialog not visible |

**Edge Cases:**
- **2.7a — Duplicate slug:** API returns 409. Error displayed in dialog.
- **2.7b — Empty name:** Validation prevents submit.

#### 2.8 Project Edit

**Mock:** `**/api/v1/projects/proj-1` PATCH returns 200.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/projects/proj-1` | Detail loads |
| 2 | Click edit button (pencil icon) | Edit dialog opens |
| 3 | Modify name to "UPCP Core Updated" | Field updated |
| 4 | Submit form | PATCH to `**/api/v1/projects/proj-1` |
| 5 | Verify dialog closes | Dialog not visible |
| 6 | Verify updated name shown | "UPCP Core Updated" visible |

#### 2.9 Project Delete

**Mock:** `**/api/v1/projects/proj-1` DELETE returns 204.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/projects/proj-1` | Detail loads |
| 2 | Click delete button | Confirm dialog opens |
| 3 | Verify dialog text: "Are you sure?" | Dialog visible |
| 4 | Click "Delete" confirm button | DELETE to `**/api/v1/projects/proj-1` |
| 5 | Verify redirect to `/projects` list | URL is `/projects` |

**Edge Case:** Cancel button in confirm dialog — project not deleted.

---

## Suite 3: Structure Management

**File:** `frontend/e2e/structure.spec.ts` (NEW)

**Description:** Tests component and module CRUD, expand/collapse, nested hierarchy.

### Preconditions

- User authenticated, on project detail page
- Mock components API returns `MOCK_COMPONENTS`

### Test Cases

#### 3.1 Structure Page — Renders Components

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/projects/proj-1/structure` | Structure page loads |
| 2 | Verify "Structure" heading visible | Text present |
| 3 | Verify "Backend API" component card | Visible with name + slug |
| 4 | Verify "Component" create button | "+" or "Component" button visible |

#### 3.2 Component Expand/Collapse

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/projects/proj-1/structure` | Page loads |
| 2 | Click on "Backend API" component card header | Expands to show modules section |
| 3 | Verify "Modules" label visible | Text present |
| 4 | Verify "Module" create button visible | "+" or "Module" button |
| 5 | Click component header again | Collapses modules section |
| 6 | Verify modules section hidden | "Modules" not visible |

#### 3.3 Component Create

**Mock:** `**/api/v1/projects/proj-1/components` POST returns 201.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/projects/proj-1/structure` | Page loads |
| 2 | Click "Component" button | Create dialog opens with title "Create Component" |
| 3 | Verify form fields: Name, Slug, Description, Status | All visible |
| 4 | Fill name: "Frontend App" | Field accepts input |
| 5 | Fill slug: "frontend-app" | Field accepts input |
| 6 | Fill description: "React SPA" | Field accepts input |
| 7 | Submit | POST fires |
| 8 | Verify success toast "Component created" | Toast visible |
| 9 | Verify dialog closed | Not visible |

**Edge Cases:**
- **3.3a — Empty name:** Validation prevents submit.
- **3.3b — Duplicate slug:** API returns 409.

#### 3.4 Component Delete

**Mock:** `**/api/v1/components/comp-1` DELETE returns 204.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/projects/proj-1/structure` | Page loads |
| 2 | Click trash icon on "Backend API" card | Confirm dialog opens |
| 3 | Verify title: "Delete Component" | Visible |
| 4 | Click "Delete" | DELETE fires |
| 5 | Verify success toast | Toast visible |
| 6 | Verify component removed from list | "Backend API" not visible |

#### 3.5 Module Create (Inside Expanded Component)

**Mock:** `**/api/v1/components/comp-1/modules` POST returns 201.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/projects/proj-1/structure` | Page loads |
| 2 | Click "Backend API" to expand | Modules section visible |
| 3 | Click "Module" button | Create dialog opens with title "Create Module" |
| 4 | Fill name: "Auth Module" | Field accepts input |
| 5 | Fill slug: "auth-module" | Field accepts input |
| 6 | Submit | POST fires |
| 7 | Verify success toast "Module created" | Toast visible |
| 8 | Verify new module in table | "Auth Module" visible in modules table |

#### 3.6 Module Delete

**Mock:** `**/api/v1/modules/mod-1` DELETE returns 204.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Expand component with modules | Modules table visible |
| 2 | Click trash icon on module row | Confirm dialog opens |
| 3 | Verify title: "Delete Module" | Visible |
| 4 | Click "Delete" | DELETE fires |
| 5 | Verify module removed from table | Module row gone |

#### 3.7 Empty Structure State

**Mock:** `**/api/v1/projects/proj-1/components` returns `{ items: [], total: 0 }`.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/projects/proj-1/structure` | Page loads |
| 2 | Verify empty state icon (Boxes) | Visible |
| 3 | Verify "No components yet" text | Visible |
| 4 | Verify "Create Component" CTA button | Visible and clickable |

---

## Suite 4: Delivery Management

**File:** `frontend/e2e/delivery.spec.ts` (expand existing)

**Description:** Tests feature CRUD, task CRUD, subtask CRUD, task detail sheet, board/list toggle, search/filter.

### Preconditions

- User authenticated, on delivery page
- Mock features API returns `MOCK_FEATURES`, tasks API returns `MOCK_TASKS`

### Test Cases

#### 4.1 Delivery Page — List View Renders

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/projects/proj-1/delivery` | Delivery page loads |
| 2 | Verify "Delivery" heading | Visible |
| 3 | Verify "Authentication" feature section | Visible with task count |
| 4 | Verify "Agent Workflow" feature section | Visible |
| 5 | Verify "Feature" create button | Visible |

#### 4.2 Feature Section — Expand/Collapse

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/projects/proj-1/delivery` | Page loads |
| 2 | Click "Authentication" feature header | Expands to show tasks table |
| 3 | Verify tasks table visible | Table with Title, Status, Updated columns |
| 4 | Verify task rows: "Implement JWT token service", etc. | Multiple rows visible |
| 5 | Click feature header again | Tasks table collapses |

#### 4.3 Feature Create

**Mock:** `**/api/v1/projects/proj-1/features` POST returns 201.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/projects/proj-1/delivery` | Page loads |
| 2 | Click "Feature" button | Create dialog opens: "Create Feature" |
| 3 | Fill name: "Notifications" | Field accepts input |
| 4 | Fill slug: "notifications" | Field accepts input |
| 5 | Fill description: "Push notification system" | Field accepts input |
| 6 | Submit | POST fires |
| 7 | Verify toast "Feature created" | Visible |
| 8 | Verify dialog closed | Not visible |

#### 4.4 Feature Delete

**Mock:** `**/api/v1/features/feat-1` DELETE returns 204.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/projects/proj-1/delivery` | Page loads |
| 2 | Click trash icon on "Authentication" | Confirm dialog: "Delete Feature" |
| 3 | Click "Delete" | DELETE fires |
| 4 | Verify toast "Feature deleted" | Visible |
| 5 | Verify feature section gone | "Authentication" not visible |

#### 4.5 Task Create (Inside Expanded Feature)

**Mock:** `**/api/v1/features/feat-1/tasks` POST returns 201.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Expand "Authentication" feature | Tasks table visible |
| 2 | Click "Task" button | Create dialog: "Create Task" |
| 3 | Fill title: "Add password reset" | Field accepts input |
| 4 | Fill description: "Implement password reset flow" | Field accepts input |
| 5 | Fill priority: `1` | Field accepts input |
| 6 | Submit | POST fires |
| 7 | Verify toast "Task created" | Visible |
| 8 | Verify new task in table | "Add password reset" visible |

#### 4.6 Task Detail Sheet — Opens

| Step | Action | Expected |
|------|--------|----------|
| 1 | Expand feature with tasks | Table visible |
| 2 | Click on task row "Implement JWT token service" | TaskDetailSheet opens |
| 3 | Verify sheet title: "Implement JWT token service" | Visible in sheet header |
| 4 | Verify status badge | Shows "Done" status |
| 5 | Verify priority badge | Shows "P0" |
| 6 | Verify "Created" and "Updated" dates | Both visible |

#### 4.7 Task Detail Sheet — Tabs

| Step | Action | Expected |
|------|--------|----------|
| 1 | Open task detail sheet for task-1 | Sheet visible |
| 2 | Verify tabs: Details, Execution, AC, DoD, Subtasks | All 5 visible |
| 3 | Click "Details" tab | Task description shown |
| 4 | Click "Execution" tab | Execution section loads (claims, heartbeats, clarifications, evidence, reviews) |
| 5 | Click "AC (0)" tab | Acceptance criteria section with add input |
| 6 | Click "DoD (0)" tab | DoD section with add input |
| 7 | Click "Subtasks (0)" tab | Subtasks section with add input |

#### 4.8 Task Detail Sheet — Add Acceptance Criterion

**Mock:** `**/api/v1/tasks/task-1/acceptance-criteria` POST returns 201.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Open task detail, go to "AC" tab | AC section visible |
| 2 | Verify empty state: "No acceptance criteria yet." | Text visible |
| 3 | Type "User can login with valid credentials" in input | Field accepts input |
| 4 | Click "+" button (or press Enter) | POST fires |
| 5 | Verify new AC in list | Text visible in list |

#### 4.9 Task Detail Sheet — Add DoD Item

**Mock:** `**/api/v1/tasks/task-1/dod-items` POST returns 201.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Open task detail, go to "DoD" tab | DoD section visible |
| 2 | Type "Tests pass" in input | Field accepts input |
| 3 | Click "+" button | POST fires |
| 4 | Verify new DoD item in list | "Tests pass" visible |

#### 4.10 Task Detail Sheet — Add Subtask

**Mock:** `**/api/v1/tasks/task-1/subtasks` POST returns 201.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Open task detail, go to "Subtasks" tab | Subtasks section visible |
| 2 | Type "Write unit tests" in input | Field accepts input |
| 3 | Click "+" button | POST fires |
| 4 | Verify new subtask with status badge | Row visible |

#### 4.11 Task Detail Sheet — Status Change

| Step | Action | Expected |
|------|--------|----------|
| 1 | Open task detail, "Details" tab | Status select visible |
| 2 | Open status dropdown | Options: Backlog, In Progress, Review, Done |
| 3 | Select "In Progress" | PATCH fires to update task status |
| 4 | Verify status badge updates | Shows new status |

#### 4.12 Task Detail Sheet — Delete

**Mock:** `**/api/v1/tasks/task-1` DELETE returns 204.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Open task detail sheet | Sheet visible |
| 2 | Click trash icon in header | Confirm dialog: "Delete Task" |
| 3 | Verify destructive variant | "Delete" button styled as destructive |
| 4 | Click "Delete" | DELETE fires, sheet closes |

#### 4.13 Board View — Toggle

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/projects/proj-1/delivery` | List view loads |
| 2 | Click "Board view" button (LayoutGrid icon) | View switches to board |
| 3 | Verify board columns: Backlog, In Progress, Review, Done | All 4 visible |
| 4 | Click "List view" button (List icon) | View switches back to list |
| 5 | Verify feature sections visible again | List layout restored |

#### 4.14 Board View — Column Content

| Step | Action | Expected |
|------|--------|----------|
| 1 | Switch to board view | Board loads |
| 2 | Verify "Backlog" column has tasks | Task cards visible |
| 3 | Verify "In Progress" column has tasks | Task cards visible |
| 4 | Verify task cards show title + priority dot | Content present |

#### 4.15 Board View — Mobile Responsive

| Step | Action | Expected |
|------|--------|----------|
| 1 | Set viewport to 375x667 | Mobile viewport |
| 2 | Navigate to delivery, switch to board | Board loads |
| 3 | Verify columns still render (stacked) | At minimum "Backlog" visible |

#### 4.16 Delivery Search/Filter

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/projects/proj-1/delivery` | Page loads |
| 2 | Type "JWT" in search input | Filter fires |
| 3 | Expand feature | Only matching tasks shown |
| 4 | Clear search | All tasks visible again |

#### 4.17 Subtask CRUD — Update and Delete

| Step | Action | Expected |
|------|--------|----------|
| 1 | Open task detail, Subtasks tab, add a subtask | Subtask appears |
| 2 | (If UI supports) Click subtask to edit status | Status changes |
| 3 | (If UI supports) Delete subtask | Subtask removed |

---

## Suite 5: Agent Workflow

**File:** `frontend/e2e/agent-workflow.spec.ts` (NEW)

**Description:** Tests the agent task lifecycle: claim, heartbeat, release, clarification, progress updates, agent inbox. These tests verify the Execution tab in TaskDetailSheet and the Active Agents dashboard section.

### Preconditions

- User authenticated
- Mock workflow API endpoints available
- Agent auth via `X-Agent-Id` header (mock in route handlers)

### Test Cases

#### 5.1 Task Claim — Display in Execution Tab

**Mock:** `**/api/v1/tasks/task-1/claims` returns active claim.

```ts
await page.route('**/api/v1/tasks/task-1/claims', (route) =>
  route.fulfill({ status: 200, body: JSON.stringify({
    items: [{
      id: 'claim-1',
      task_id: 'task-1',
      agent_id: 'backend-developer',
      state: 'active',
      claimed_at: new Date(Date.now() - 300000).toISOString(),
      released_at: null,
      last_heartbeat_at: new Date(Date.now() - 60000).toISOString(),
      context_snapshot: 'Implementing JWT service',
    }]
  })})
);
```

| Step | Action | Expected |
|------|--------|----------|
| 1 | Open task detail for task-1 | Sheet opens |
| 2 | Click "Execution" tab | Execution section loads |
| 3 | Verify agent claim card visible | Card with agent info |
| 4 | Verify agent name: "backend-developer" | Text present |
| 5 | Verify "Working" status badge with pulse | AgentStatusBadge visible |
| 6 | Verify "Claimed" timestamp | Date visible |
| 7 | Verify "State: active" | Text present |
| 8 | Verify "Release claim" button | Visible and enabled |

#### 5.2 Task Claim — No Claims State

**Mock:** `**/api/v1/tasks/task-1/claims` returns empty.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Open task detail, Execution tab | Section loads |
| 2 | Verify "No agent claims yet." | Dashed border with text |
| 3 | Verify no "Release claim" button | Not visible |

#### 5.3 Release Claim (Voluntary)

**Mock:** `**/api/v1/tasks/task-1/release` POST returns `{ ok: true }`.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Open task with active claim | Claim card visible |
| 2 | Click "Release claim" button | POST to release endpoint |
| 3 | Verify claim card updates or refreshes | State changes to "released" or shows no claims |

#### 5.4 Heartbeat Display

**Mock:** `**/api/v1/tasks/task-1/heartbeats` returns heartbeat history.

```ts
await page.route('**/api/v1/tasks/task-1/heartbeats', (route) =>
  route.fulfill({ status: 200, body: JSON.stringify({
    items: [
      {
        id: 'hb-1',
        claim_id: 'claim-1',
        progress_percent: 75,
        current_step: 'Writing unit tests',
        next_step: 'Integration tests',
        blockers: null,
        eta: new Date(Date.now() + 600000).toISOString(),
        created_at: new Date(Date.now() - 60000).toISOString(),
      },
      {
        id: 'hb-2',
        claim_id: 'claim-1',
        progress_percent: 50,
        current_step: 'Implementing JWT generation',
        next_step: 'Unit tests',
        blockers: 'Missing test fixtures',
        eta: null,
        created_at: new Date(Date.now() - 180000).toISOString(),
      },
    ]
  })})
);
```

| Step | Action | Expected |
|------|--------|----------|
| 1 | Open task detail, Execution tab | Section loads |
| 2 | Verify "Heartbeats" heading with Clock icon | Visible |
| 3 | Verify first heartbeat: "Writing unit tests" | Text visible |
| 4 | Verify progress bar at 75% | Progress bar element with width |
| 5 | Verify "Next: Integration tests" | Text visible |
| 6 | Verify second heartbeat has blocker | "Blocker: Missing test fixtures" in red |
| 7 | Verify ETA shown for first heartbeat | Date visible |

#### 5.5 Heartbeat — No Heartbeats State

**Mock:** `**/api/v1/tasks/task-1/heartbeats` returns empty.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Open task detail, Execution tab | No heartbeat section rendered |
| 2 | Verify absence of "Heartbeats" heading | Not visible |

#### 5.6 Clarification Request — Display

**Mock:** `**/api/v1/tasks/task-1/clarifications` returns clarification data.

```ts
await page.route('**/api/v1/tasks/task-1/clarifications', (route) =>
  route.fulfill({ status: 200, body: JSON.stringify({
    items: [{
      id: 'clar-1',
      task_id: 'task-1',
      author_type: 'agent',
      author_id: 'backend-developer',
      question: 'Should JWT tokens expire after 15 minutes or 1 hour?',
      context: 'Implementing token expiry configuration',
      blocking: true,
      state: 'open',
      answer: null,
      answered_by: null,
      answered_at: null,
      created_at: new Date(Date.now() - 300000).toISOString(),
    }]
  })})
);
```

| Step | Action | Expected |
|------|--------|----------|
| 1 | Open task detail, Execution tab | Section loads |
| 2 | Verify "Clarifications" heading with MessageCircle icon | Visible |
| 3 | Verify ClarificationBanner visible | Banner present |
| 4 | Verify question text: "Should JWT tokens expire..." | Text visible |
| 5 | Verify asked by: "backend-developer" | Text visible |
| 6 | Verify blocking indicator | Visual indicator (red/orange) |

#### 5.7 Clarification — No Clarifications State

**Mock:** `**/api/v1/tasks/task-1/clarifications` returns empty.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Open task detail, Execution tab | Section loads |
| 2 | Verify "No clarifications requested." | Dashed border with text |

#### 5.8 Evidence Display

**Mock:** `**/api/v1/tasks/task-1/evidence` returns evidence items.

```ts
await page.route('**/api/v1/tasks/task-1/evidence', (route) =>
  route.fulfill({ status: 200, body: JSON.stringify({
    items: [{
      id: 'ev-1',
      task_id: 'task-1',
      type: 'test_output',
      title: 'Unit test results',
      description: 'All 42 tests passing',
      url: null,
      content_snippet: '42 passed, 0 failed',
      artifact_ref: null,
      created_by_type: 'agent',
      created_by_id: 'qa-engineer',
      verification_state: 'unverified',
      created_at: new Date().toISOString(),
    }]
  })})
);
```

| Step | Action | Expected |
|------|--------|----------|
| 1 | Open task detail, Execution tab | Section loads |
| 2 | Verify "Evidence" heading with FileText icon | Visible |
| 3 | Verify evidence card: "Unit test results" | Title visible |
| 4 | Verify type: "test_output" | Text visible |
| 5 | Verify description: "All 42 tests passing" | Text visible |
| 6 | Verify verification state: "unverified" | Text visible |

#### 5.9 Review Rounds Display

**Mock:** `**/api/v1/tasks/task-1/review-rounds` returns review data.

```ts
await page.route('**/api/v1/tasks/task-1/review-rounds', (route) =>
  route.fulfill({ status: 200, body: JSON.stringify({
    items: [{
      id: 'rr-1',
      task_id: 'task-1',
      requested_by_type: 'agent',
      requested_by_id: 'backend-developer',
      reviewer_type: 'agent',
      reviewer_id: 'code-quality-guard',
      state: 'completed',
      verdict: 'approve',
      confidence: 92,
      summary: 'Code quality excellent, all tests pass',
      created_at: new Date().toISOString(),
      started_at: new Date().toISOString(),
      completed_at: new Date().toISOString(),
    }]
  })})
);
```

| Step | Action | Expected |
|------|--------|----------|
| 1 | Open task detail, Execution tab | Section loads |
| 2 | Verify "Reviews" heading with CheckCircle icon | Visible |
| 3 | Verify ReviewVerdictCard visible | Card present |
| 4 | Verify reviewer: "code-quality-guard" | Text visible |
| 5 | Verify verdict: "approve" | Text/badge visible |
| 6 | Verify confidence: 92% | Number visible |
| 7 | Verify summary text | Text visible |

#### 5.10 Review — Accept/Reject Actions

| Step | Action | Expected |
|------|--------|----------|
| 1 | Open task with non-approved review | Review card with verdict != approve |
| 2 | Verify "Accept" button visible | Button present |
| 3 | Verify "Reject" button visible | Button present |
| 4 | Click "Accept" | Verdict update fires |

#### 5.11 Active Agents Dashboard Section

**Mock:** `**/api/v1/dashboard/agent-activity` returns agent activity data.

```ts
await page.route('**/api/v1/dashboard/agent-activity', (route) =>
  route.fulfill({ status: 200, body: JSON.stringify({
    items: [{
      agent_id: 'backend-developer',
      agent_name: 'Backend Developer',
      task_id: 'task-2',
      task_title: 'Implement auth middleware',
      claimed_at: new Date(Date.now() - 600000).toISOString(),
      last_heartbeat_at: new Date(Date.now() - 60000).toISOString(),
      progress_percent: 65,
      current_step: 'Writing middleware',
      is_stale: false,
    }]
  })})
);
```

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/` (dashboard) | Dashboard loads |
| 2 | Scroll to "Active Agents" section | Section visible |
| 3 | Verify agent card: "backend-developer" | Agent name visible |
| 4 | Verify task: "Implement auth middleware" | Task title visible |
| 5 | Verify progress: 65% | Progress indicator |
| 6 | Verify not stale | No stale indicator |

#### 5.12 Active Agents — Stale Detection

**Mock:** Agent with stale heartbeat (`is_stale: true`).

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to dashboard | Loads |
| 2 | Scroll to "Active Agents" | Section visible |
| 3 | Verify stale agent has visual indicator | Warning/stale badge or icon |

---

## Suite 6: Evidence & Review

**File:** `frontend/e2e/evidence-review.spec.ts` (NEW)

**Description:** Tests evidence lifecycle (create, verify, accept, reject), review round lifecycle (create, start, finding, verdict), and quality gate submission.

### Preconditions

- User authenticated
- Task exists with claims/evidence endpoints mocked
- Quality endpoints mocked

### Test Cases

#### 6.1 Attach Evidence — Via API Mock Verification

**Mock:** POST `**/api/v1/tasks/task-1/evidence` returns 201.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Open task detail, Execution tab | Evidence section visible |
| 2 | (If UI form exists) Fill evidence form | Fields accept input |
| 3 | Submit evidence | POST to evidence endpoint |
| 4 | Verify new evidence in list | Evidence card visible |

**Note:** If no UI form exists for evidence creation (API-only), test verifies the list rendering with mocked data only.

#### 6.2 Evidence Verification States

**Mock:** Evidence items in different states: `unverified`, `agent_verified`, `human_accepted`, `rejected`.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Mock evidence with state `unverified` | List shows "unverified" badge |
| 2 | Mock evidence with state `agent_verified` | List shows "agent_verified" |
| 3 | Mock evidence with state `human_accepted` | List shows "human_accepted" |
| 4 | Mock evidence with state `rejected` | List shows "rejected" |

#### 6.3 Submit for Review Gate — Blocked by DoD

**Mock:** POST `**/api/v1/tasks/task-1/submit-review` returns 400 with gate failure.

```ts
await page.route('**/api/v1/tasks/task-1/submit-review', (route) =>
  route.fulfill({ status: 400, body: JSON.stringify({
    detail: 'dod_not_satisfied: Tests pass, Code review'
  })})
);
```

| Step | Action | Expected |
|------|--------|----------|
| 1 | Trigger submit-for-review action | API call fires |
| 2 | Verify error about DoD not satisfied | Error message with DoD item names |

#### 6.4 Submit for Review Gate — Blocked by Clarification

**Mock:** Returns 400 with `clarification_blocking`.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Trigger submit-for-review | API call fires |
| 2 | Verify error about blocking clarification | Error message about open question |

#### 6.5 Submit for Review Gate — Success

**Mock:** POST returns 201 with new review round.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Trigger submit-for-review (all gates pass) | API call fires |
| 2 | Verify review round created | New round in reviews list |
| 3 | Verify state: "pending" | Badge/text shows pending |

#### 6.6 Review Round — Start

**Mock:** POST `**/api/v1/review-rounds/rr-1/start` returns 200.

| Step | Action | Expected |
|------|--------|----------|
| 1 | (Via API) Start review round | State changes to "in_progress" |

#### 6.7 Review Finding — Add

**Mock:** POST `**/api/v1/review-rounds/rr-1/findings` returns 201.

| Step | Action | Expected |
|------|--------|----------|
| 1 | (Via API) Add finding with severity: "warning" | Finding created |
| 2 | Verify finding appears in review | Finding card visible |

#### 6.8 Review Verdict — Approve

**Mock:** POST `**/api/v1/review-rounds/rr-1/verdict` returns 200.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Submit verdict: approve, confidence 95 | API call fires |
| 2 | Verify ReviewVerdictCard shows "approve" | Green/approved indicator |
| 3 | Verify confidence shown | 95% visible |

#### 6.9 Review Verdict — Reject

| Step | Action | Expected |
|------|--------|----------|
| 1 | Submit verdict: reject, confidence 30 | API call fires |
| 2 | Verify ReviewVerdictCard shows "reject" | Red/rejected indicator |
| 3 | Verify reject summary | Text visible |

#### 6.10 Quality Gate — All Checks Pass

**Mock:** Task with all DoD passed, required evidence attached, no blocking clarifications.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Trigger submit-for-review | API returns 201 |
| 2 | Verify success — review round created | New round appears |

---

## Suite 7: Quality Management

**File:** `frontend/e2e/quality.spec.ts` (expand existing)

**Description:** Tests acceptance criteria CRUD, DoD items CRUD, quality stats, and quality gate validation via the Quality tab.

### Preconditions

- User authenticated, on project quality page
- Mock quality stats API

### Test Cases

#### 7.1 Quality Page — Stats Display

**Mock:** `**/api/v1/projects/proj-1/quality/stats` returns `MOCK_QUALITY_STATS`.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/projects/proj-1/quality` | Quality page loads |
| 2 | Verify quality statistics displayed | Stats cards/numbers visible |
| 3 | Verify total tasks: 22 | Number matches |
| 4 | Verify pass rate: 84% | Percentage shown |
| 5 | Verify AC stats (total/passed) | Numbers visible |
| 6 | Verify DoD stats (total/passed) | Numbers visible |

#### 7.2 Acceptance Criteria — Add via Task Detail

**Mock:** POST `**/api/v1/tasks/task-1/acceptance-criteria` returns 201.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Open task detail for task-1 | Sheet opens |
| 2 | Click "AC" tab | AC section visible |
| 3 | Type criterion: "API returns 200 for valid login" | Input accepts text |
| 4 | Click "+" or press Enter | POST fires |
| 5 | Verify new AC in list | Text visible |
| 6 | Verify AC count updated in tab label | "AC (1)" shown |

#### 7.3 Acceptance Criteria — Empty State

| Step | Action | Expected |
|------|--------|----------|
| 1 | Open task with no ACs | AC tab shows empty state |
| 2 | Verify "No acceptance criteria yet." | Text visible |
| 3 | Verify "+" icon | Icon present |

#### 7.4 DoD Items — Add via Task Detail

**Mock:** POST `**/api/v1/tasks/task-1/dod-items` returns 201.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Open task detail, "DoD" tab | DoD section visible |
| 2 | Type DoD item: "Lint passes" | Input accepts text |
| 3 | Click "+" or press Enter | POST fires |
| 4 | Verify new DoD in list | Text visible |
| 5 | Verify count in tab label | "DoD (1)" |

#### 7.5 DoD Items — Empty State

| Step | Action | Expected |
|------|--------|----------|
| 1 | Open task with no DoD items | DoD tab empty state |
| 2 | Verify "No DoD items yet." | Text visible |

#### 7.6 Quality Stats — Empty Project

**Mock:** Stats return all zeros.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to quality page | Page loads |
| 2 | Verify zero stats displayed | All numbers are 0 |
| 3 | Verify pass rate: 0% | Percentage shown |

---

## Suite 8: Dashboard & Reporting

**File:** `frontend/e2e/dashboard.spec.ts` (expand existing)

**Description:** Tests dashboard stats, attention sections, portfolio overview, project health, report generation/export.

### Preconditions

- User authenticated
- Mock dashboard, attention, portfolio, reporting APIs

### Test Cases

#### 8.1 Dashboard — Stat Cards

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/` | Dashboard loads |
| 2 | Verify "Tasks In Progress" stat card | Visible with count |
| 3 | Verify "Tasks Done" stat card | Visible with count |
| 4 | Verify project count | Shows "2" from mock data |

#### 8.2 Dashboard — Needs Attention Sections

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/` | Dashboard loads |
| 2 | Scroll to "Needs Your Review" | Section visible |
| 3 | Verify "Open Questions" heading | Visible |
| 4 | Verify items listed (or empty state) | Content present |

#### 8.3 Dashboard — Recent Activity Feed

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/` | Dashboard loads |
| 2 | Scroll to "Recent Activity" | Section visible |
| 3 | Verify activity events from mock data | Event items visible |
| 4 | Verify event has actor name | "code-quality-guard" visible |
| 5 | Verify event has entity reference | Task reference visible |

#### 8.4 Dashboard — Recent Projects

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/` | Dashboard loads |
| 2 | Scroll to "Recent Projects" | Section visible |
| 3 | Verify "UPCP Core" listed | Text visible |
| 4 | Verify "Mobile App" listed | Text visible |
| 5 | Click project link | Navigates to project detail |

#### 8.5 Attention Dashboard — Blocked Tasks

**Mock:** `**/api/v1/dashboard/attention` returns data with blocked tasks.

```ts
await page.route('**/api/v1/dashboard/attention', (route) =>
  route.fulfill({ status: 200, body: JSON.stringify({
    needs_review: [],
    open_questions: [],
    blocked_tasks: [{ task_id: 'task-3', title: 'Add RBAC models', feature_id: 'feat-1' }],
    stale_claims: [],
    failed_dod: [],
    rejected_tasks: [],
    agent_verdicts_waiting: [],
    low_health_projects: [],
    recent_activity: [],
  })})
);
```

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to dashboard | Loads |
| 2 | Verify blocked task listed in attention | "Add RBAC models" visible |

#### 8.6 Attention Dashboard — Stale Claims

**Mock:** Attention data includes stale claims.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to dashboard | Loads |
| 2 | Verify stale claim listed | Agent name + "stale" indicator |
| 3 | Verify last heartbeat timestamp | Time visible |

#### 8.7 Attention Dashboard — Low Health Projects

**Mock:** Attention data includes low health projects.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to dashboard | Loads |
| 2 | Verify low health project card | Project name + score < 70 |
| 3 | Verify top issue label | "blocked tasks" or similar |

#### 8.8 Project Health Score

**Mock:** `**/api/v1/projects/proj-1/health` returns health data.

```ts
await page.route('**/api/v1/projects/proj-1/health', (route) =>
  route.fulfill({ status: 200, body: JSON.stringify({
    score: 55,
    breakdown: { blocked: 2, stale_claims: 1, failed_dod: 1, open_clarifications: 0, rejected: 0 },
    top_issue: 'blocked tasks',
  })})
);
```

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to project detail | Loads |
| 2 | Verify health score displayed (55) | Number/visual present |
| 3 | Verify top issue | "blocked tasks" text |

#### 8.9 Portfolio Overview

**Mock:** `**/api/v1/portfolio/overview` returns portfolio data.

```ts
await page.route('**/api/v1/portfolio/overview', (route) =>
  route.fulfill({ status: 200, body: JSON.stringify({
    total_projects: 2,
    total_tasks: 22,
    tasks_by_status: { backlog: 5, in_progress: 3, review: 2, done: 12 },
    projects: [
      { id: 'proj-1', name: 'UPCP Core', slug: 'upcp-core', task_count: 15, health_score: 75, top_issue: '' },
      { id: 'proj-2', name: 'Mobile App', slug: 'mobile-app', task_count: 7, health_score: 90, top_issue: '' },
    ],
  })})
);
```

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/reports` | Reports/portfolio page loads |
| 2 | Verify total projects: 2 | Number visible |
| 3 | Verify total tasks: 22 | Number visible |
| 4 | Verify per-project summaries | Both projects listed with health scores |

#### 8.10 Report Generation

**Mock:** POST `**/api/v1/projects/proj-1/reports/daily` returns 201.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/reports` | Page loads |
| 2 | (If UI has generate button) Click "Generate Daily Report" | POST fires |
| 3 | Verify new report in list | Report entry visible |
| 4 | Verify report type: "daily" | Badge/text visible |

#### 8.11 Report Export — Markdown

**Mock:** `**/api/v1/reports/report-1/markdown` returns markdown string.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to report detail | Report loads |
| 2 | (If UI has export button) Click "Export Markdown" | API call fires |
| 3 | Verify markdown content returned | Text contains `# Daily Report` |

---

## Suite 9: Notifications

**File:** `frontend/e2e/notifications.spec.ts` (NEW)

**Description:** Tests notification display, mark read, mark all read, unread count badge, notification dropdown.

### Preconditions

- User authenticated
- Mock notification endpoints

### Test Cases

#### 9.1 Notification Badge — Unread Count

**Mock:** `**/api/v1/notifications/unread-count` returns `{ count: 3 }`.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/` | Dashboard loads |
| 2 | Find notification bell icon in header | Icon visible |
| 3 | Verify badge count: "3" | Badge number visible on bell |

#### 9.2 Notification Badge — Zero Count

**Mock:** `**/api/v1/notifications/unread-count` returns `{ count: 0 }`.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/` | Dashboard loads |
| 2 | Verify bell icon visible | Present |
| 3 | Verify no badge or badge shows "0" | No distracting badge |

#### 9.3 Notification Dropdown — Opens

**Mock:** `**/api/v1/notifications` returns notification list.

```ts
await page.route('**/api/v1/notifications**', (route) =>
  route.fulfill({ status: 200, body: JSON.stringify({
    items: [
      { id: 'n-1', type: 'review_requested', title: 'Review requested', message: 'Task "JWT service" needs review', entity_type: 'task', entity_id: 'task-1', is_read: false, created_at: new Date().toISOString() },
      { id: 'n-2', type: 'task_completed', title: 'Task completed', message: 'Auth middleware is done', entity_type: 'task', entity_id: 'task-2', is_read: true, created_at: new Date().toISOString() },
    ]
  })})
);
```

| Step | Action | Expected |
|------|--------|----------|
| 1 | Click notification bell | Dropdown opens |
| 2 | Verify notification items visible | 2 items listed |
| 3 | Verify unread notification has visual indicator | Bold or dot indicator on "Review requested" |
| 4 | Verify read notification has no indicator | "Task completed" shows as read |
| 5 | Verify notification title and message | Both visible |

#### 9.4 Mark Single Notification Read

**Mock:** POST `**/api/v1/notifications/n-1/read` returns `{ id: 'n-1', is_read: true }`.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Open notification dropdown | List visible |
| 2 | Click on unread notification "n-1" | POST fires |
| 3 | Verify notification marked as read | Visual indicator changes |
| 4 | Verify unread count decremented | Badge updates |

#### 9.5 Mark All Read

**Mock:** POST `**/api/v1/notifications/read-all` returns `{ count: 3 }`.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Open notification dropdown with unread items | List visible |
| 2 | Click "Mark all read" button | POST fires |
| 3 | Verify all notifications show as read | No unread indicators |
| 4 | Verify badge count becomes 0 | Badge disappears or shows 0 |

#### 9.6 Notifications — Empty State

**Mock:** `**/api/v1/notifications` returns `{ items: [] }`.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Open notification dropdown | Dropdown opens |
| 2 | Verify empty state message | "No notifications" or similar |
| 3 | Verify no badge on bell | Badge hidden |

---

## Suite 10: Git Integration

**File:** `frontend/e2e/git.spec.ts` (expand existing)

**Description:** Tests git provider management, branch listing, commit history display.

### Preconditions

- User authenticated, on project git tab
- Mock git endpoints

### Test Cases

#### 10.1 Git Tab — Empty State

**Mock:** `**/api/v1/projects/proj-1/git-providers` returns empty.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/projects/proj-1/git` | Git page loads |
| 2 | Verify empty state | "No git providers" or similar |

#### 10.2 Git Provider — List

**Mock:** Return provider list.

```ts
await page.route('**/api/v1/projects/proj-1/git-providers', (route) =>
  route.fulfill({ status: 200, body: JSON.stringify([
    { id: 'gp-1', name: 'GitHub', provider_type: 'github', url: 'https://github.com/org/repo', status: 'active' }
  ])})
);
```

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to git tab | Page loads |
| 2 | Verify "GitHub" provider visible | Name visible |
| 3 | Verify provider type: "github" | Badge or text visible |
| 4 | Verify URL: "https://github.com/org/repo" | Text visible |

#### 10.3 Git Provider — Create

**Mock:** POST returns 201.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to git tab | Page loads |
| 2 | Click "Add Provider" or equivalent | Form/dialog opens |
| 3 | Fill provider details | Fields accept input |
| 4 | Submit | POST fires |
| 5 | Verify new provider in list | Provider visible |

#### 10.4 Git Branches — List

**Mock:** `**/api/v1/git-providers/gp-1/branches` returns branch data.

```ts
await page.route('**/api/v1/git-providers/gp-1/branches', (route) =>
  route.fulfill({ status: 200, body: JSON.stringify([
    { id: 'br-1', name: 'main', last_commit_sha: 'abc1234', is_default: true },
    { id: 'br-2', name: 'feature/auth', last_commit_sha: 'def5678', is_default: false },
  ])})
);
```

| Step | Action | Expected |
|------|--------|----------|
| 1 | Select/navigate to provider | Branches load |
| 2 | Verify "main" branch listed | Name visible |
| 3 | Verify default indicator on "main" | Badge or marker |
| 4 | Verify "feature/auth" branch | Name visible |

#### 10.5 Git Commits — History

**Mock:** `**/api/v1/git-providers/gp-1/commits` returns commit data.

```ts
await page.route('**/api/v1/git-providers/gp-1/commits', (route) =>
  route.fulfill({ status: 200, body: JSON.stringify([
    { id: 'c-1', sha: 'abc1234', message: 'feat: add JWT service', author: 'developer', committed_at: new Date().toISOString() },
    { id: 'c-2', sha: 'def5678', message: 'fix: token refresh bug', author: 'developer', committed_at: new Date().toISOString() },
  ])})
);
```

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to commits view | Commits load |
| 2 | Verify commit: "feat: add JWT service" | Message visible |
| 3 | Verify SHA: "abc1234" | SHA visible (truncated) |
| 4 | Verify author: "developer" | Author visible |
| 5 | Verify date | Date visible |

---

## Suite 11: Settings & Admin

**File:** `frontend/e2e/settings.spec.ts` (NEW)

**Description:** Tests settings page, theme toggle, API info display, and admin controls.

### Preconditions

- User authenticated

### Test Cases

#### 11.1 Settings Page — Renders

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/settings` | Settings page loads |
| 2 | Verify settings page heading | "Settings" or similar visible |
| 3 | Verify settings sections/cards | At least one section visible |

#### 11.2 Theme Toggle — Via Topbar

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/` | Dashboard loads |
| 2 | Find theme toggle button in header | Button visible |
| 3 | Click toggle | Theme changes (dark → light or light → dark) |
| 4 | Verify `document.documentElement.classList` contains `dark` or not | Matches toggle state |
| 5 | Click toggle again | Theme reverts |

#### 11.3 Theme Persistence

| Step | Action | Expected |
|------|--------|----------|
| 1 | Toggle theme to dark | Dark mode active |
| 2 | Navigate to `/projects` | Page loads |
| 3 | Verify dark mode still active | Background color dark |
| 4 | Refresh page | Page reloads |
| 5 | Verify dark mode persists | Theme preserved in localStorage |

#### 11.4 API Info Display

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/settings` | Page loads |
| 2 | (If shown) Verify API version or backend URL | Info text visible |

#### 11.5 Sidebar Navigation — All Items

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/` | Sidebar visible |
| 2 | Verify items: Dashboard, Projects, Reports, Health, Settings | All visible |
| 3 | Verify "UPCP" branding/logo | Visible in sidebar header |

---

## Suite 12: Accessibility

**File:** `frontend/e2e/accessibility.spec.ts` (expand existing)

**Description:** Tests keyboard navigation, screen reader compatibility, focus management, ARIA labels, and WCAG compliance.

### Preconditions

- User authenticated
- Multiple pages tested

### Test Cases

#### 12.1 Skip-to-Content Link

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/` | Page loads |
| 2 | Verify `<main id="main-content">` exists | Element found |
| 3 | Verify "Skip to main content" link | Visible on focus, href="#main-content" |
| 4 | Focus the skip link (Tab) | Link becomes visible |
| 5 | Activate skip link (Enter) | Focus moves to #main-content |

#### 12.2 Heading Hierarchy

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/` | Page loads |
| 2 | Count `<h1>` elements | Exactly 1 or 0 |
| 3 | Verify no heading level skips | h1 → h2 → h3 (no h1 → h3) |

#### 12.3 Interactive Elements — Focusable

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/` | Page loads |
| 2 | Press Tab 10 times | Focus moves through elements |
| 3 | Verify `document.activeElement` is never null | Always a focused element |
| 4 | Verify visible focus indicator | Focus ring or outline visible |

#### 12.4 Links — Accessible Names

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/` | Page loads |
| 2 | Check all `<a>` elements | Each has text or aria-label |
| 3 | Verify no empty links | No link with empty text AND no aria-label |

#### 12.5 Badges — Text Content

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/` | Page loads |
| 2 | Find all `[data-slot="badge"]` | List found |
| 3 | Verify each has non-empty text | `textContent.trim().length > 0` |

#### 12.6 Tables — Proper Structure

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/projects/proj-1` | Page loads |
| 2 | Find all `<table>` elements | At least 1 (if data present) |
| 3 | Verify each has `<thead>` and `<tbody>` | Structure correct |
| 4 | Verify table headers have text | `<th>` not empty |

#### 12.7 Dialog Focus Trap

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/projects/proj-1` | Page loads |
| 2 | Open edit dialog (pencil icon) | Dialog opens |
| 3 | Tab through dialog | Focus stays within dialog |
| 4 | Press Escape | Dialog closes |
| 5 | Verify focus returns to trigger button | Focus on pencil icon |

#### 12.8 Keyboard Navigation — Tabs

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/projects/proj-1` | Tabs visible |
| 2 | Focus "Overview" tab | Tab focused |
| 3 | Press ArrowRight | "Structure" tab focused |
| 4 | Press ArrowRight | "Delivery" tab focused |
| 5 | Press ArrowLeft | "Structure" tab focused again |
| 6 | Press Enter/Space | Tab activates, URL changes |

#### 12.9 ARIA Labels — Form Inputs

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/login` | Form visible |
| 2 | Check email input | Has `type="email"` or aria-label |
| 3 | Check password input | Has `type="password"` or aria-label |
| 4 | Check toggle button | Has `aria-label="Show password"` |

#### 12.10 Color Contrast — Text Readability

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/` | Page loads |
| 2 | Check primary text color | Not pure black (#000) |
| 3 | Check background is not transparent | `backgroundColor` set |
| 4 | Verify in both light and dark mode | Both pass |

---

## Suite 13: Error Handling

**File:** `frontend/e2e/error-states.spec.ts` (expand existing)

**Description:** Tests network errors, 401/403 redirects, 404 pages, validation errors, rate limiting.

### Preconditions

- User authenticated (except 401 tests)

### Test Cases

#### 13.1 404 Page — Unknown Route

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/completely-unknown-route` | Page loads |
| 2 | Verify 404 text | "404" or "not found" visible |
| 3 | Verify navigation back option | Link to home or dashboard |

#### 13.2 API 500 — Error Boundary

| Step | Action | Expected |
|------|--------|----------|
| 1 | Mock `**/api/v1/dashboard/stats` to return 500 | Error response |
| 2 | Navigate to `/` | Page attempts to load |
| 3 | Verify error message visible | "error" or "failed" text |
| 4 | Verify page doesn't crash completely | Error boundary catches it |

#### 13.3 401 — Redirect to Login

| Step | Action | Expected |
|------|--------|----------|
| 1 | Mock `**/api/v1/projects` to return 401 | Unauthorized |
| 2 | Navigate to `/projects` | API returns 401 |
| 3 | Verify redirect to `/login` | URL contains `/login` |

#### 13.4 403 — Forbidden

**Mock:** API returns 403 for a specific resource.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Mock `**/api/v1/projects/proj-1` to return 403 | Forbidden |
| 2 | Navigate to `/projects/proj-1` | API returns 403 |
| 3 | Verify error message | "Forbidden" or "access denied" visible |

#### 13.5 Validation Error — Form Submit

**Mock:** POST `**/api/v1/projects` returns 422.

```ts
await page.route('**/api/v1/projects', (route) => {
  if (route.request().method() === 'POST')
    return route.fulfill({ status: 422, body: JSON.stringify({ detail: [{ loc: ['body', 'name'], msg: 'field required' }] }) });
  return route.continue();
});
```

| Step | Action | Expected |
|------|--------|----------|
| 1 | Open create project dialog | Form visible |
| 2 | Submit without filling required fields | Validation fires |
| 3 | Verify validation error shown | Error message in dialog |

#### 13.6 Network Error — Offline

| Step | Action | Expected |
|------|--------|----------|
| 1 | Mock all API routes to abort | Network failure |
| 2 | Navigate to `/` | Page tries to load |
| 3 | Verify error handling | Error message or retry option |

#### 13.7 Rate Limiting — 429 Response

**Mock:** API returns 429.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Mock `**/api/v1/projects` to return 429 | Rate limited |
| 2 | Navigate to `/projects` | API returns 429 |
| 3 | Verify rate limit message | "Too many requests" or similar |
| 4 | Verify retry possible | User can try again |

#### 13.8 Empty State — No Data

**Mock:** All list endpoints return empty arrays.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Navigate to `/projects` | Empty state |
| 2 | Verify "No projects yet" or similar | Empty state UI |
| 3 | Verify CTA to create | "Create Project" button |
| 4 | Navigate to `/projects/proj-1/delivery` | Empty features |
| 5 | Verify "No features yet" | Empty state with CTA |

#### 13.9 Loading State — Skeleton

| Step | Action | Expected |
|------|--------|----------|
| 1 | Add 2-second delay to all API responses | Slow responses |
| 2 | Navigate to `/` | Skeleton loaders appear |
| 3 | Verify skeleton cards/rows visible | Animated placeholders |
| 4 | Wait for data | Skeletons replaced by content |

#### 13.10 Error Boundary — Component Crash

| Step | Action | Expected |
|------|--------|----------|
| 1 | Mock API to return malformed JSON | Parse error |
| 2 | Navigate to affected page | Error boundary activates |
| 3 | Verify error boundary UI | Error message visible |
| 4 | Verify app doesn't white-screen | Other parts still work |

---

## Suite 14: Multi-User Scenarios

**File:** `frontend/e2e/multi-user.spec.ts` (NEW)

**Description:** Tests concurrent agent operations, conflict detection, and human-agent collaboration.

### Preconditions

- Simulates multiple agents/users via sequential mock responses
- E2E tests run single-browser, so concurrency is simulated via API mock sequencing

### Test Cases

#### 14.1 Two Agents Claiming Same Task — Conflict

**Mock:** First claim succeeds, second returns 409.

```ts
let claimCount = 0;
await page.route('**/api/v1/tasks/task-1/claim', (route) => {
  claimCount++;
  if (claimCount === 1) {
    return route.fulfill({ status: 201, body: JSON.stringify({
      id: 'claim-1', task_id: 'task-1', agent_id: 'backend-developer', state: 'active',
      claimed_at: new Date().toISOString(),
    })});
  }
  return route.fulfill({ status: 409, body: JSON.stringify({ detail: 'task is already claimed' }) });
});
```

| Step | Action | Expected |
|------|--------|----------|
| 1 | Open task detail for task-1 | Sheet opens |
| 2 | (Simulate) Agent A claims task | Claim succeeds, claim card shows "backend-developer" |
| 3 | (Simulate) Agent B attempts claim | 409 returned |
| 4 | Verify only one claim shown | Single active claim in Execution tab |

**Note:** In a real E2E test, this would require two browser contexts. The mock approach validates UI behavior when conflict error is returned.

#### 14.2 Agent Releases, Another Agent Claims

**Mock:** Release succeeds, then new claim succeeds.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Open task with active claim by Agent A | Claim card shows Agent A |
| 2 | Click "Release claim" | Release succeeds |
| 3 | Verify claim card shows "released" state or empty | State updated |
| 4 | (Simulate) Agent B claims | New claim appears |
| 5 | Verify new agent shown | Agent B name visible |

#### 14.3 Agent and Human Collaboration — Review Flow

| Step | Action | Expected |
|------|--------|----------|
| 1 | Agent submits task for review | Review round created |
| 2 | Open task detail as human | Review round visible in Execution tab |
| 3 | Human clicks "Accept" on review | Verdict updates to "approve" |
| 4 | Verify task can transition to "done" | Status change available |

#### 14.4 Concurrent Edit — Optimistic Update

**Mock:** PATCH returns 409 (conflict).

```ts
await page.route('**/api/v1/tasks/task-1', (route) => {
  if (route.request().method() === 'PATCH') {
    return route.fulfill({ status: 409, body: JSON.stringify({ detail: 'conflict: task was modified by another user' }) });
  }
  return route.continue();
});
```

| Step | Action | Expected |
|------|--------|----------|
| 1 | Open task detail | Sheet loads |
| 2 | Change status via dropdown | PATCH fires |
| 3 | Mock returns 409 conflict | Error displayed |
| 4 | Verify task reverts to original state | Original status shown |
| 5 | Verify conflict message | Toast or inline error |

#### 14.5 Agent Heartbeat While Human Views Task

**Mock:** Heartbeat list updates in real-time (simulated by route returning new data on second call).

| Step | Action | Expected |
|------|--------|----------|
| 1 | Open task detail, Execution tab | Heartbeats load with 2 items |
| 2 | Mock heartbeat endpoint to return 3 items | Updated data |
| 3 | Trigger re-fetch (navigate away and back) | New heartbeat appears |
| 4 | Verify progress bar updated | Latest progress shown |

#### 14.6 Clarification Request/Answer Flow

**Mock:** Clarification in `open` state, then `answered`.

| Step | Action | Expected |
|------|--------|----------|
| 1 | Open task with open clarification | Clarification banner shows "open" |
| 2 | Mock clarification to return `answered` state | Updated data |
| 3 | Trigger re-fetch | Answer visible |
| 4 | Verify answer text and answered_by | Both fields populated |

---

## Data Requirements Summary

### Standard Mock Data (from `fixtures/mock-data.ts`)

| Entity | ID | Key Fields |
|--------|-----|-----------|
| User | `user-1` | admin@upcp.dev, is_superuser |
| Project | `proj-1` | "UPCP Core", active |
| Project | `proj-2` | "Mobile App", active |
| Feature | `feat-1` | "Authentication", in-progress |
| Feature | `feat-2` | "Agent Workflow", backlog |
| Task | `task-1` | "Implement JWT token service", done |
| Task | `task-2` | "Implement auth middleware", in-progress |
| Task | `task-3` | "Add RBAC models", blocked |
| Task | `task-4` | "Write auth unit tests", ready_for_review |
| Component | `comp-1` | "Backend API" |

### Additional Mock Data Needed

| Entity | ID | Used In |
|--------|-----|---------|
| Claim | `claim-1` | Suite 5 (Agent Workflow) |
| Heartbeat | `hb-1`, `hb-2` | Suite 5 |
| Clarification | `clar-1` | Suite 5 |
| Evidence | `ev-1` | Suite 6 |
| Review Round | `rr-1` | Suite 6 |
| Notification | `n-1`, `n-2` | Suite 9 |
| Git Provider | `gp-1` | Suite 10 |
| Branch | `br-1`, `br-2` | Suite 10 |
| Commit | `c-1`, `c-2` | Suite 10 |

### Task State Machine Reference (from `lifecycle.py`)

```
backlog → ready → claimed → in_progress → done
                                 ↓
                              blocked → in_progress
                                 ↓
                     needs_clarification → in_progress
                                 ↓
                     ready_for_review → done
                                 ↓
                          changes_requested → in_progress
```

**Terminal states:** `done`, `cancelled`

### Evidence Verification States

```
unverified → agent_verified → human_accepted
unverified → rejected
stale → unverified
```

### Review Round States

```
pending → in_progress → completed
pending → cancelled
in_progress → cancelled
```

---

## Implementation Priority

| Priority | Suite | New/Expand | Est. Tests |
|----------|-------|------------|------------|
| P0 | 5. Agent Workflow | NEW | 12 |
| P0 | 6. Evidence & Review | NEW | 10 |
| P1 | 4. Delivery Management | Expand | 17 |
| P1 | 1. Auth Flow | Expand | 8 |
| P1 | 9. Notifications | NEW | 6 |
| P2 | 3. Structure Management | NEW | 7 |
| P2 | 7. Quality Management | Expand | 6 |
| P2 | 14. Multi-User Scenarios | NEW | 6 |
| P2 | 8. Dashboard & Reporting | Expand | 11 |
| P3 | 2. Project CRUD | Expand | 9 |
| P3 | 10. Git Integration | Expand | 5 |
| P3 | 11. Settings & Admin | NEW | 5 |
| P3 | 12. Accessibility | Expand | 10 |
| P3 | 13. Error Handling | Expand | 10 |
| **Total** | | | **~122** |

---

## Mock Data Extension

Extend `fixtures/mock-data.ts` with:

```ts
export const MOCK_CLAIMS = { /* ... */ };
export const MOCK_HEARTBEATS = { /* ... */ };
export const MOCK_CLARIFICATIONS = { /* ... */ };
export const MOCK_EVIDENCE = { /* ... */ };
export const MOCK_REVIEW_ROUNDS = { /* ... */ };
export const MOCK_NOTIFICATIONS = { /* ... */ };
export const MOCK_GIT_PROVIDERS = { /* ... */ };
export const MOCK_BRANCHES = { /* ... */ };
export const MOCK_COMMITS = { /* ... */ };
```

Extend `fixtures/helpers.ts` `mockAllApis()` with routes for:

- `**/api/v1/dashboard/attention`
- `**/api/v1/dashboard/agent-activity`
- `**/api/v1/portfolio/overview`
- `**/api/v1/notifications**`
- `**/api/v1/projects/*/health`
- `**/api/v1/tasks/*/claims`
- `**/api/v1/tasks/*/heartbeats`
- `**/api/v1/tasks/*/clarifications`
- `**/api/v1/tasks/*/evidence`
- `**/api/v1/tasks/*/review-rounds`
- `**/api/v1/projects/*/git-providers`
