import { type Page, type Route, type BrowserContext } from '@playwright/test';
import {
  MOCK_USER,
  MOCK_TOKENS,
  MOCK_PROJECTS,
  MOCK_DASHBOARD_STATS,
  MOCK_FEATURES,
  MOCK_TASKS,
  MOCK_COMPONENTS,
  MOCK_HEALTH,
  MOCK_QUALITY_STATS,
  MOCK_AUDIT_EVENTS,
  MOCK_CLAIMS,
  MOCK_HEARTBEATS,
  MOCK_CLARIFICATIONS,
  MOCK_EVIDENCE,
  MOCK_REVIEW_ROUNDS,
  MOCK_REVIEW_FINDINGS,
  MOCK_AGENT_ACTIVITY,
  MOCK_ATTENTION,
  MOCK_NOTIFICATIONS,
} from './mock-data';

/**
 * Intercept all API calls and return mock data.
 */
export async function mockAllApis(page: Page) {
  // Auth endpoints
  await page.route('**/auth/me', (route: Route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_USER) })
  );
  await page.route('**/auth/login', (route: Route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_TOKENS) })
  );
  await page.route('**/auth/setup', (route: Route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ ...MOCK_TOKENS, user: MOCK_USER }) })
  );
  await page.route('**/auth/refresh', (route: Route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_TOKENS) })
  );

  // Dashboard
  await page.route('**/api/v1/dashboard/stats', (route: Route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_DASHBOARD_STATS) })
  );

  // Health
  await page.route('**/api/v1/health', (route: Route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_HEALTH) })
  );

  // Projects list
  await page.route('**/api/v1/projects?**', (route: Route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ items: MOCK_PROJECTS, total: MOCK_PROJECTS.length, offset: 0, limit: 20 }),
    })
  );

  // Individual project
  await page.route('**/api/v1/projects/proj-1', (route: Route) => {
    if (route.request().method() === 'DELETE') return route.fulfill({ status: 204 });
    if (route.request().method() === 'PATCH') return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_PROJECTS[0]) });
    return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_PROJECTS[0]) });
  });
  await page.route('**/api/v1/projects/proj-2', (route: Route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_PROJECTS[1]) })
  );

  // Features
  await page.route('**/api/v1/projects/proj-1/features**', (route: Route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: MOCK_FEATURES, total: MOCK_FEATURES.length, offset: 0, limit: 20 }) })
  );

  // Tasks
  await page.route('**/api/v1/features/feat-1/tasks**', (route: Route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: MOCK_TASKS, total: MOCK_TASKS.length, offset: 0, limit: 20 }) })
  );
  await page.route('**/api/v1/tasks/task-1', (route: Route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_TASKS[0]) })
  );
  await page.route('**/api/v1/tasks/task-2', (route: Route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_TASKS[1]) })
  );
  await page.route('**/api/v1/tasks/task-3', (route: Route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_TASKS[2]) })
  );

  // Components
  await page.route('**/api/v1/projects/proj-1/components**', (route: Route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: MOCK_COMPONENTS, total: MOCK_COMPONENTS.length, offset: 0, limit: 20 }) })
  );

  // Quality
  await page.route('**/api/v1/projects/proj-1/quality**', (route: Route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_QUALITY_STATS) })
  );

  // Acceptance criteria, DoD, subtasks
  await page.route('**/api/v1/tasks/*/acceptance-criteria**', (route: Route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: [], total: 0, offset: 0, limit: 20 }) })
  );
  await page.route('**/api/v1/tasks/*/dod**', (route: Route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: [], total: 0, offset: 0, limit: 20 }) })
  );
  await page.route('**/api/v1/tasks/*/subtasks**', (route: Route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: [], total: 0, offset: 0, limit: 20 }) })
  );

  // Audit
  await page.route('**/api/v1/projects/proj-1/audit**', (route: Route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: MOCK_AUDIT_EVENTS, total: MOCK_AUDIT_EVENTS.length, offset: 0, limit: 20 }) })
  );

  // Search
  await page.route('**/api/v1/search**', (route: Route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) })
  );

  // Reports, Git, modules
  await page.route('**/api/v1/projects/proj-1/reports**', (route: Route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: [], total: 0, offset: 0, limit: 20 }) })
  );
  await page.route('**/api/v1/projects/proj-1/git/**', (route: Route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) })
  );
  await page.route('**/api/v1/components/*/modules**', (route: Route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: [], total: 0, offset: 0, limit: 20 }) })
  );

  // Catch-all for unmocked API calls
  await page.route('**/api/**', (route: Route) => {
    return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: [], total: 0, offset: 0, limit: 20 }) });
  });
}

/**
 * Mock agent workflow endpoints for task detail execution tab.
 * Override specific routes per test for different scenarios.
 */
export async function mockWorkflowApis(page: Page) {
  await page.route('**/api/v1/tasks/*/claims', (route: Route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: MOCK_CLAIMS, total: MOCK_CLAIMS.length }) })
  );
  await page.route('**/api/v1/tasks/*/heartbeats', (route: Route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: MOCK_HEARTBEATS, total: MOCK_HEARTBEATS.length }) })
  );
  await page.route('**/api/v1/tasks/*/clarifications', (route: Route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: MOCK_CLARIFICATIONS, total: MOCK_CLARIFICATIONS.length }) })
  );
  await page.route('**/api/v1/tasks/*/evidence', (route: Route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: MOCK_EVIDENCE, total: MOCK_EVIDENCE.length }) })
  );
  await page.route('**/api/v1/tasks/*/review-rounds', (route: Route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: MOCK_REVIEW_ROUNDS, total: MOCK_REVIEW_ROUNDS.length }) })
  );
  await page.route('**/api/v1/review-rounds/*/findings', (route: Route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: MOCK_REVIEW_FINDINGS, total: MOCK_REVIEW_FINDINGS.length }) })
  );
  await page.route('**/api/v1/dashboard/attention', (route: Route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_ATTENTION) })
  );
  await page.route('**/api/v1/dashboard/agent-activity', (route: Route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: MOCK_AGENT_ACTIVITY, total: MOCK_AGENT_ACTIVITY.length }) })
  );
  await page.route('**/api/v1/notifications**', (route: Route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: MOCK_NOTIFICATIONS, total: MOCK_NOTIFICATIONS.length }) })
  );
}

/**
 * Navigate to a page with auth set up via addInitScript.
 * This avoids the localStorage SecurityError by injecting tokens
 * before the page JavaScript runs.
 */
export async function gotoPage(page: Page, path: string) {
  // Use addInitScript to set localStorage before the app loads
  await page.context().addInitScript((tokens: typeof MOCK_TOKENS) => {
    window.localStorage.setItem('upcp_access_token', tokens.access_token);
    window.localStorage.setItem('upcp_refresh_token', tokens.refresh_token);
  }, MOCK_TOKENS);

  await mockAllApis(page);
  await page.goto(path);
  await page.waitForLoadState('domcontentloaded');
  // Small wait for React to hydrate and API calls to complete
  await page.waitForTimeout(500);
}
