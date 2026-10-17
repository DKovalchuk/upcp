import { type Page, type Route } from '@playwright/test';
import {
  MOCK_USER,
  MOCK_TOKENS,
  MOCK_PROJECTS,
  MOCK_FEATURES,
  MOCK_TASKS,
  MOCK_COMPONENTS,
  MOCK_HEALTH,
  MOCK_AGENT_ACTIVITY,
} from './mock-data';

/**
 * Dashboard redesign fixtures (TASK-0128 Parts C/D).
 *
 * New helpers added ALONGSIDE the legacy `helpers.ts` on purpose:
 * the legacy `mockAllApis` registers its broad `/api/` glob catch-all LAST,
 * and in Playwright routes are matched LIFO — so the catch-all shadowed every
 * specific mock AND intercepted the frontend module `/src/lib/api/index.ts`
 * (JSON instead of JS → blank page). Here the catch-all is registered FIRST
 * and scoped to `/api/v1/` so it cannot touch frontend module URLs.
 */

// ── Rich mock data ──────────────────────────────────────────

export const STATS_ALL = {
  project_count: 3,
  task_counts_by_status: { backlog: 5, in_progress: 3, review: 2, done: 12, blocked: 2 },
  recent_projects: MOCK_PROJECTS,
  recent_activity: [
    {
      id: 'evt-1',
      timestamp: new Date(Date.now() - 5 * 60000).toISOString(),
      event_type: 'completed',
      entity_type: 'task',
      entity_id: 'task-1',
      actor_type: 'agent',
      actor_id: 'code-quality-guard',
      payload: null,
      note: null,
    },
    {
      id: 'evt-2',
      timestamp: new Date(Date.now() - 15 * 60000).toISOString(),
      event_type: 'claimed',
      entity_type: 'task',
      entity_id: 'task-2',
      actor_type: 'agent',
      actor_id: 'backend-developer',
      payload: null,
      note: null,
    },
  ],
  done_this_week: 6,
  blocked_count: 2,
  claimed_count: 1,
  health_score: 78,
};

/** Returned when `?project_id=` is present so KPI values visibly change. */
export const STATS_SCOPED = {
  ...STATS_ALL,
  project_count: 1,
  task_counts_by_status: { backlog: 1, in_progress: 1, review: 0, done: 4, blocked: 1 },
  done_this_week: 2,
  blocked_count: 1,
  claimed_count: 1,
  health_score: 91,
};

export const ATTENTION_ALL = {
  needs_review: [
    { task_id: 'task-rev-1', project_id: 'proj-1', requested_by: 'code-quality-guard' },
    { task_id: 'task-rev-2', project_id: 'proj-1', requested_by: 'qa-engineer' },
    { task_id: 'task-rev-3', project_id: 'proj-2', requested_by: 'reviewer' },
    { task_id: 'task-rev-4', project_id: 'proj-2', requested_by: 'reviewer' },
  ],
  open_questions: [
    { task_id: 'task-q-1', project_id: 'proj-1', question: 'JWT token expiry 15m or 1h?', author: 'database-architect' },
  ],
  blocked_tasks: [
    { task_id: 'task-blk-1', project_id: 'proj-1', title: 'Fix login timeout' },
  ],
  stale_claims: [],
  failed_dod: [],
  rejected_tasks: [],
  agent_verdicts_waiting: [],
  low_health_projects: [
    { project_id: 'proj-2', project_name: 'Mobile App', health_score: 42, top_issue: 'Flaky e2e suite' },
  ],
  recent_activity: [],
};

export const VELOCITY_8W = {
  items: [
    { week: '2026-W35', count: 3 },
    { week: '2026-W36', count: 5 },
    { week: '2026-W37', count: 4 },
    { week: '2026-W38', count: 7 },
    { week: '2026-W39', count: 2 },
    { week: '2026-W40', count: 6 },
    { week: '2026-W41', count: 8 },
    { week: '2026-W42', count: 5 },
  ],
};

export function portfolioOverview(projectCount = 3) {
  const projects = Array.from({ length: projectCount }, (_, i) => ({
    id: `proj-${i + 1}`,
    name: i === 0 ? 'UPCP Core' : i === 1 ? 'Mobile App' : `Project ${i + 1}`,
    slug: `project-${i + 1}`,
    task_count: 10 + i,
    health_score: i === 1 ? 42 : 80 + i,
    top_issue: i === 1 ? 'Flaky e2e suite' : '',
  }));
  return {
    total_projects: projectCount,
    total_tasks: projects.reduce((s, p) => s + p.task_count, 0),
    tasks_by_status: { backlog: 5, in_progress: 3, done: 12 },
    projects,
  };
}

// ── Helpers ─────────────────────────────────────────────────

const PNG_1PX = Buffer.from(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==',
  'base64'
);

/** Register console + pageerror collectors. Call BEFORE navigation. */
export function collectErrors(page: Page): string[] {
  const errors: string[] = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') errors.push(`console: ${msg.text()}`);
  });
  page.on('pageerror', (err) => errors.push(`pageerror: ${String(err)}`));
  return errors;
}

/**
 * Register all dashboard-related routes with CORRECT precedence:
 * catch-all first (lowest priority), specific mocks after (LIFO wins).
 * A later-registered route can still override via `route.fallback()`.
 */
export async function mockDashboardApis(page: Page) {
  // 1. Catch-all — scoped to backend API only, registered FIRST.
  await page.route('**/api/v1/**', (route: Route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ items: [], total: 0, offset: 0, limit: 20 }),
    })
  );

  // 2. Auth (frontend module /src/lib/auth.ts does not match these globs)
  await page.route('**/auth/me', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_USER) })
  );
  await page.route('**/auth/refresh', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_TOKENS) })
  );
  await page.route('**/auth/login', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_TOKENS) })
  );

  // 3. Static asset 404s would pollute the console-error assertion
  await page.route('**/avatars/**', (route) =>
    route.fulfill({ status: 200, contentType: 'image/png', body: PNG_1PX })
  );

  // 4. Projects list BEFORE detail routes (detail routes registered later win LIFO)
  await page.route('**/api/v1/projects?**', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ items: MOCK_PROJECTS, total: MOCK_PROJECTS.length, offset: 0, limit: 20 }),
    })
  );
  await page.route('**/api/v1/projects/proj-1', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_PROJECTS[0]) })
  );
  await page.route('**/api/v1/projects/proj-2', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_PROJECTS[1]) })
  );

  // 5. Project sub-resources (delivery/detail pages)
  await page.route('**/api/v1/projects/proj-1/features**', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ items: MOCK_FEATURES, total: MOCK_FEATURES.length, offset: 0, limit: 20 }),
    })
  );
  await page.route('**/api/v1/features/feat-1/tasks**', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ items: MOCK_TASKS, total: MOCK_TASKS.length, offset: 0, limit: 20 }),
    })
  );
  await page.route('**/api/v1/projects/proj-1/components**', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ items: MOCK_COMPONENTS, total: MOCK_COMPONENTS.length, offset: 0, limit: 20 }),
    })
  );
  await page.route('**/api/v1/projects/proj-1/quality**', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ pass_rate: 0.9 }) })
  );

  // 6. Dashboard core endpoints — scoped stats when ?project_id present
  await page.route('**/api/v1/dashboard/stats*', (route) => {
    const url = route.request().url();
    const scoped = url.includes('project_id=');
    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(scoped ? STATS_SCOPED : STATS_ALL),
    });
  });
  await page.route('**/api/v1/dashboard/attention*', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(ATTENTION_ALL) })
  );
  await page.route('**/api/v1/dashboard/agent-activity', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ items: MOCK_AGENT_ACTIVITY, total: MOCK_AGENT_ACTIVITY.length }),
    })
  );
  await page.route('**/api/v1/analytics/velocity*', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(VELOCITY_8W) })
  );
  await page.route('**/api/v1/portfolio/overview', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(portfolioOverview(3)) })
  );

  // 7. Notifications — list first, then unread-count, then stream (LIFO)
  await page.route('**/api/v1/notifications?**', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: [], total: 0 }) })
  );
  await page.route('**/api/v1/notifications/unread-count', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ count: 2 }) })
  );
  // Benign SSE stream by default; C7 overrides with a critical event.
  await page.route('**/api/v1/notifications/stream*', (route) =>
    route.fulfill({ status: 200, contentType: 'text/event-stream', body: ': keepalive\n\n' })
  );

  await page.route('**/api/v1/health', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_HEALTH) })
  );
}

/**
 * Set auth tokens before any app script runs, install base mocks, run an
 * optional per-test override hook (registered AFTER base mocks → wins LIFO),
 * then navigate.
 */
export async function gotoDashboard(
  page: Page,
  path = '/',
  beforeGoto?: (page: Page) => Promise<void>
) {
  await page.context().addInitScript((tokens: typeof MOCK_TOKENS) => {
    window.localStorage.setItem('upcp_access_token', tokens.access_token);
    window.localStorage.setItem('upcp_refresh_token', tokens.refresh_token);
  }, MOCK_TOKENS);
  await mockDashboardApis(page);
  if (beforeGoto) await beforeGoto(page);
  await page.goto(path);
  await page.waitForLoadState('domcontentloaded');
}

/** Record every `/dashboard/stats` request URL (registered LIFO → use route.fallback()). */
export async function recordStatsRequests(page: Page): Promise<string[]> {
  const urls: string[] = [];
  await page.route('**/dashboard/stats*', (route) => {
    urls.push(route.request().url());
    return route.fallback();
  });
  return urls;
}

/**
 * Press Tab until `target` is the active element. Returns true when reached.
 * Honest keyboard-navigation proof for D3/D4 without hardcoding tab counts.
 */
export async function tabUntilFocused(page: Page, target: ReturnType<Page['locator']>, max = 200) {
  for (let i = 0; i < max; i++) {
    const reached = await target.evaluate((el) => el === document.activeElement).catch(() => false);
    if (reached) return true;
    await page.keyboard.press('Tab');
  }
  return await target.evaluate((el) => el === document.activeElement).catch(() => false);
}
