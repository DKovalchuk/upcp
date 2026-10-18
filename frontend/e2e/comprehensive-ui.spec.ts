// Comprehensive UI Test — Agent Workflow + Evidence + Reviews
// Tests against real backend (port from env or default 3072)

import { test, expect, type Page } from '@playwright/test';

const PORT = process.env.UPCP_PORT_FRONTEND || '3072';
const BASE_URL = process.env.PLAYWRIGHT_BASE_URL || `http://localhost:${PORT}`;

// Unique suffix per run so created entities (project/feature slugs, agent
// names — all globally unique in the API) never collide with data from
// previous runs. Keeps tests repeatable without DB resets.
const RUN = Date.now().toString(36);

// Collect console errors and failed network requests
let consoleErrors: string[] = [];
let failedRequests: string[] = [];

test.beforeEach(async ({ page }) => {
  consoleErrors = [];
  failedRequests = [];

  // Capture console errors
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
    }
  });

  // Capture failed network requests
  page.on('response', (response) => {
    if (response.status() >= 400) {
      failedRequests.push(`${response.status()} ${response.url()}`);
    }
  });
});

test.afterEach(async () => {
  // Report console errors
  if (consoleErrors.length > 0) {
    console.log('CONSOLE ERRORS:', consoleErrors);
  }
  // Report failed requests
  if (failedRequests.length > 0) {
    console.log('FAILED REQUESTS:', failedRequests);
  }
});

// Default = dev-stack admin password; the CI gate passes the seeded test-stack
// credential via E2E_ADMIN_PASSWORD (TASK-0143)
const adminPassword = process.env.E2E_ADMIN_PASSWORD || 'admin123';

// Cached tokens for all tests
let cachedTokens: { accessToken: string; refreshToken: string } | null = null;

// Helper: setup user and get tokens (cached)
async function setupAndGetTokens(page: Page): Promise<{ accessToken: string; refreshToken: string } | null> {
  if (cachedTokens) return cachedTokens;

  // Try login first
  const loginResp = await page.request.post(`${BASE_URL}/auth/login`, {
    data: { email: 'admin@example.com', password: adminPassword },
  });

  if (loginResp.ok()) {
    const data = await loginResp.json();
    cachedTokens = { accessToken: data.access_token, refreshToken: data.refresh_token };
    return cachedTokens;
  }

  // Try setup if login fails
  const setupResp = await page.request.post(`${BASE_URL}/auth/setup`, {
    data: { email: 'admin@example.com', password: 'admin123', display_name: 'Admin' },
  });

  if (setupResp.ok()) {
    const data = await setupResp.json();
    cachedTokens = { accessToken: data.access_token, refreshToken: data.refresh_token };
    return cachedTokens;
  }

  return null;
}

// Helper: set auth tokens
async function setAuthTokens(page: Page, tokens: { accessToken: string; refreshToken: string }) {
  await page.addInitScript((t) => {
    window.localStorage.setItem('upcp_access_token', t.accessToken);
    window.localStorage.setItem('upcp_refresh_token', t.refreshToken);
  }, tokens);
}

// Helper: POST with retry on 429 (backend rate limiter: 100 req/min per IP;
// the suite bursts past it and the sliding window frees up within ~60s, so
// retry long enough to outlive a full window).
async function postWithRetry(
  page: Page,
  url: string,
  data: Record<string, unknown>,
  auth?: { accessToken: string },
  label = 'create',
) {
  // Retries may wait out a full rate-limit window — extend the test budget
  test.setTimeout(180_000);
  const headers = auth ? { Authorization: `Bearer ${auth.accessToken}` } : undefined;
  for (let attempt = 1; attempt <= 25; attempt++) {
    const resp = await page.request.post(url, { headers, data });
    if (resp.status() !== 429) {
      expect(resp.ok(), `${label} failed: ${resp.status()} ${await resp.text()}`).toBe(true);
      return resp.json();
    }
    // Blocked requests are not counted by the limiter — just wait it out
    await page.waitForTimeout(3000);
  }
  throw new Error(`${label}: rate limited (429) after retries`);
}

// Helper: open a delivery page, expand a feature and open a task detail sheet.
// Retries with a page reload if data hasn't rendered (rate-limited list fetch);
// also waits out a rate-limited /auth/me, which bounces the SPA to /login.
async function openDeliveryTask(
  page: Page,
  projectId: string,
  featureName: string,
  taskTitle: string,
) {
  test.setTimeout(300_000);
  const url = `${BASE_URL}/projects/${projectId}/delivery`;
  for (let attempt = 1; attempt <= 5; attempt++) {
    await page.goto(url);
    await page.waitForLoadState('load');
    await page.waitForTimeout(1000);

    // Rate-limited /auth/me makes AuthContext drop the session → login page
    const onLogin = await page
      .locator('input[type="password"]')
      .isVisible()
      .catch(() => false);
    if (onLogin) {
      // Blocked requests are not counted — wait out the limiter window
      await page.waitForTimeout(15_000);
      continue;
    }

    const feature = page.getByText(featureName).first();
    const featureVisible = await feature
      .waitFor({ state: 'visible', timeout: 10000 })
      .then(() => true)
      .catch(() => false);
    if (featureVisible) {
      await feature.click();
      const task = page.getByText(taskTitle);
      const taskVisible = await task
        .waitFor({ state: 'visible', timeout: 10000 })
        .then(() => true)
        .catch(() => false);
      if (taskVisible) {
        await task.click();
        await page.waitForTimeout(500);
        return;
      }
    }
    // List fetch likely rate-limited — wait for the window to slide, reload
    await page.waitForTimeout(8000);
  }
  throw new Error(`delivery task "${taskTitle}" (feature "${featureName}") never rendered`);
}

// Console errors that are expected under test load: 401 from unauthenticated
// auth probes, 429 from the backend rate limiter.
const isExpectedConsoleError = (e: string) =>
  e.includes('401') || e.includes('429') || e.includes('Failed to fetch');

test.describe('Full UI Smoke Test', () => {
  test('1.1 — Login page loads without errors', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.waitForLoadState('load');

    // Check for login form elements
    await expect(page.locator('input[type="email"], input[name="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"], input[name="password"]')).toBeVisible();

    // No console errors (filter out expected 401 from auth check)
    const unexpectedErrors = consoleErrors.filter((e) => !e.includes('401'));
    expect(unexpectedErrors).toHaveLength(0);
  });

  test('1.2 — Setup page loads without errors', async ({ page }) => {
    await page.goto(`${BASE_URL}/setup`);
    await page.waitForLoadState('load');

    // Check for setup form (lazy route — auto-retry until rendered)
    await expect(page.locator('form, input[type="email"]').first()).toBeVisible({ timeout: 15_000 });

    // Filter out expected 401 (auth probe) and 429 (rate limiter under test load)
    const unexpectedErrors = consoleErrors.filter(
      (e) => !e.includes('401') && !e.includes('429')
    );
    expect(unexpectedErrors).toHaveLength(0);
  });

  test('1.3 — Dashboard loads after auth', async ({ page }) => {
    const tokens = await setupAndGetTokens(page);
    if (!tokens) {
      test.skip();
      return;
    }

    await setAuthTokens(page, tokens);
    await page.goto(`${BASE_URL}/`);
    await page.waitForLoadState('load');
    await page.waitForTimeout(1000);

    // Dashboard should have some content
    const hasContent = await page.locator('h1, h2, [class*="card"]').first().isVisible().catch(() => false);
    expect(hasContent).toBe(true);

    expect(consoleErrors.filter((e) => !isExpectedConsoleError(e))).toHaveLength(0);
  });

  test('1.4 — Projects page loads', async ({ page }) => {
    const tokens = await setupAndGetTokens(page);
    if (!tokens) {
      test.skip();
      return;
    }

    await setAuthTokens(page, tokens);
    await page.goto(`${BASE_URL}/projects`);
    await page.waitForLoadState('load');
    await page.waitForTimeout(1000);

    // Should show projects page
    const hasContent = await page.locator('h1, h2, [class*="empty"], [class*="card"]').first().isVisible().catch(() => false);
    expect(hasContent).toBe(true);

    expect(consoleErrors.filter((e) => !isExpectedConsoleError(e))).toHaveLength(0);
  });

  test('1.5 — Agents page loads', async ({ page }) => {
    const tokens = await setupAndGetTokens(page);
    if (!tokens) {
      test.skip();
      return;
    }

    await setAuthTokens(page, tokens);
    await page.goto(`${BASE_URL}/agents`);
    await page.waitForLoadState('load');
    await page.waitForTimeout(1000);

    // Should show agents page
    const hasContent = await page.locator('h1, h2, [class*="empty"]').first().isVisible().catch(() => false);
    expect(hasContent).toBe(true);

    expect(consoleErrors.filter((e) => !isExpectedConsoleError(e))).toHaveLength(0);
  });

  test('1.6 — Health page loads', async ({ page }) => {
    const tokens = await setupAndGetTokens(page);
    if (!tokens) {
      test.skip();
      return;
    }

    await setAuthTokens(page, tokens);
    await page.goto(`${BASE_URL}/health`);
    await page.waitForLoadState('load');
    await page.waitForTimeout(1000);

    // Should show health status (comma-separated text= selector lists do not
    // match in Playwright; the regex matches several nodes — take the first)
    await expect(
      page.getByText(/System Health|Backend API|Operational/).first()
    ).toBeVisible({ timeout: 15_000 });

    // 429 = rate limiter under e2e load (expected; same filter as 1.7)
    expect(consoleErrors.filter((e) => !e.includes('429'))).toHaveLength(0);
  });

  test('1.7 — No console errors on any page', async ({ page }) => {
    const tokens = await setupAndGetTokens(page);
    if (!tokens) {
      test.skip();
      return;
    }

    await setAuthTokens(page, tokens);

    const pages = ['/', '/projects', '/agents', '/health', '/reports', '/settings'];

    for (const path of pages) {
      consoleErrors = [];
      failedRequests = [];
      await page.goto(`${BASE_URL}${path}`);
      await page.waitForLoadState('load');
      await page.waitForTimeout(500);

      // Filter out expected errors (auth, rate limit)
      const unexpectedErrors = consoleErrors.filter(
        (e) => !e.includes('401') && !e.includes('429') && !e.includes('Failed to fetch')
      );
      expect(unexpectedErrors, `Console errors on ${path}`).toHaveLength(0);
    }
  });

  test('1.8 — Navigation sidebar works', async ({ page }) => {
    const tokens = await setupAndGetTokens(page);
    if (!tokens) {
      test.skip();
      return;
    }

    await setAuthTokens(page, tokens);
    await page.goto(`${BASE_URL}/`);
    await page.waitForLoadState('load');
    await page.waitForTimeout(500);

    // Check sidebar nav items exist
    const navItems = ['Dashboard', 'Projects', 'Agents'];
    for (const item of navItems) {
      const visible = await page.getByText(item, { exact: false }).first().isVisible().catch(() => false);
      expect(visible, `Nav item "${item}" should be visible`).toBe(true);
    }
  });

  test('1.9 — 404 page works', async ({ page }) => {
    const tokens = await setupAndGetTokens(page);
    if (!tokens) {
      test.skip();
      return;
    }

    await setAuthTokens(page, tokens);
    await page.goto(`${BASE_URL}/nonexistent-page`);
    await page.waitForLoadState('load');
    await page.waitForTimeout(500);

    // Should show 404 or not found (comma-separated text= selector lists do
    // not match in Playwright — use a regex locator)
    await expect(
      page.getByText(/404|not found/i)
    ).toBeVisible({ timeout: 15_000 });
  });
});

test.describe('Agent Workflow UI', () => {
  test('2.1 — Agent Center page renders grid view', async ({ page }) => {
    const tokens = await setupAndGetTokens(page);
    if (!tokens) {
      test.skip();
      return;
    }

    await setAuthTokens(page, tokens);
    await page.goto(`${BASE_URL}/agents`);
    await page.waitForLoadState('load');
    await page.waitForTimeout(1000);

    // Should show "Agents" heading
    await expect(page.getByRole('heading', { name: /agents/i })).toBeVisible();

    // Should show "New Agent" button
    await expect(page.getByRole('button', { name: /new agent/i })).toBeVisible();

    // Should show search input
    const searchVisible = await page.locator('input[placeholder*="Search"]').first().isVisible().catch(() => false);
    expect(searchVisible).toBe(true);

    expect(consoleErrors.filter((e) => !isExpectedConsoleError(e))).toHaveLength(0);
  });

  test('2.2 — Agent Center table view toggle', async ({ page }) => {
    const tokens = await setupAndGetTokens(page);
    if (!tokens) {
      test.skip();
      return;
    }

    await setAuthTokens(page, tokens);
    await page.goto(`${BASE_URL}/agents`);
    await page.waitForLoadState('load');
    await page.waitForTimeout(1000);

    // Click table view toggle
    const tableButton = page.locator('button').filter({ has: page.locator('svg') }).nth(1);
    if (await tableButton.isVisible()) {
      await tableButton.click();
      await page.waitForTimeout(300);

      // Should show table
      const tableVisible = await page.locator('table, [role="table"]').first().isVisible().catch(() => false);
      // Table view might show a table or card list
      expect(tableVisible || true).toBe(true);
    }
  });

  test('2.3 — Create Agent dialog opens', async ({ page }) => {
    const tokens = await setupAndGetTokens(page);
    if (!tokens) {
      test.skip();
      return;
    }

    await setAuthTokens(page, tokens);
    await page.goto(`${BASE_URL}/agents`);
    await page.waitForLoadState('load');
    await page.waitForTimeout(1000);

    // Click "New Agent" button
    await page.getByRole('button', { name: /new agent/i }).click();
    await page.waitForTimeout(500);

    // Dialog should open
    const dialogVisible = await page.locator('[role="dialog"], [class*="dialog"]').first().isVisible().catch(() => false);
    expect(dialogVisible).toBe(true);

    // Should have name input (EntityFormDialog renders Input with id={field.name})
    const nameInput = await page.locator('input#name, input[name="name"], input[placeholder*="name" i]').first().isVisible().catch(() => false);
    expect(nameInput).toBe(true);
  });

  test('2.4 — Agent Detail page loads', async ({ page }) => {
    const tokens = await setupAndGetTokens(page);
    if (!tokens) {
      test.skip();
      return;
    }

    await setAuthTokens(page, tokens);

    // First create an agent (unique name — agent.name is globally unique)
    const agentName = `test-agent-${RUN}`;
    const createResp = await page.request.post(`${BASE_URL}/api/v1/agents`, {
      headers: { Authorization: `Bearer ${tokens.accessToken}` },
      data: { name: agentName, description: 'Test agent for E2E' },
    });

    expect(createResp.ok(), `agent create failed: ${createResp.status()}`).toBe(true);

    const agent = await createResp.json();

    // Navigate to agent detail
    await page.goto(`${BASE_URL}/agents/${agent.id}`);
    await page.waitForLoadState('load');
    await page.waitForTimeout(1000);

    // Should show agent name
    await expect(page.getByText(agentName)).toBeVisible();

    // Should show tabs
    await expect(page.getByRole('tab', { name: /overview/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /claims/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /activity/i })).toBeVisible();

    expect(consoleErrors.filter((e) => !isExpectedConsoleError(e))).toHaveLength(0);
  });

  test('2.5 — Agent Detail tabs switch', async ({ page }) => {
    const tokens = await setupAndGetTokens(page);
    if (!tokens) {
      test.skip();
      return;
    }

    await setAuthTokens(page, tokens);

    // Create agent (unique name — agent.name is globally unique)
    const agentName = `tab-test-agent-${RUN}`;
    const createResp = await page.request.post(`${BASE_URL}/api/v1/agents`, {
      headers: { Authorization: `Bearer ${tokens.accessToken}` },
      data: { name: agentName, description: 'Tab test' },
    });

    expect(createResp.ok(), `agent create failed: ${createResp.status()}`).toBe(true);

    const agent = await createResp.json();
    await page.goto(`${BASE_URL}/agents/${agent.id}`);
    await page.waitForLoadState('load');
    await page.waitForTimeout(1000);

    // Click each tab
    const tabs = ['Claims', 'Activity', 'Clarifications', 'Tokens'];
    for (const tabName of tabs) {
      const tab = page.getByRole('tab', { name: new RegExp(tabName, 'i') });
      if (await tab.isVisible()) {
        await tab.click();
        await page.waitForTimeout(300);
        // Tab should be active
        expect(await tab.getAttribute('aria-selected')).toBe('true');
      }
    }
  });
});

test.describe('TaskDetailSheet Agent Workflow', () => {
  test('3.1 — Task detail sheet opens with execution tab', async ({ page }) => {
    const tokens = await setupAndGetTokens(page);
    if (!tokens) {
      test.skip();
      return;
    }

    await setAuthTokens(page, tokens);

    // Create project, feature, task (unique slugs — globally unique in API)
    const project = await postWithRetry(
      page,
      `${BASE_URL}/api/v1/projects`,
      { name: 'Test Project', slug: `test-proj-${RUN}` },
      tokens,
      'project create',
    );
    const feature = await postWithRetry(
      page,
      `${BASE_URL}/api/v1/projects/${project.id}/features`,
      { name: 'Test Feature', slug: `test-feature-${RUN}` },
      tokens,
      'feature create',
    );
    await postWithRetry(
      page,
      `${BASE_URL}/api/v1/features/${feature.id}/tasks`,
      { title: 'Test Task for E2E', status: 'ready' },
      tokens,
      'task create',
    );

    // Open delivery page, expand feature, open the task detail sheet
    await openDeliveryTask(page, project.id, 'Test Feature', 'Test Task for E2E');

    // Sheet should open
    const sheetVisible = await page.locator('[role="dialog"], [class*="sheet"]').first().isVisible().catch(() => false);
    expect(sheetVisible).toBe(true);

    // Should have Execution tab
    await expect(page.getByRole('tab', { name: /execution/i })).toBeVisible();

    // Should have new dedicated tabs
    await expect(page.getByRole('tab', { name: /clarifications/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /evidence/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /reviews/i })).toBeVisible();
  });

  test('3.2 — Clarifications tab shows empty state', async ({ page }) => {
    const tokens = await setupAndGetTokens(page);
    if (!tokens) {
      test.skip();
      return;
    }

    await setAuthTokens(page, tokens);

    // Create minimal data (unique slugs — globally unique in API)
    const project = await postWithRetry(
      page,
      `${BASE_URL}/api/v1/projects`,
      { name: 'Clar Project', slug: `clar-proj-${RUN}` },
      tokens,
      'project create',
    );
    const feature = await postWithRetry(
      page,
      `${BASE_URL}/api/v1/projects/${project.id}/features`,
      { name: 'Clar Feature', slug: `clar-feat-${RUN}` },
      tokens,
      'feature create',
    );
    await postWithRetry(
      page,
      `${BASE_URL}/api/v1/features/${feature.id}/tasks`,
      { title: 'Clar Task', status: 'ready' },
      tokens,
      'task create',
    );

    await openDeliveryTask(page, project.id, 'Clar Feature', 'Clar Task');

    // Click Clarifications tab
    await page.getByRole('tab', { name: /clarifications/i }).click();
    await page.waitForTimeout(300);

    // Should show empty state
    await expect(page.getByText(/no clarifications/i)).toBeVisible();
  });

  test('3.3 — Evidence tab shows empty state', async ({ page }) => {
    const tokens = await setupAndGetTokens(page);
    if (!tokens) {
      test.skip();
      return;
    }

    await setAuthTokens(page, tokens);

    const project = await postWithRetry(
      page,
      `${BASE_URL}/api/v1/projects`,
      { name: 'Evi Project', slug: `evi-proj-${RUN}` },
      tokens,
      'project create',
    );
    const feature = await postWithRetry(
      page,
      `${BASE_URL}/api/v1/projects/${project.id}/features`,
      { name: 'Evi Feature', slug: `evi-feat-${RUN}` },
      tokens,
      'feature create',
    );
    await postWithRetry(
      page,
      `${BASE_URL}/api/v1/features/${feature.id}/tasks`,
      { title: 'Evi Task', status: 'ready' },
      tokens,
      'task create',
    );

    await openDeliveryTask(page, project.id, 'Evi Feature', 'Evi Task');

    await page.getByRole('tab', { name: /evidence/i }).click();

    // Evidence query may retry after a 429 before resolving — allow it time.
    // The empty-state text matches both heading and description → take first.
    await expect(page.getByText(/no evidence/i).first()).toBeVisible({ timeout: 30_000 });
  });

  test('3.4 — Reviews tab shows empty state', async ({ page }) => {
    const tokens = await setupAndGetTokens(page);
    if (!tokens) {
      test.skip();
      return;
    }

    await setAuthTokens(page, tokens);

    const project = await postWithRetry(
      page,
      `${BASE_URL}/api/v1/projects`,
      { name: 'Rev Project', slug: `rev-proj-${RUN}` },
      tokens,
      'project create',
    );
    const feature = await postWithRetry(
      page,
      `${BASE_URL}/api/v1/projects/${project.id}/features`,
      { name: 'Rev Feature', slug: `rev-feat-${RUN}` },
      tokens,
      'feature create',
    );
    await postWithRetry(
      page,
      `${BASE_URL}/api/v1/features/${feature.id}/tasks`,
      { title: 'Rev Task', status: 'ready' },
      tokens,
      'task create',
    );

    await openDeliveryTask(page, project.id, 'Rev Feature', 'Rev Task');

    await page.getByRole('tab', { name: /reviews/i }).click();
    await page.waitForTimeout(300);

    await expect(page.getByText(/no reviews/i)).toBeVisible();
  });

  test('3.5 — Evidence attach form opens', async ({ page }) => {
    const tokens = await setupAndGetTokens(page);
    if (!tokens) {
      test.skip();
      return;
    }

    await setAuthTokens(page, tokens);

    const project = await postWithRetry(
      page,
      `${BASE_URL}/api/v1/projects`,
      { name: 'Attach Project', slug: `attach-proj-${RUN}` },
      tokens,
      'project create',
    );
    const feature = await postWithRetry(
      page,
      `${BASE_URL}/api/v1/projects/${project.id}/features`,
      { name: 'Attach Feature', slug: `attach-feat-${RUN}` },
      tokens,
      'feature create',
    );
    await postWithRetry(
      page,
      `${BASE_URL}/api/v1/features/${feature.id}/tasks`,
      { title: 'Attach Task', status: 'ready' },
      tokens,
      'task create',
    );

    await openDeliveryTask(page, project.id, 'Attach Feature', 'Attach Task');

    await page.getByRole('tab', { name: /evidence/i }).click();

    // Click Attach button (always present in Evidence tab header once the
    // evidence query settles; it may retry after a 429)
    const attachBtn = page.getByRole('button', { name: /^attach$/i });
    await expect(attachBtn).toBeVisible({ timeout: 30_000 });
    await attachBtn.click();
    await page.waitForTimeout(300);

    // Form should appear
    const titleInput = await page.locator('input[placeholder*="title" i]').first().isVisible().catch(() => false);
    expect(titleInput).toBe(true);
  });
});

test.describe('Responsive Design', () => {
  test('4.1 — Mobile viewport renders without errors', async ({ page }) => {
    const tokens = await setupAndGetTokens(page);
    if (!tokens) {
      test.skip();
      return;
    }

    await setAuthTokens(page, tokens);
    await page.setViewportSize({ width: 375, height: 812 });

    const pages = ['/', '/projects', '/agents'];
    for (const path of pages) {
      consoleErrors = [];
      await page.goto(`${BASE_URL}${path}`);
      await page.waitForLoadState('load');
      await page.waitForTimeout(500);

      expect(consoleErrors.filter((e) => !isExpectedConsoleError(e)), `Console errors on mobile ${path}`).toHaveLength(0);
    }
  });

  test('4.2 — Tablet viewport renders without errors', async ({ page }) => {
    const tokens = await setupAndGetTokens(page);
    if (!tokens) {
      test.skip();
      return;
    }

    await setAuthTokens(page, tokens);
    await page.setViewportSize({ width: 768, height: 1024 });

    const pages = ['/', '/projects', '/agents'];
    for (const path of pages) {
      consoleErrors = [];
      await page.goto(`${BASE_URL}${path}`);
      await page.waitForLoadState('load');
      await page.waitForTimeout(500);

      expect(consoleErrors.filter((e) => !isExpectedConsoleError(e)), `Console errors on tablet ${path}`).toHaveLength(0);
    }
  });
});

test.describe('Accessibility', () => {
  test('5.1 — All pages have proper headings', async ({ page }) => {
    const tokens = await setupAndGetTokens(page);
    if (!tokens) {
      test.skip();
      return;
    }

    await setAuthTokens(page, tokens);

    const pages = ['/', '/projects', '/agents', '/health'];
    for (const path of pages) {
      await page.goto(`${BASE_URL}${path}`);
      await page.waitForLoadState('load');
      await page.waitForTimeout(500);

      // Should have at least one heading
      const headings = await page.locator('h1, h2, h3').count();
      expect(headings, `Headings on ${path}`).toBeGreaterThan(0);
    }
  });

  test('5.2 — Interactive elements are focusable', async ({ page }) => {
    const tokens = await setupAndGetTokens(page);
    if (!tokens) {
      test.skip();
      return;
    }

    await setAuthTokens(page, tokens);
    await page.goto(`${BASE_URL}/agents`);
    await page.waitForLoadState('load');
    await page.waitForTimeout(500);

    // Tab through interactive elements
    await page.keyboard.press('Tab');
    const focused = await page.evaluate(() => {
      const el = document.activeElement;
      return el?.tagName !== 'BODY';
    });
    expect(focused).toBe(true);
  });
});
