import { test, expect } from '@playwright/test';

test.use({ storageState: { cookies: [], origins: [] } });

const API = process.env.E2E_API_BASE || 'http://127.0.0.1:38080';
// Default = dev-stack admin password; the CI gate passes the seeded test-stack
// credential via E2E_ADMIN_PASSWORD (TASK-0143)
const adminPassword = process.env.E2E_ADMIN_PASSWORD || 'admin123';

test.describe('Authentication flow', () => {
  test('login page renders', async ({ page }) => {
    await page.goto('/login');
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible({ timeout: 10_000 });
  });

  test('login with valid credentials redirects', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel(/email/i).fill('admin@example.com');
    await page.getByRole('textbox', { name: 'Password' }).fill(adminPassword);
    await page.getByRole('button', { name: /sign in|log in|enter/i }).click();
    await page.waitForURL('**/', { timeout: 10_000 });
    expect(page.url()).not.toContain('/login');
  });

  test('login with invalid credentials shows error', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel(/email/i).fill('wrong@example.com');
    await page.getByRole('textbox', { name: 'Password' }).fill('wrongpassword');
    await page.getByRole('button', { name: /sign in|log in|enter/i }).click();
    await expect(page.getByText(/invalid|incorrect|error/i)).toBeVisible({ timeout: 5_000 });
  });

  test('unauthenticated user redirected to /login', async ({ page }) => {
    await page.goto('/projects');
    await page.waitForURL('**/login', { timeout: 10_000 });
    expect(page.url()).toContain('/login');
  });

  // Regression (TASK-0139): background notification polling used to 401 on
  // public pages and client.ts hard-redirected /setup to /login mid-load.
  test('unauthenticated /setup stays on the setup form', async ({ page }) => {
    await page.goto('/setup');
    await expect(page.getByText(/create your admin account/i)).toBeVisible({
      timeout: 10_000,
    });
    // Give the on-mount unread-count poll time to fire and (before the fix)
    // yank the page away; the form must still be there afterwards.
    await page.waitForTimeout(3000);
    expect(page.url()).toContain('/setup');
    await expect(page.getByText(/create your admin account/i)).toBeVisible();
  });
});

test.describe('API auth', () => {
  test('POST /auth/login returns access_token', async ({ request }) => {
    const resp = await request.post(`${API}/auth/login`, {
      data: { email: 'admin@example.com', password: adminPassword },
    });
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(body).toHaveProperty('access_token');
  });

  test('GET /auth/me with token returns user', async ({ request }) => {
    const login = await request.post(`${API}/auth/login`, {
      data: { email: 'admin@example.com', password: adminPassword },
    });
    const { access_token } = await login.json();

    const me = await request.get(`${API}/auth/me`, {
      headers: { Authorization: `Bearer ${access_token}` },
    });
    expect(me.ok()).toBeTruthy();
    const user = await me.json();
    expect(user.email).toBe('admin@example.com');
    expect(user.is_active).toBe(true);
  });

  test('GET /auth/me without token returns 401/403', async ({ request }) => {
    const resp = await request.get(`${API}/auth/me`);
    expect(resp.status()).toBeGreaterThanOrEqual(400);
  });
});
