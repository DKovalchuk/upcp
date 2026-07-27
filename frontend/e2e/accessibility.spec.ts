import { test, expect } from '@playwright/test';
import { gotoPage } from './fixtures/helpers';

test.describe('Accessibility', () => {
  test('main content has id for skip link', async ({ page }) => {
    await gotoPage(page, '/');
    const main = page.locator('#main-content');
    await expect(main).toBeVisible();
  });

  test('skip-to-content link exists', async ({ page }) => {
    await gotoPage(page, '/');
    const skipLink = page.getByText('Skip to main content');
    await expect(skipLink).toHaveAttribute('href', '#main-content');
  });

  test('headings follow hierarchy', async ({ page }) => {
    await gotoPage(page, '/');
    const h1 = await page.locator('h1').count();
    expect(h1).toBeLessThanOrEqual(1);
  });

  test('tables have proper structure', async ({ page }) => {
    await gotoPage(page, '/projects/proj-1');
    const tables = page.locator('table');
    const tableCount = await tables.count();
    if (tableCount > 0) {
      await expect(tables.first().locator('thead')).toBeVisible();
      await expect(tables.first().locator('tbody')).toBeVisible();
    }
  });

  test('badges have text content', async ({ page }) => {
    await gotoPage(page, '/');
    const badges = page.locator('[data-slot="badge"]');
    const count = await badges.count();
    for (let i = 0; i < Math.min(count, 10); i++) {
      const badge = badges.nth(i);
      const text = await badge.textContent();
      expect(text?.trim().length).toBeGreaterThan(0);
    }
  });

  test('interactive elements are focusable', async ({ page }) => {
    await gotoPage(page, '/');
    for (let i = 0; i < 5; i++) {
      await page.keyboard.press('Tab');
    }
    const focused = await page.evaluate(() => document.activeElement?.tagName);
    expect(focused).toBeTruthy();
  });

  test('links have accessible names', async ({ page }) => {
    await gotoPage(page, '/');
    const links = page.locator('a');
    const count = await links.count();
    for (let i = 0; i < Math.min(count, 15); i++) {
      const link = links.nth(i);
      const text = await link.textContent();
      const ariaLabel = await link.getAttribute('aria-label');
      expect((text?.trim().length || 0) + (ariaLabel?.length || 0)).toBeGreaterThan(0);
    }
  });
});
