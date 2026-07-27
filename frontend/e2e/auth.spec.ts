import { test, expect } from '@playwright/test';
import { mockAllApis } from './fixtures/helpers';

test.describe('Authentication', () => {
  test('redirects to login when not authenticated', async ({ page }) => {
    await mockAllApis(page);
    // Don't set auth tokens — go directly
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(1000);
    // Should redirect to login or show login content
    const url = page.url();
    const isLogin = url.includes('/login') || await page.getByText('Sign in').isVisible().catch(() => false) || await page.getByText('Login').isVisible().catch(() => false);
    expect(isLogin).toBeTruthy();
  });

  test('login page has form inputs', async ({ page }) => {
    await mockAllApis(page);
    await page.goto('/login');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(500);
    const inputs = page.locator('input');
    const count = await inputs.count();
    expect(count).toBeGreaterThanOrEqual(2);
  });

  test('login page has submit button', async ({ page }) => {
    await mockAllApis(page);
    await page.goto('/login');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(500);
    const buttons = page.locator('button');
    const count = await buttons.count();
    expect(count).toBeGreaterThanOrEqual(1);
  });

  test('setup page has required fields', async ({ page }) => {
    await mockAllApis(page);
    await page.goto('/setup');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(500);
    const inputs = page.locator('input');
    const count = await inputs.count();
    expect(count).toBeGreaterThanOrEqual(3);
  });
});
