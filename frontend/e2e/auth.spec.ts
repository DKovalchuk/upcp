import { test, expect, type Page } from '@playwright/test';

test.describe('Authentication', () => {
  // Background notification polling (unread-count via apiFetch, SSE stream)
  // returns 401 when unauthenticated against a LIVE backend — client.ts
  // treats any non-/auth/ 401 as fatal and does window.location.href =
  // '/login', yanking /setup away mid-test (reproduced: input count 2 vs 3).
  // With the backend down these requests fail as network errors (no 401),
  // which is why the failure only appears with the dev stack running.
  const mockNotifications = async (page: Page) => {
    await page.route('**/api/v1/notifications/unread-count', (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: '{"count":0}' })
    );
    await page.route('**/api/v1/notifications/stream*', (route) =>
      route.fulfill({ status: 200, contentType: 'text/event-stream', body: '' })
    );
  };

  test('redirects to login when not authenticated', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);
    const url = page.url();
    const isLogin = url.includes('/login') || await page.getByText('Sign in').isVisible().catch(() => false) || await page.getByText('Login').isVisible().catch(() => false);
    expect(isLogin).toBeTruthy();
  });

  test('login page has form inputs', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(1000);
    const inputs = page.locator('input');
    const count = await inputs.count();
    expect(count).toBeGreaterThanOrEqual(2);
  });

  test('login page has submit button', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(1000);
    const buttons = page.locator('button');
    const count = await buttons.count();
    expect(count).toBeGreaterThanOrEqual(1);
  });

  test('login page has password visibility toggle', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(1000);
    const passwordInput = page.getByRole('textbox', { name: 'Password' });
    await expect(passwordInput).toBeVisible({ timeout: 5000 });
    await expect(passwordInput).toHaveAttribute('type', 'password');
    const toggle = page.getByLabel('Show password');
    await toggle.click();
    await expect(passwordInput).toHaveAttribute('type', 'text');
    const hideToggle = page.getByLabel('Hide password');
    await expect(hideToggle).toBeVisible();
    await hideToggle.click();
    await expect(passwordInput).toHaveAttribute('type', 'password');
  });

  test('setup page has password visibility toggle', async ({ page }) => {
    await mockNotifications(page);
    await page.goto('/setup');
    await page.waitForLoadState('domcontentloaded');
    // Assert the setup form itself — login also has a Password textbox +
    // Show password toggle, so without this guard the test passed vacuously
    // whenever the page was bounced to /login.
    await expect(page.getByText('Create your admin account')).toBeVisible({ timeout: 5000 });
    const passwordInput = page.getByRole('textbox', { name: 'Password' });
    await expect(passwordInput).toBeVisible({ timeout: 5000 });
    await expect(passwordInput).toHaveAttribute('type', 'password');
    const toggle = page.getByLabel('Show password');
    await toggle.click();
    await expect(passwordInput).toHaveAttribute('type', 'text');
  });

  test('setup page has required fields', async ({ page }) => {
    await mockNotifications(page);
    await page.goto('/setup');
    await page.waitForLoadState('domcontentloaded');
    // Fail with a clear signal if the page got redirected to /login instead
    // of rendering the setup form (see mockNotifications for the redirect cause).
    await expect(page.getByText('Create your admin account')).toBeVisible({ timeout: 5000 });
    const inputs = page.locator('input');
    const count = await inputs.count();
    expect(count).toBeGreaterThanOrEqual(3);
  });
});
