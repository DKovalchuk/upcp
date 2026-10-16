import { test, expect } from '@playwright/test';

test.describe('Frontend navigation', () => {
  test('dashboard loads after login', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText(/dashboard|stats|projects/i).first()).toBeVisible({ timeout: 10_000 });
  });

  test('navigate to /projects', async ({ page }) => {
    await page.goto('/projects');
    await expect(page.getByText(/project/i).first()).toBeVisible({ timeout: 10_000 });
  });

  test('navigate to /settings', async ({ page }) => {
    await page.goto('/settings');
    await page.waitForLoadState('networkidle');
    expect(page.url()).toContain('/settings');
  });

  test('navigate to /health', async ({ page }) => {
    await page.goto('/health');
    await page.waitForLoadState('networkidle');
    expect(page.url()).toContain('/health');
  });

  test('sidebar links are visible', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    const links = page.locator('a[href]');
    await expect(links.first()).toBeVisible({ timeout: 5_000 });
    const count = await links.count();
    expect(count).toBeGreaterThan(2);
  });
});
