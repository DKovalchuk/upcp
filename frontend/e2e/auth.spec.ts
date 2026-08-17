import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
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
    await page.goto('/setup');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(1000);
    const passwordInput = page.getByRole('textbox', { name: 'Password' });
    await expect(passwordInput).toBeVisible({ timeout: 5000 });
    await expect(passwordInput).toHaveAttribute('type', 'password');
    const toggle = page.getByLabel('Show password');
    await toggle.click();
    await expect(passwordInput).toHaveAttribute('type', 'text');
  });

  test('setup page has required fields', async ({ page }) => {
    await page.goto('/setup');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(1000);
    const inputs = page.locator('input');
    const count = await inputs.count();
    expect(count).toBeGreaterThanOrEqual(3);
  });
});
