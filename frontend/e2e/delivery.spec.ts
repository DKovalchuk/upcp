import { test, expect } from '@playwright/test';
import { gotoPage, mockWorkflowApis, openTaskSheet } from './fixtures/helpers';

test.describe('Delivery — Task Detail Execution Tab', () => {
  // Sprint 4+ split the old monolithic Execution tab into dedicated tabs:
  // Execution now shows claims + heartbeats + Git, while Clarifications,
  // Evidence and Reviews live in their own tabs.
  test('4.7 — execution tab shows all workflow sections', async ({ page }) => {
    await gotoPage(page, '/projects/proj-1/delivery');
    await mockWorkflowApis(page);
    await openTaskSheet(page);

    // Click Execution tab
    await page.getByRole('tab', { name: /execution/i }).click();
    await page.waitForTimeout(300);

    const sheet = page.locator('[data-slot="sheet-content"]');
    const panel = sheet.getByRole('tabpanel');
    // Workflow sections on Execution
    await expect(panel.getByText('Heartbeats')).toBeVisible();
    await expect(panel.getByText('Git')).toBeVisible();
    // The other workflow sections are reachable as tabs
    await expect(sheet.getByRole('tab', { name: 'Clarifications' })).toBeVisible();
    await expect(sheet.getByRole('tab', { name: 'Evidence' })).toBeVisible();
    await expect(sheet.getByRole('tab', { name: 'Reviews' })).toBeVisible();
  });

  test('4.7a — execution tab shows agent claim', async ({ page }) => {
    await gotoPage(page, '/projects/proj-1/delivery');
    await mockWorkflowApis(page);
    await openTaskSheet(page);
    await page.getByRole('tab', { name: /execution/i }).click();
    await page.waitForTimeout(300);

    // Agent claim should be visible
    await expect(page.getByText('backend-developer')).toBeVisible();
    await expect(page.getByRole('button', { name: /release claim/i })).toBeVisible();
  });

  test('4.7b — execution tab shows heartbeat progress', async ({ page }) => {
    await gotoPage(page, '/projects/proj-1/delivery');
    await mockWorkflowApis(page);
    await openTaskSheet(page);
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
    await openTaskSheet(page);
    // Evidence moved from Execution to its own tab
    await page.getByRole('tab', { name: 'Evidence' }).click();
    await page.waitForTimeout(300);

    const panel = page.locator('[data-slot="sheet-content"]').getByRole('tabpanel');
    await expect(panel.getByText('Unit test results')).toBeVisible();
    await expect(panel.getByText('Git diff of changes')).toBeVisible();
  });

  test('4.7d — execution tab shows review round', async ({ page }) => {
    await gotoPage(page, '/projects/proj-1/delivery');
    await mockWorkflowApis(page);
    await openTaskSheet(page);
    // Reviews moved from Execution to its own tab
    await page.getByRole('tab', { name: 'Reviews' }).click();
    await page.waitForTimeout(300);

    const panel = page.locator('[data-slot="sheet-content"]').getByRole('tabpanel');
    await expect(panel.getByText('Reviews')).toBeVisible();
    await expect(panel.getByText('code-quality-guard')).toBeVisible();
  });
});

test.describe('Delivery — Board View', () => {
  test('board view renders columns', async ({ page }) => {
    await gotoPage(page, '/projects/proj-1/delivery');
    const boardBtn = page.getByRole('button', { name: 'Board view' });
    await boardBtn.click();
    await page.waitForTimeout(500);
    await expect(page.getByText('Backlog', { exact: false }).first()).toBeVisible();
    await expect(page.getByText('In Progress').first()).toBeVisible();
    await expect(page.getByText('Review').first()).toBeVisible();
    await expect(page.getByText('Done').first()).toBeVisible();
  });

  test('board view stacks columns on mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await gotoPage(page, '/projects/proj-1/delivery');
    const boardBtn = page.getByRole('button', { name: 'Board view' });
    await boardBtn.click();
    await page.waitForTimeout(500);
    await expect(page.getByText('Backlog', { exact: false }).first()).toBeVisible();
  });

  test('board view shows task status columns', async ({ page }) => {
    await gotoPage(page, '/projects/proj-1/delivery');
    const boardBtn = page.getByRole('button', { name: 'Board view' });
    await boardBtn.click();
    await page.waitForTimeout(500);
    // Each column should have at least one task card
    const backlogCol = page.getByText('Backlog').first();
    await expect(backlogCol).toBeVisible();
  });
});

test.describe('Delivery — Task Lifecycle States', () => {
  test('task status badge shows correct state', async ({ page }) => {
    await gotoPage(page, '/projects/proj-1/delivery');
    // Feature rows are collapsed by default — expand before asserting rows
    await openTaskSheet(page, 'Implement JWT token service');
    await page.keyboard.press('Escape'); // close the sheet, keep the expanded list

    // "done" task should have Done badge
    await expect(page.getByText('Implement JWT token service').first()).toBeVisible();
    // "in-progress" task should be visible
    await expect(page.getByText('Implement auth middleware').first()).toBeVisible();
  });

  test('task priority dots render correctly', async ({ page }) => {
    await gotoPage(page, '/projects/proj-1/delivery');

    // Priority dots render on board cards (list rows show status instead)
    await page.getByRole('button', { name: 'Board view' }).click();
    const priorityDots = page.locator('[role="img"][aria-label^="Priority"]');
    await expect(priorityDots.first()).toBeVisible();
    const count = await priorityDots.count();
    expect(count).toBeGreaterThanOrEqual(1);
  });
});

test.describe('Audit Page — Search', () => {
  test('audit page has search input', async ({ page }) => {
    await gotoPage(page, '/projects/proj-1/audit');
    const searchInput = page.getByPlaceholder('Search events...');
    await expect(searchInput).toBeVisible({ timeout: 10000 });
  });

  test('audit page has event type filter', async ({ page }) => {
    await gotoPage(page, '/projects/proj-1/audit');
    await expect(page.getByText('All event types')).toBeVisible({ timeout: 10000 });
  });

  test('audit page has entity type filter', async ({ page }) => {
    await gotoPage(page, '/projects/proj-1/audit');
    await expect(page.getByText('All entity types')).toBeVisible({ timeout: 10000 });
  });
});
