import { test, expect } from '@playwright/test';
import { gotoPage } from './fixtures/helpers';

test.describe('Command Palette', () => {
  test('opens with Ctrl+K', async ({ page }) => {
    await gotoPage(page, '/');
    await page.keyboard.press('Control+k');
    await page.waitForTimeout(500);
    // Command palette is rendered as a dialog with a search input
    const searchInput = page.locator('[cmdk-input]');
    await expect(searchInput).toBeVisible({ timeout: 5000 });
  });

  test('closes with Escape', async ({ page }) => {
    await gotoPage(page, '/');
    await page.keyboard.press('Control+k');
    await page.waitForTimeout(500);
    const searchInput = page.locator('[cmdk-input]');
    await expect(searchInput).toBeVisible({ timeout: 5000 });
    await page.keyboard.press('Escape');
    await page.waitForTimeout(300);
    await expect(searchInput).not.toBeVisible();
  });

  test('shows navigation commands', async ({ page }) => {
    await gotoPage(page, '/');
    await page.keyboard.press('Control+k');
    await page.waitForTimeout(500);
    const searchInput = page.locator('[cmdk-input]');
    await expect(searchInput).toBeVisible({ timeout: 5000 });
    // Should show navigation items inside the cmdk list
    await expect(page.getByText('Dashboard').last()).toBeVisible();
    await expect(page.getByText('Projects').last()).toBeVisible();
  });

  test('shows project commands when on project page', async ({ page }) => {
    await gotoPage(page, '/projects/proj-1');
    await page.keyboard.press('Control+k');
    await page.waitForTimeout(500);
    const searchInput = page.locator('[cmdk-input]');
    await expect(searchInput).toBeVisible({ timeout: 5000 });
    await expect(page.getByText('Overview').last()).toBeVisible();
    await expect(page.getByText('Structure').last()).toBeVisible();
    await expect(page.getByText('Delivery').last()).toBeVisible();
  });

  test('search trigger button opens palette', async ({ page }) => {
    await gotoPage(page, '/');
    await page.getByText('Search or jump to...').click();
    await page.waitForTimeout(500);
    const searchInput = page.locator('[cmdk-input]');
    await expect(searchInput).toBeVisible({ timeout: 5000 });
  });

  test('shows Actions group with New Project', async ({ page }) => {
    await gotoPage(page, '/');
    await page.keyboard.press('Control+k');
    await page.waitForTimeout(500);
    const searchInput = page.locator('[cmdk-input]');
    await expect(searchInput).toBeVisible({ timeout: 5000 });
    await expect(page.getByText('New Project').last()).toBeVisible();
  });

  test('shows project actions on project page', async ({ page }) => {
    await gotoPage(page, '/projects/proj-1/delivery');
    await page.keyboard.press('Control+k');
    await page.waitForTimeout(500);
    const searchInput = page.locator('[cmdk-input]');
    await expect(searchInput).toBeVisible({ timeout: 5000 });
    await expect(page.getByText('New Feature').last()).toBeVisible();
    await expect(page.getByText('Refresh Data').last()).toBeVisible();
  });
});
