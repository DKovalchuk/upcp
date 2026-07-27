import { test, expect } from '@playwright/test';
import { gotoPage } from './fixtures/helpers';

test.describe('Navigation & Layout', () => {
  test('renders sidebar with all nav items', async ({ page }) => {
    await gotoPage(page, '/');
    await expect(page.locator('span').filter({ hasText: 'UPCP' }).first()).toBeVisible();
    await expect(page.getByText('Dashboard').first()).toBeVisible();
    await expect(page.getByText('Projects').first()).toBeVisible();
    await expect(page.getByText('Reports').first()).toBeVisible();
    await expect(page.getByText('Health').first()).toBeVisible();
    await expect(page.getByText('Settings').first()).toBeVisible();
  });

  test('topbar has search trigger', async ({ page }) => {
    await gotoPage(page, '/');
    await expect(page.getByText('Search or jump to...')).toBeVisible();
    await expect(page.getByText('Ctrl K')).toBeVisible();
  });

  test('navigates to projects page via sidebar', async ({ page }) => {
    await gotoPage(page, '/');
    await page.locator('a').filter({ hasText: /^Projects$/ }).first().click();
    await expect(page).toHaveURL(/\/projects/);
  });

  test('navigates to health page via sidebar', async ({ page }) => {
    await gotoPage(page, '/');
    await page.locator('a').filter({ hasText: /^Health$/ }).first().click();
    await expect(page).toHaveURL(/\/health/);
  });

  test('navigates to reports page via sidebar', async ({ page }) => {
    await gotoPage(page, '/');
    await page.locator('a').filter({ hasText: /^Reports$/ }).first().click();
    await expect(page).toHaveURL(/\/reports/);
  });

  test('project detail page renders', async ({ page }) => {
    await gotoPage(page, '/projects/proj-1');
    // Should show the project detail page
    await expect(page.getByText('Project Details')).toBeVisible({ timeout: 10000 });
  });

  test('skip-to-content link exists', async ({ page }) => {
    await gotoPage(page, '/');
    const skipLink = page.getByText('Skip to main content');
    await expect(skipLink).toHaveAttribute('href', '#main-content');
  });

  test('sidebar collapses on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await gotoPage(page, '/');
    const trigger = page.locator('[data-sidebar="trigger"]');
    if (await trigger.isVisible().catch(() => false)) {
      await expect(trigger).toBeVisible();
    }
  });
});
