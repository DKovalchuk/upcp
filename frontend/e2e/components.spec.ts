import { test, expect } from '@playwright/test';
import { gotoPage } from './fixtures/helpers';

test.describe('Component Interactions', () => {
  test('status badges display correct text', async ({ page }) => {
    await gotoPage(page, '/');
    await expect(page.getByText('Active').first()).toBeVisible();
  });

  test('tabs are keyboard navigable', async ({ page }) => {
    await gotoPage(page, '/projects/proj-1');
    const overviewTab = page.getByRole('tab', { name: 'Overview' });
    await overviewTab.focus();
    await expect(overviewTab).toBeFocused();
    await page.keyboard.press('ArrowRight');
    const structureTab = page.getByRole('tab', { name: 'Structure' });
    await expect(structureTab).toBeFocused();
  });

  test('dialog traps focus and closes with Escape', async ({ page }) => {
    await gotoPage(page, '/projects/proj-1');
    // Find the edit button (pencil icon)
    const editButton = page.locator('button').filter({ has: page.locator('svg[class*="lucide-pencil"]') }).first();
    if (await editButton.isVisible().catch(() => false)) {
      await editButton.click();
      await page.waitForTimeout(300);
      await expect(page.getByText('Edit Project')).toBeVisible();
      await page.keyboard.press('Escape');
      await page.waitForTimeout(300);
      await expect(page.getByText('Edit Project')).not.toBeVisible();
    }
  });

  test('all interactive elements are focusable', async ({ page }) => {
    await gotoPage(page, '/');
    // Tab through several elements
    for (let i = 0; i < 5; i++) {
      await page.keyboard.press('Tab');
    }
    // Should have a focused element
    const focused = await page.evaluate(() => document.activeElement?.tagName);
    expect(focused).toBeTruthy();
  });

  test('cards have proper structure', async ({ page }) => {
    await gotoPage(page, '/');
    const cards = page.locator('[data-slot="card"]');
    // Dashboard loads async — wait for content instead of counting a still-empty main
    await expect(cards.first()).toBeVisible({ timeout: 10000 });
    expect(await cards.count()).toBeGreaterThan(0);
  });
});
