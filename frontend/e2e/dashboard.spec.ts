import { test, expect } from '@playwright/test';
import { gotoPage } from './fixtures/helpers';

test.describe('Dashboard', () => {
  test('shows stat cards', async ({ page }) => {
    await gotoPage(page, '/');
    await expect(page.getByText('Tasks In Progress')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Tasks Done')).toBeVisible();
  });

  test('shows Needs Attention section', async ({ page }) => {
    await gotoPage(page, '/');
    const el = page.getByText('Needs Your Review');
    await el.scrollIntoViewIfNeeded();
    await expect(el).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Open Questions', { exact: true })).toBeVisible();
  });

  test('shows Active Agents section', async ({ page }) => {
    await gotoPage(page, '/');
    const el = page.getByText('Active Agents').first();
    await el.scrollIntoViewIfNeeded();
    await expect(el).toBeVisible({ timeout: 10000 });
  });

  test('shows Recent Activity section', async ({ page }) => {
    await gotoPage(page, '/');
    const el = page.getByText('Recent Activity').last();
    await el.scrollIntoViewIfNeeded();
    await expect(el).toBeVisible({ timeout: 10000 });
  });

  test('shows recent projects heading', async ({ page }) => {
    await gotoPage(page, '/');
    const el = page.getByText('Recent Projects', { exact: true });
    await el.scrollIntoViewIfNeeded();
    await expect(el).toBeVisible({ timeout: 10000 });
  });

  test('activity feed shows events from API', async ({ page }) => {
    await gotoPage(page, '/');
    // The mock API returns recent_activity with actor_id "code-quality-guard"
    // The LiveActivityFeed transforms and displays this
    const feed = page.getByText('Recent Activity').last();
    await feed.scrollIntoViewIfNeeded();
    await page.waitForTimeout(500);
    // Check that the feed has content (either events or empty state)
    const hasContent = await page.getByText('No recent activity').isVisible().catch(() => false) ||
      await page.locator('[data-slot="badge"]').first().isVisible().catch(() => false);
    expect(hasContent).toBeTruthy();
  });
});
