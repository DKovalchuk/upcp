import { test, expect } from '@playwright/test';
import { gotoPage } from './fixtures/helpers';

test.describe('Keyboard Shortcuts', () => {
  test('G then D navigates to dashboard', async ({ page }) => {
    await gotoPage(page, '/projects');
    await page.keyboard.press('g');
    await page.waitForTimeout(200);
    await page.keyboard.press('d');
    await page.waitForTimeout(500);
    await expect(page).toHaveURL(/\/$/);
  });

  test('G then P navigates to projects', async ({ page }) => {
    await gotoPage(page, '/');
    await page.keyboard.press('g');
    await page.waitForTimeout(200);
    await page.keyboard.press('p');
    await page.waitForTimeout(500);
    await expect(page).toHaveURL(/\/projects/);
  });

  test('G then R navigates to reports', async ({ page }) => {
    await gotoPage(page, '/');
    await page.keyboard.press('g');
    await page.waitForTimeout(200);
    await page.keyboard.press('r');
    await page.waitForTimeout(500);
    await expect(page).toHaveURL(/\/reports/);
  });

  test('Ctrl+K opens command palette', async ({ page }) => {
    await gotoPage(page, '/');
    await page.keyboard.press('Control+k');
    await page.waitForTimeout(500);
    const input = page.locator('[cmdk-input]');
    await expect(input).toBeVisible({ timeout: 5000 });
  });
});
