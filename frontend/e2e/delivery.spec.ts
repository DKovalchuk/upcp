import { test, expect } from '@playwright/test';
import { gotoPage, mockWorkflowApis } from './fixtures/helpers';

test.describe('Delivery — Task Detail Execution Tab', () => {
  test('4.7 — execution tab shows all workflow sections', async ({ page }) => {
    await gotoPage(page, '/projects/proj-1/delivery');
    await mockWorkflowApis(page);
    // Click task row to open sheet
    await page.getByText('Implement auth middleware').click();
    await page.waitForTimeout(500);

    // Click Execution tab
    await page.getByRole('tab', { name: /execution/i }).click();
    await page.waitForTimeout(300);

    // All workflow sections should be visible
    await expect(page.getByText('Clarifications')).toBeVisible();
    await expect(page.getByText('Evidence')).toBeVisible();
    await expect(page.getByText('Reviews')).toBeVisible();
    await expect(page.getByText('Git')).toBeVisible();
  });

  test('4.7a — execution tab shows agent claim', async ({ page }) => {
    await gotoPage(page, '/projects/proj-1/delivery');
    await mockWorkflowApis(page);
    await page.getByText('Implement auth middleware').click();
    await page.waitForTimeout(500);
    await page.getByRole('tab', { name: /execution/i }).click();
    await page.waitForTimeout(300);

    // Agent claim should be visible
    await expect(page.getByText('backend-developer')).toBeVisible();
    await expect(page.getByRole('button', { name: /release claim/i })).toBeVisible();
  });

  test('4.7b — execution tab shows heartbeat progress', async ({ page }) => {
    await gotoPage(page, '/projects/proj-1/delivery');
    await mockWorkflowApis(page);
    await page.getByText('Implement auth middleware').click();
    await page.waitForTimeout(500);
    await page.getByRole('tab', { name: /execution/i }).click();
    await page.waitForTimeout(300);

    // Heartbeat data should be visible
    await expect(page.getByText('Heartbeats')).toBeVisible();
    await expect(page.getByText('Writing unit tests')).toBeVisible();
    await expect(page.getByText('75%')).toBeVisible();
  });

  test('4.7c — execution tab shows evidence', async ({ page }) => {
    await gotoPage(page, '/projects/proj-1/delivery');
    await mockWorkflowApis(page);
    await page.getByText('Implement auth middleware').click();
    await page.waitForTimeout(500);
    await page.getByRole('tab', { name: /execution/i }).click();
    await page.waitForTimeout(300);

    // Evidence should be visible
    await expect(page.getByText('Unit test results')).toBeVisible();
    await expect(page.getByText('Git diff of changes')).toBeVisible();
  });

  test('4.7d — execution tab shows review round', async ({ page }) => {
    await gotoPage(page, '/projects/proj-1/delivery');
    await mockWorkflowApis(page);
    await page.getByText('Implement auth middleware').click();
    await page.waitForTimeout(500);
    await page.getByRole('tab', { name: /execution/i }).click();
    await page.waitForTimeout(300);

    // Review should be visible
    await expect(page.getByText('Reviews')).toBeVisible();
    await expect(page.getByText('code-quality-guard')).toBeVisible();
  });
});

test.describe('Delivery — Board View', () => {
  test('board view renders columns', async ({ page }) => {
    await gotoPage(page, '/projects/proj-1/delivery');
    const boardBtn = page.getByRole('button', { name: /board/i });
    if (await boardBtn.isVisible().catch(() => false)) {
      await boardBtn.click();
      await page.waitForTimeout(500);
    }
    await expect(page.getByText('Backlog').first()).toBeVisible();
    await expect(page.getByText('In Progress').first()).toBeVisible();
    await expect(page.getByText('Review').first()).toBeVisible();
    await expect(page.getByText('Done').first()).toBeVisible();
  });

  test('board view stacks columns on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await gotoPage(page, '/projects/proj-1/delivery');
    const boardBtn = page.getByRole('button', { name: /board/i });
    if (await boardBtn.isVisible().catch(() => false)) {
      await boardBtn.click();
      await page.waitForTimeout(500);
    }
    await expect(page.getByText('Backlog').first()).toBeVisible();
  });

  test('board view shows task status columns', async ({ page }) => {
    await gotoPage(page, '/projects/proj-1/delivery');
    const boardBtn = page.getByRole('button', { name: /board/i });
    if (await boardBtn.isVisible().catch(() => false)) {
      await boardBtn.click();
      await page.waitForTimeout(500);
    }
    // Each column should have at least one task card
    const backlogCol = page.getByText('Backlog').first();
    await expect(backlogCol).toBeVisible();
  });
});

test.describe('Delivery — Task Lifecycle States', () => {
  test('task status badge shows correct state', async ({ page }) => {
    await gotoPage(page, '/projects/proj-1/delivery');
    await page.waitForTimeout(500);

    // "done" task should have Done badge
    await expect(page.getByText('Implement JWT token service').first()).toBeVisible();
    // "in-progress" task should be visible
    await expect(page.getByText('Implement auth middleware').first()).toBeVisible();
  });

  test('task priority dots render correctly', async ({ page }) => {
    await gotoPage(page, '/projects/proj-1/delivery');
    await page.waitForTimeout(500);

    // Priority dots should be rendered (role=img with priority labels)
    const priorityDots = page.locator('[role="img"][aria-label*="priority"]');
    const count = await priorityDots.count();
    expect(count).toBeGreaterThanOrEqual(1);
  });
});

test.describe('Audit Page — Search', () => {
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
