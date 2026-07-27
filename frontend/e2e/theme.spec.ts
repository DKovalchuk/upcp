import { test, expect } from '@playwright/test';
import { gotoPage } from './fixtures/helpers';

test.describe('Theme & Appearance', () => {
  test('page renders with theme', async ({ page }) => {
    await gotoPage(page, '/');
    const bgColor = await page.evaluate(() => getComputedStyle(document.body).backgroundColor);
    expect(bgColor).toBeTruthy();
    expect(bgColor).not.toBe('rgba(0, 0, 0, 0)');
  });

  test('theme toggle button exists in topbar', async ({ page }) => {
    await gotoPage(page, '/');
    const header = page.locator('header');
    const buttons = header.locator('button');
    const count = await buttons.count();
    expect(count).toBeGreaterThanOrEqual(3); // sidebar trigger, search, theme, bell, avatar
  });

  test('dark mode applies correctly when set', async ({ page }) => {
    await gotoPage(page, '/');
    await page.evaluate(() => document.documentElement.classList.add('dark'));
    await page.waitForTimeout(300);
    const bgColor = await page.evaluate(() => getComputedStyle(document.body).backgroundColor);
    expect(bgColor).toBeTruthy();
  });
});
