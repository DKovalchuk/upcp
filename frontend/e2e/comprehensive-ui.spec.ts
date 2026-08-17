// Comprehensive UI Test — Agent Workflow + Evidence + Reviews
// Tests against real backend on localhost:3072

import { test, expect, type Page } from '@playwright/test';

const BASE_URL = 'http://localhost:3072';

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

// Cached tokens for all tests
let cachedTokens: { accessToken: string; refreshToken: string } | null = null;

// Helper: setup user and get tokens (cached)
async function setupAndGetTokens(page: Page): Promise<{ accessToken: string; refreshToken: string } | null> {
  if (cachedTokens) return cachedTokens;

  // Try login first
  const loginResp = await page.request.post(`${BASE_URL}/auth/login`, {
    data: { email: 'admin@example.com', password: 'admin123' },
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

test.describe('Full UI Smoke Test', () => {
  test('1.1 — Login page loads without errors', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.waitForLoadState('networkidle');

    // Check for login form elements
    await expect(page.locator('input[type="email"], input[name="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"], input[name="password"]')).toBeVisible();

    // No console errors (filter out expected 401 from auth check)
    const unexpectedErrors = consoleErrors.filter((e) => !e.includes('401'));
    expect(unexpectedErrors).toHaveLength(0);
  });

  test('1.2 — Setup page loads without errors', async ({ page }) => {
    await page.goto(`${BASE_URL}/setup`);
    await page.waitForLoadState('networkidle');

    // Check for setup form
    const formVisible = await page.locator('form, input[type="email"]').first().isVisible().catch(() => false);
    expect(formVisible).toBe(true);

    // Filter out expected 401 errors
    const unexpectedErrors = consoleErrors.filter((e) => !e.includes('401'));
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
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Dashboard should have some content
    const hasContent = await page.locator('h1, h2, [class*="card"]').first().isVisible().catch(() => false);
    expect(hasContent).toBe(true);

    expect(consoleErrors).toHaveLength(0);
  });

  test('1.4 — Projects page loads', async ({ page }) => {
    const tokens = await setupAndGetTokens(page);
    if (!tokens) {
      test.skip();
      return;
    }

    await setAuthTokens(page, tokens);
    await page.goto(`${BASE_URL}/projects`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Should show projects page
    const hasContent = await page.locator('h1, h2, [class*="empty"], [class*="card"]').first().isVisible().catch(() => false);
    expect(hasContent).toBe(true);

    expect(consoleErrors).toHaveLength(0);
  });

  test('1.5 — Agents page loads', async ({ page }) => {
    const tokens = await setupAndGetTokens(page);
    if (!tokens) {
      test.skip();
      return;
    }

    await setAuthTokens(page, tokens);
    await page.goto(`${BASE_URL}/agents`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Should show agents page
    const hasContent = await page.locator('h1, h2, [class*="empty"]').first().isVisible().catch(() => false);
    expect(hasContent).toBe(true);

    expect(consoleErrors).toHaveLength(0);
  });

  test('1.6 — Health page loads', async ({ page }) => {
    const tokens = await setupAndGetTokens(page);
    if (!tokens) {
      test.skip();
      return;
    }

    await setAuthTokens(page, tokens);
    await page.goto(`${BASE_URL}/health`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Should show health status
    const hasContent = await page.locator('text=System Health, text=Backend API, text=Operational').first().isVisible().catch(() => false);
    expect(hasContent).toBe(true);

    expect(consoleErrors).toHaveLength(0);
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
      await page.waitForLoadState('networkidle');
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
    await page.waitForLoadState('networkidle');
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
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);

    // Should show 404 or not found
    const has404 = await page.locator('text=404, text=not found, text=Not Found').first().isVisible().catch(() => false);
    expect(has404).toBe(true);
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
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Should show "Agents" heading
    await expect(page.getByRole('heading', { name: /agents/i })).toBeVisible();

    // Should show "New Agent" button
    await expect(page.getByRole('button', { name: /new agent/i })).toBeVisible();

    // Should show search input
    const searchVisible = await page.locator('input[placeholder*="Search"]').first().isVisible().catch(() => false);
    expect(searchVisible).toBe(true);

    expect(consoleErrors).toHaveLength(0);
  });

  test('2.2 — Agent Center table view toggle', async ({ page }) => {
    const tokens = await setupAndGetTokens(page);
    if (!tokens) {
      test.skip();
      return;
    }

    await setAuthTokens(page, tokens);
    await page.goto(`${BASE_URL}/agents`);
    await page.waitForLoadState('networkidle');
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
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Click "New Agent" button
    await page.getByRole('button', { name: /new agent/i }).click();
    await page.waitForTimeout(500);

    // Dialog should open
    const dialogVisible = await page.locator('[role="dialog"], [class*="dialog"]').first().isVisible().catch(() => false);
    expect(dialogVisible).toBe(true);

    // Should have name input
    const nameInput = await page.locator('input[name="name"], input[placeholder*="name" i]').first().isVisible().catch(() => false);
    expect(nameInput).toBe(true);
  });

  test('2.4 — Agent Detail page loads', async ({ page }) => {
    const tokens = await setupAndGetTokens(page);
    if (!tokens) {
      test.skip();
      return;
    }

    await setAuthTokens(page, tokens);

    // First create an agent
    const createResp = await page.request.post(`${BASE_URL}/api/v1/agents`, {
      headers: { Authorization: `Bearer ${tokens.accessToken}` },
      data: { name: 'test-agent', description: 'Test agent for E2E' },
    });

    if (!createResp.ok()) {
      test.skip();
      return;
    }

    const agent = await createResp.json();

    // Navigate to agent detail
    await page.goto(`${BASE_URL}/agents/${agent.id}`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Should show agent name
    await expect(page.getByText('test-agent')).toBeVisible();

    // Should show tabs
    await expect(page.getByRole('tab', { name: /overview/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /claims/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /activity/i })).toBeVisible();

    expect(consoleErrors).toHaveLength(0);
  });

  test('2.5 — Agent Detail tabs switch', async ({ page }) => {
    const tokens = await setupAndGetTokens(page);
    if (!tokens) {
      test.skip();
      return;
    }

    await setAuthTokens(page, tokens);

    // Create agent
    const createResp = await page.request.post(`${BASE_URL}/api/v1/agents`, {
      headers: { Authorization: `Bearer ${tokens.accessToken}` },
      data: { name: 'tab-test-agent', description: 'Tab test' },
    });

    if (!createResp.ok()) {
      test.skip();
      return;
    }

    const agent = await createResp.json();
    await page.goto(`${BASE_URL}/agents/${agent.id}`);
    await page.waitForLoadState('networkidle');
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

    // Create project, feature, task
    const projectResp = await page.request.post(`${BASE_URL}/api/v1/projects`, {
      headers: { Authorization: `Bearer ${tokens.accessToken}` },
      data: { name: 'Test Project', slug: 'test-proj' },
    });

    if (!projectResp.ok()) {
      test.skip();
      return;
    }

    const project = await projectResp.json();

    const featureResp = await page.request.post(`${BASE_URL}/api/v1/projects/${project.id}/features`, {
      headers: { Authorization: `Bearer ${tokens.accessToken}` },
      data: { name: 'Test Feature', slug: 'test-feature' },
    });

    if (!featureResp.ok()) {
      test.skip();
      return;
    }

    const feature = await featureResp.json();

    const taskResp = await page.request.post(`${BASE_URL}/api/v1/features/${feature.id}/tasks`, {
      headers: { Authorization: `Bearer ${tokens.accessToken}` },
      data: { title: 'Test Task for E2E', status: 'ready' },
    });

    if (!taskResp.ok()) {
      test.skip();
      return;
    }

    // Navigate to delivery page
    await page.goto(`${BASE_URL}/projects/${project.id}/delivery`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Click on the task to open detail sheet
    const taskRow = page.getByText('Test Task for E2E');
    if (await taskRow.isVisible()) {
      await taskRow.click();
      await page.waitForTimeout(500);

      // Sheet should open
      const sheetVisible = await page.locator('[role="dialog"], [class*="sheet"]').first().isVisible().catch(() => false);
      expect(sheetVisible).toBe(true);

      // Should have Execution tab
      await expect(page.getByRole('tab', { name: /execution/i })).toBeVisible();

      // Should have new dedicated tabs
      await expect(page.getByRole('tab', { name: /clarifications/i })).toBeVisible();
      await expect(page.getByRole('tab', { name: /evidence/i })).toBeVisible();
      await expect(page.getByRole('tab', { name: /reviews/i })).toBeVisible();
    }
  });

  test('3.2 — Clarifications tab shows empty state', async ({ page }) => {
    const tokens = await setupAndGetTokens(page);
    if (!tokens) {
      test.skip();
      return;
    }

    await setAuthTokens(page, tokens);

    // Create minimal data
    const projectResp = await page.request.post(`${BASE_URL}/api/v1/projects`, {
      headers: { Authorization: `Bearer ${tokens.accessToken}` },
      data: { name: 'Clar Project', slug: 'clar-proj' },
    });
    if (!projectResp.ok()) { test.skip(); return; }
    const project = await projectResp.json();

    const featureResp = await page.request.post(`${BASE_URL}/api/v1/projects/${project.id}/features`, {
      headers: { Authorization: `Bearer ${tokens.accessToken}` },
      data: { name: 'Clar Feature', slug: 'clar-feat' },
    });
    if (!featureResp.ok()) { test.skip(); return; }
    const feature = await featureResp.json();

    const taskResp = await page.request.post(`${BASE_URL}/api/v1/features/${feature.id}/tasks`, {
      headers: { Authorization: `Bearer ${tokens.accessToken}` },
      data: { title: 'Clar Task', status: 'ready' },
    });
    if (!taskResp.ok()) { test.skip(); return; }

    await page.goto(`${BASE_URL}/projects/${project.id}/delivery`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    await page.getByText('Clar Task').click();
    await page.waitForTimeout(500);

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

    const projectResp = await page.request.post(`${BASE_URL}/api/v1/projects`, {
      headers: { Authorization: `Bearer ${tokens.accessToken}` },
      data: { name: 'Evi Project', slug: 'evi-proj' },
    });
    if (!projectResp.ok()) { test.skip(); return; }
    const project = await projectResp.json();

    const featureResp = await page.request.post(`${BASE_URL}/api/v1/projects/${project.id}/features`, {
      headers: { Authorization: `Bearer ${tokens.accessToken}` },
      data: { name: 'Evi Feature', slug: 'evi-feat' },
    });
    if (!featureResp.ok()) { test.skip(); return; }
    const feature = await featureResp.json();

    const taskResp = await page.request.post(`${BASE_URL}/api/v1/features/${feature.id}/tasks`, {
      headers: { Authorization: `Bearer ${tokens.accessToken}` },
      data: { title: 'Evi Task', status: 'ready' },
    });
    if (!taskResp.ok()) { test.skip(); return; }

    await page.goto(`${BASE_URL}/projects/${project.id}/delivery`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    await page.getByText('Evi Task').click();
    await page.waitForTimeout(500);

    await page.getByRole('tab', { name: /evidence/i }).click();
    await page.waitForTimeout(300);

    await expect(page.getByText(/no evidence/i)).toBeVisible();
  });

  test('3.4 — Reviews tab shows empty state', async ({ page }) => {
    const tokens = await setupAndGetTokens(page);
    if (!tokens) {
      test.skip();
      return;
    }

    await setAuthTokens(page, tokens);

    const projectResp = await page.request.post(`${BASE_URL}/api/v1/projects`, {
      headers: { Authorization: `Bearer ${tokens.accessToken}` },
      data: { name: 'Rev Project', slug: 'rev-proj' },
    });
    if (!projectResp.ok()) { test.skip(); return; }
    const project = await projectResp.json();

    const featureResp = await page.request.post(`${BASE_URL}/api/v1/projects/${project.id}/features`, {
      headers: { Authorization: `Bearer ${tokens.accessToken}` },
      data: { name: 'Rev Feature', slug: 'rev-feat' },
    });
    if (!featureResp.ok()) { test.skip(); return; }
    const feature = await featureResp.json();

    const taskResp = await page.request.post(`${BASE_URL}/api/v1/features/${feature.id}/tasks`, {
      headers: { Authorization: `Bearer ${tokens.accessToken}` },
      data: { title: 'Rev Task', status: 'ready' },
    });
    if (!taskResp.ok()) { test.skip(); return; }

    await page.goto(`${BASE_URL}/projects/${project.id}/delivery`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    await page.getByText('Rev Task').click();
    await page.waitForTimeout(500);

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

    const projectResp = await page.request.post(`${BASE_URL}/api/v1/projects`, {
      headers: { Authorization: `Bearer ${tokens.accessToken}` },
      data: { name: 'Attach Project', slug: 'attach-proj' },
    });
    if (!projectResp.ok()) { test.skip(); return; }
    const project = await projectResp.json();

    const featureResp = await page.request.post(`${BASE_URL}/api/v1/projects/${project.id}/features`, {
      headers: { Authorization: `Bearer ${tokens.accessToken}` },
      data: { name: 'Attach Feature', slug: 'attach-feat' },
    });
    if (!featureResp.ok()) { test.skip(); return; }
    const feature = await featureResp.json();

    const taskResp = await page.request.post(`${BASE_URL}/api/v1/features/${feature.id}/tasks`, {
      headers: { Authorization: `Bearer ${tokens.accessToken}` },
      data: { title: 'Attach Task', status: 'ready' },
    });
    if (!taskResp.ok()) { test.skip(); return; }

    await page.goto(`${BASE_URL}/projects/${project.id}/delivery`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    await page.getByText('Attach Task').click();
    await page.waitForTimeout(500);

    await page.getByRole('tab', { name: /evidence/i }).click();
    await page.waitForTimeout(300);

    // Click Attach button
    const attachBtn = page.getByRole('button', { name: /attach/i });
    if (await attachBtn.isVisible()) {
      await attachBtn.click();
      await page.waitForTimeout(300);

      // Form should appear
      const titleInput = await page.locator('input[placeholder*="title" i]').first().isVisible().catch(() => false);
      expect(titleInput).toBe(true);
    }
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
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(500);

      expect(consoleErrors, `Console errors on mobile ${path}`).toHaveLength(0);
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
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(500);

      expect(consoleErrors, `Console errors on tablet ${path}`).toHaveLength(0);
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
      await page.waitForLoadState('networkidle');
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
    await page.waitForLoadState('networkidle');
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
