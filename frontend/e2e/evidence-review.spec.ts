import { test, expect } from '@playwright/test';
import { gotoPage, mockWorkflowApis, openTaskSheet } from './fixtures/helpers';
import {
  MOCK_EVIDENCE_ACCEPTED,
  MOCK_EVIDENCE_REJECTED,
  MOCK_EVIDENCE_EMPTY,
  MOCK_REVIEW_ROUNDS_EMPTY,
} from './fixtures/mock-data';

// Helper: open task detail and switch to one of the dedicated tabs.
// Note: Sprint 4+ moved Evidence and Reviews out of Execution into
// their own tabs.
async function openTaskTab(page: import('@playwright/test').Page, tabName: string | RegExp) {
  await gotoPage(page, '/projects/proj-1/delivery');
  await mockWorkflowApis(page);
  await openTaskSheet(page);
  await page.getByRole('tab', { name: tabName }).click();
  await page.waitForTimeout(300);
}

function sheetPanel(page: import('@playwright/test').Page) {
  return page.locator('[data-slot="sheet-content"]').getByRole('tabpanel');
}

test.describe('Evidence & Review', () => {
  test.describe('Evidence Lifecycle', () => {
    test('6.1 — displays evidence list with items', async ({ page }) => {
      await openTaskTab(page, 'Evidence');

      const panel = sheetPanel(page);
      await expect(panel.getByText('Evidence')).toBeVisible();
      await expect(panel.getByText('Unit test results')).toBeVisible();
      await expect(panel.getByText('All 42 tests passing')).toBeVisible();
      await expect(panel.getByText('Git diff of changes')).toBeVisible();
      // Raw content snippet rendered in the evidence card
      await expect(panel.getByText('42 passed, 0 failed')).toBeVisible();
    });

    test('6.2 — shows unverified verification state', async ({ page }) => {
      await openTaskTab(page, 'Evidence');

      // First evidence item is unverified
      await expect(sheetPanel(page).getByText('unverified')).toBeVisible();
    });

    test('6.2a — shows agent_verified verification state', async ({ page }) => {
      await openTaskTab(page, 'Evidence');

      // Second evidence item is agent_verified
      await expect(sheetPanel(page).getByText('agent_verified')).toBeVisible();
    });

    test('6.2b — shows human_accepted verification state', async ({ page }) => {
      await gotoPage(page, '/projects/proj-1/delivery');
      await mockWorkflowApis(page);
      await page.route('**/api/v1/tasks/*/evidence', (route) =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: MOCK_EVIDENCE_ACCEPTED, total: MOCK_EVIDENCE_ACCEPTED.length }) })
      );
      await openTaskSheet(page);
      await page.getByRole('tab', { name: 'Evidence' }).click();
      await page.waitForTimeout(300);

      await expect(sheetPanel(page).getByText('human_accepted')).toBeVisible();
    });

    test('6.2c — shows rejected verification state', async ({ page }) => {
      await gotoPage(page, '/projects/proj-1/delivery');
      await mockWorkflowApis(page);
      await page.route('**/api/v1/tasks/*/evidence', (route) =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: MOCK_EVIDENCE_REJECTED, total: MOCK_EVIDENCE_REJECTED.length }) })
      );
      await openTaskSheet(page);
      await page.getByRole('tab', { name: 'Evidence' }).click();
      await page.waitForTimeout(300);

      await expect(sheetPanel(page).getByText('rejected')).toBeVisible();
    });

    test('6.1a — shows empty state when no evidence', async ({ page }) => {
      await gotoPage(page, '/projects/proj-1/delivery');
      await mockWorkflowApis(page);
      await page.route('**/api/v1/tasks/*/evidence', (route) =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: MOCK_EVIDENCE_EMPTY, total: 0 }) })
      );
      await openTaskSheet(page);
      await page.getByRole('tab', { name: 'Evidence' }).click();
      await page.waitForTimeout(300);

      // EmptyState title on the Evidence tab
      await expect(sheetPanel(page).getByText('No evidence', { exact: true })).toBeVisible();
    });
  });

  test.describe('Review Rounds', () => {
    test('6.4 — displays completed review round', async ({ page }) => {
      await openTaskTab(page, 'Reviews');

      const panel = sheetPanel(page);
      await expect(panel.getByText('Reviews')).toBeVisible();
      await expect(panel.getByText('code-quality-guard')).toBeVisible();
      await expect(panel.getByText('92%')).toBeVisible();
      await expect(panel.getByText(/code quality excellent/i)).toBeVisible();
    });

    test('6.4a — shows verdict as approve', async ({ page }) => {
      await openTaskTab(page, 'Reviews');

      // ReviewVerdictCard renders the verdict as "Approved"
      await expect(sheetPanel(page).getByText(/approve/i).first()).toBeVisible();
    });

    test('6.4b — shows empty state when no reviews', async ({ page }) => {
      await gotoPage(page, '/projects/proj-1/delivery');
      await mockWorkflowApis(page);
      await page.route('**/api/v1/tasks/*/review-rounds', (route) =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: MOCK_REVIEW_ROUNDS_EMPTY, total: 0 }) })
      );
      await openTaskSheet(page);
      await page.getByRole('tab', { name: 'Reviews' }).click();
      await page.waitForTimeout(300);

      // EmptyState title on the Reviews tab
      await expect(sheetPanel(page).getByText('No reviews', { exact: true })).toBeVisible();
    });
    // 6.5 (accept/reject for pending review), 6.6 (findings stub — asserted
    // nothing) and 6.7/6.7a (verdict POST) removed: the current UI has no
    // review-verdict accept/reject controls (no component passes
    // onAccept/onReject to ReviewVerdictCard or calls useSubmitReviewVerdict).
  });
});
