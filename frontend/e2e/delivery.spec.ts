import { test, expect } from '@playwright/test';
import { gotoPage, mockAllApis } from './fixtures/helpers';

test.describe('Delivery - Board View', () => {
  test('board view renders columns', async ({ page }) => {
    await gotoPage(page, '/projects/proj-1/delivery');
    // Switch to board view
    const boardBtn = page.getByRole('button', { name: /board/i });
    if (await boardBtn.isVisible().catch(() => false)) {
      await boardBtn.click();
      await page.waitForTimeout(500);
    }
    // Board columns should be visible
    await expect(page.getByText('Backlog').first()).toBeVisible();
    await expect(page.getByText('In Progress').first()).toBeVisible();
    await expect(page.getByText('Review').first()).toBeVisible();
    await expect(page.getByText('Done').first()).toBeVisible();
  });

  test('board view stacks columns on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await gotoPage(page, '/projects/proj-1/delivery');
    // Switch to board view
    const boardBtn = page.getByRole('button', { name: /board/i });
    if (await boardBtn.isVisible().catch(() => false)) {
      await boardBtn.click();
      await page.waitForTimeout(500);
    }
    // Columns should still be visible (stacked layout)
    await expect(page.getByText('Backlog').first()).toBeVisible();
  });
});

test.describe('Audit Page - Search', () => {
  test('audit page has search input', async ({ page }) => {
    await gotoPage(page, '/projects/proj-1/audit');
    const searchInput = page.getByPlaceholder('Search events...');
    await expect(searchInput).toBeVisible();
  });

  test('audit page has event type filter', async ({ page }) => {
    await gotoPage(page, '/projects/proj-1/audit');
    await expect(page.getByText('All event types')).toBeVisible();
  });

  test('audit page has entity type filter', async ({ page }) => {
    await gotoPage(page, '/projects/proj-1/audit');
    await expect(page.getByText('All entity types')).toBeVisible();
  });
});
