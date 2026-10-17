import { test, expect } from '@playwright/test';
import { gotoPage, mockWorkflowApis, openTaskSheet } from './fixtures/helpers';
import {
  MOCK_CLAIMS_EMPTY,
  MOCK_HEARTBEATS_EMPTY,
  MOCK_CLARIFICATIONS,
  MOCK_CLARIFICATIONS_EMPTY,
  MOCK_AGENT_ACTIVITY_STALE,
} from './fixtures/mock-data';

// Helper: open task detail and switch to a tab.
// Note: Sprint 4+ moved Clarifications/Evidence/Reviews out of Execution
// into dedicated tabs; Execution keeps claims + heartbeats + Git.
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

test.describe('Agent Workflow', () => {
  test.describe('Claim Display', () => {
    test('5.1 — shows active claim in Execution tab', async ({ page }) => {
      await gotoPage(page, '/projects/proj-1/delivery');
      await mockWorkflowApis(page);
      await openTaskSheet(page);
      await page.getByRole('tab', { name: /execution/i }).click();
      await page.waitForTimeout(300);

      // Agent name should be visible
      await expect(page.getByText('backend-developer')).toBeVisible();
      // Release claim button should be visible for an active claim
      await expect(page.getByRole('button', { name: /release claim/i })).toBeVisible();
      // Claimed timestamp should be visible ("Claimed" label + state row both match)
      await expect(page.getByText(/claimed/i).first()).toBeVisible();
    });

    test('5.1a — shows state and claimed timestamp', async ({ page }) => {
      await gotoPage(page, '/projects/proj-1/delivery');
      await mockWorkflowApis(page);
      await openTaskSheet(page);
      await page.getByRole('tab', { name: /execution/i }).click();
      await page.waitForTimeout(300);

      // State shows the claim state from the API ("claimed" = active claim)
      await expect(page.getByText('claimed', { exact: true })).toBeVisible();
      await expect(page.getByText(/claimed at|claimed/i).first()).toBeVisible();
    });

    test('5.2 — shows empty state when no claims', async ({ page }) => {
      await gotoPage(page, '/projects/proj-1/delivery');
      await mockWorkflowApis(page);
      // Override claims to return empty
      await page.route('**/api/v1/tasks/*/claims', (route) =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: MOCK_CLAIMS_EMPTY, total: 0 }) })
      );
      await openTaskSheet(page);
      await page.getByRole('tab', { name: /execution/i }).click();
      await page.waitForTimeout(300);

      await expect(page.getByText(/no agent claims/i)).toBeVisible();
      await expect(page.getByRole('button', { name: /release claim/i })).not.toBeVisible();
    });
  });

  test.describe('Heartbeats', () => {
    test('5.4 — displays heartbeat history', async ({ page }) => {
      await openTaskTab(page, /execution/i);

      // Heartbeats section heading
      await expect(sheetPanel(page).getByText('Heartbeats')).toBeVisible();
      // First heartbeat content
      await expect(page.getByText('Writing unit tests')).toBeVisible();
      await expect(page.getByText('75%')).toBeVisible();
      await expect(page.getByText(/next: integration tests/i)).toBeVisible();
    });

    test('5.4a — shows blocker in red', async ({ page }) => {
      await openTaskTab(page, /execution/i);

      // Second heartbeat has a blocker
      await expect(page.getByText('Blocker: Missing test fixtures')).toBeVisible();
    });

    test('5.4b — shows ETA when available', async ({ page }) => {
      await openTaskTab(page, /execution/i);

      // First heartbeat has ETA
      await expect(page.getByText(/eta:/i)).toBeVisible();
    });

    test('5.5 — hides heartbeats section when empty', async ({ page }) => {
      await gotoPage(page, '/projects/proj-1/delivery');
      await mockWorkflowApis(page);
      await page.route('**/api/v1/tasks/*/heartbeats', (route) =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: MOCK_HEARTBEATS_EMPTY, total: 0 }) })
      );
      await openTaskSheet(page);
      await page.getByRole('tab', { name: /execution/i }).click();
      await page.waitForTimeout(300);

      // Heartbeats section heading should NOT be visible
      await expect(page.getByText('Heartbeats')).not.toBeVisible();
    });
  });

  test.describe('Clarifications', () => {
    test('5.6 — displays clarification requests', async ({ page }) => {
      await gotoPage(page, '/projects/proj-1/delivery');
      await mockWorkflowApis(page);
      // Override to return clarifications for task-2
      await page.route('**/api/v1/tasks/task-2/clarifications', (route) =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: MOCK_CLARIFICATIONS, total: MOCK_CLARIFICATIONS.length }) })
      );
      await openTaskSheet(page);
      // Clarifications live in their own tab now
      await page.getByRole('tab', { name: 'Clarifications' }).click();
      await page.waitForTimeout(300);

      const panel = sheetPanel(page);
      // Question text should be visible
      await expect(panel.getByText(/JWT tokens expire/i)).toBeVisible();
      // Asked by
      await expect(panel.getByText('database-architect')).toBeVisible();
    });

    test('5.6a — shows blocking indicator', async ({ page }) => {
      await gotoPage(page, '/projects/proj-1/delivery');
      await mockWorkflowApis(page);
      await page.route('**/api/v1/tasks/task-2/clarifications', (route) =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: MOCK_CLARIFICATIONS, total: MOCK_CLARIFICATIONS.length }) })
      );
      await openTaskSheet(page);
      await page.getByRole('tab', { name: 'Clarifications' }).click();
      await page.waitForTimeout(300);

      // Blocking is indicated by the amber alert styling on the banner
      await expect(page.locator('[data-slot="sheet-content"]').locator('[class*="border-amber-500"]')).toBeVisible();
    });

    test('5.7 — shows empty state when no clarifications', async ({ page }) => {
      await gotoPage(page, '/projects/proj-1/delivery');
      await mockWorkflowApis(page);
      await page.route('**/api/v1/tasks/*/clarifications', (route) =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: MOCK_CLARIFICATIONS_EMPTY, total: 0 }) })
      );
      await openTaskSheet(page);
      await page.getByRole('tab', { name: 'Clarifications' }).click();
      await page.waitForTimeout(300);

      await expect(page.getByText(/no clarifications/i)).toBeVisible();
    });
  });

  test.describe('Evidence', () => {
    test('5.8 — displays evidence list', async ({ page }) => {
      await openTaskTab(page, 'Evidence');

      const panel = sheetPanel(page);
      // Evidence heading
      await expect(panel.getByText('Evidence')).toBeVisible();
      // Evidence items
      await expect(panel.getByText('Unit test results')).toBeVisible();
      await expect(panel.getByText('Git diff of changes')).toBeVisible();
      await expect(panel.getByText('42 passed, 0 failed')).toBeVisible();
    });

    test('5.8a — shows verification states', async ({ page }) => {
      await openTaskTab(page, 'Evidence');

      const panel = sheetPanel(page);
      // unverified state
      await expect(panel.getByText('unverified')).toBeVisible();
      // agent_verified state
      await expect(panel.getByText('agent_verified')).toBeVisible();
    });

    test('5.8b — shows empty state when no evidence', async ({ page }) => {
      await gotoPage(page, '/projects/proj-1/delivery');
      await mockWorkflowApis(page);
      await page.route('**/api/v1/tasks/*/evidence', (route) =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: [], total: 0 }) })
      );
      await openTaskSheet(page);
      await page.getByRole('tab', { name: 'Evidence' }).click();
      await page.waitForTimeout(300);

      // EmptyState title on the Evidence tab
      await expect(sheetPanel(page).getByText('No evidence', { exact: true })).toBeVisible();
    });
  });

  test.describe('Reviews', () => {
    test('5.9 — displays review rounds with verdict', async ({ page }) => {
      await openTaskTab(page, 'Reviews');

      const panel = sheetPanel(page);
      // Reviews heading
      await expect(panel.getByText('Reviews')).toBeVisible();
      // Reviewer name
      await expect(panel.getByText('code-quality-guard')).toBeVisible();
      // Verdict (ReviewVerdictCard renders "Approved")
      await expect(panel.getByText(/approve/i).first()).toBeVisible();
      // Confidence
      await expect(panel.getByText('92%')).toBeVisible();
      // Summary
      await expect(panel.getByText(/code quality excellent/i)).toBeVisible();
    });

    test('5.9a — shows empty state when no reviews', async ({ page }) => {
      await gotoPage(page, '/projects/proj-1/delivery');
      await mockWorkflowApis(page);
      await page.route('**/api/v1/tasks/*/review-rounds', (route) =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: [], total: 0 }) })
      );
      await openTaskSheet(page);
      await page.getByRole('tab', { name: 'Reviews' }).click();
      await page.waitForTimeout(300);

      // EmptyState title on the Reviews tab
      await expect(sheetPanel(page).getByText('No reviews', { exact: true })).toBeVisible();
    });
    // 5.10 (accept/reject buttons for pending reviews) removed: the current
    // ReviewsTab renders no verdict accept/reject controls anywhere in the UI
    // (no component passes onAccept/onReject to ReviewVerdictCard).
  });

  test.describe('Dashboard Agent Activity', () => {
    test('5.11 — shows active agents section on dashboard', async ({ page }) => {
      await gotoPage(page, '/', { workflow: true });

      const agentCard = page.locator('[data-slot="card"]').filter({ hasText: 'Active Agents' });
      await agentCard.scrollIntoViewIfNeeded();
      await expect(agentCard.getByText('Backend Developer')).toBeVisible({ timeout: 10000 });
      // Task title should be visible
      await expect(agentCard.getByText('Implement auth middleware')).toBeVisible();
    });

    test('5.12 — shows stale agent indicator', async ({ page }) => {
      await gotoPage(page, '/', {
        workflow: true,
        beforeGoto: async (p) => {
          await p.route('**/api/v1/dashboard/agent-activity', (route) =>
            route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: MOCK_AGENT_ACTIVITY_STALE, total: MOCK_AGENT_ACTIVITY_STALE.length }) })
          );
        },
      });

      const agentCard = page.locator('[data-slot="card"]').filter({ hasText: 'Active Agents' });
      await agentCard.scrollIntoViewIfNeeded();
      await expect(agentCard.getByText('Database Architect')).toBeVisible({ timeout: 10000 });
      // Stale badge rendered by AgentStatusBadge inside the card
      await expect(agentCard.getByText('Stale', { exact: true })).toBeVisible();
    });
  });
});
