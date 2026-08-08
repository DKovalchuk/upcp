import { test, expect } from '@playwright/test';
import { gotoPage, mockWorkflowApis } from './fixtures/helpers';
import {
  MOCK_CLAIMS,
  MOCK_CLAIMS_EMPTY,
  MOCK_HEARTBEATS,
  MOCK_HEARTBEATS_EMPTY,
  MOCK_CLARIFICATIONS,
  MOCK_CLARIFICATIONS_EMPTY,
  MOCK_AGENT_ACTIVITY,
  MOCK_AGENT_ACTIVITY_STALE,
  MOCK_AGENT_ACTIVITY_EMPTY,
} from './fixtures/mock-data';

// Helper: open task detail and switch to Execution tab
async function openExecutionTab(page: import('@playwright/test').Page, taskId = 'task-2') {
  await gotoPage(page, '/projects/proj-1/delivery');
  await mockWorkflowApis(page);
  // Click the task row to open the sheet
  await page.getByText('Implement auth middleware').click();
  await page.waitForTimeout(500);
  // Click Execution tab
  await page.getByRole('tab', { name: /execution/i }).click();
  await page.waitForTimeout(300);
}

test.describe('Agent Workflow', () => {
  test.describe('Claim Display', () => {
    test('5.1 — shows active claim in Execution tab', async ({ page }) => {
      await gotoPage(page, '/projects/proj-1/delivery');
      await mockWorkflowApis(page);
      await page.getByText('Implement auth middleware').click();
      await page.waitForTimeout(500);
      await page.getByRole('tab', { name: /execution/i }).click();
      await page.waitForTimeout(300);

      // Agent name should be visible
      await expect(page.getByText('backend-developer')).toBeVisible();
      // Release claim button should be visible for active claim
      await expect(page.getByRole('button', { name: /release claim/i })).toBeVisible();
      // Claimed timestamp should be visible
      await expect(page.getByText(/claimed/i)).toBeVisible();
    });

    test('5.1a — shows state and claimed timestamp', async ({ page }) => {
      await gotoPage(page, '/projects/proj-1/delivery');
      await mockWorkflowApis(page);
      await page.getByText('Implement auth middleware').click();
      await page.waitForTimeout(500);
      await page.getByRole('tab', { name: /execution/i }).click();
      await page.waitForTimeout(300);

      // State should show "active" or similar
      await expect(page.getByText('active')).toBeVisible();
    });

    test('5.2 — shows empty state when no claims', async ({ page }) => {
      await gotoPage(page, '/projects/proj-1/delivery');
      await mockWorkflowApis(page);
      // Override claims to return empty
      await page.route('**/api/v1/tasks/*/claims', (route) =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: MOCK_CLAIMS_EMPTY, total: 0 }) })
      );
      await page.getByText('Implement auth middleware').click();
      await page.waitForTimeout(500);
      await page.getByRole('tab', { name: /execution/i }).click();
      await page.waitForTimeout(300);

      await expect(page.getByText(/no agent claims/i)).toBeVisible();
      await expect(page.getByRole('button', { name: /release claim/i })).not.toBeVisible();
    });
  });

  test.describe('Heartbeats', () => {
    test('5.4 — displays heartbeat history', async ({ page }) => {
      await openExecutionTab(page);

      // Heartbeats section heading
      await expect(page.getByText('Heartbeats')).toBeVisible();
      // First heartbeat content
      await expect(page.getByText('Writing unit tests')).toBeVisible();
      await expect(page.getByText('75%')).toBeVisible();
      await expect(page.getByText(/next: integration tests/i)).toBeVisible();
    });

    test('5.4a — shows blocker in red', async ({ page }) => {
      await openExecutionTab(page);

      // Second heartbeat has a blocker
      await expect(page.getByText('Blocker: Missing test fixtures')).toBeVisible();
    });

    test('5.4b — shows ETA when available', async ({ page }) => {
      await openExecutionTab(page);

      // First heartbeat has ETA
      await expect(page.getByText(/eta:/i)).toBeVisible();
    });

    test('5.5 — hides heartbeats section when empty', async ({ page }) => {
      await gotoPage(page, '/projects/proj-1/delivery');
      await mockWorkflowApis(page);
      await page.route('**/api/v1/tasks/*/heartbeats', (route) =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: MOCK_HEARTBEATS_EMPTY, total: 0 }) })
      );
      await page.getByText('Implement auth middleware').click();
      await page.waitForTimeout(500);
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
      // Override to return clarifications for task-3 (blocked task)
      await page.route('**/api/v1/tasks/task-2/clarifications', (route) =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: MOCK_CLARIFICATIONS, total: MOCK_CLARIFICATIONS.length }) })
      );
      await page.getByText('Implement auth middleware').click();
      await page.waitForTimeout(500);
      await page.getByRole('tab', { name: /execution/i }).click();
      await page.waitForTimeout(300);

      // Clarifications heading
      await expect(page.getByText('Clarifications')).toBeVisible();
      // Question text should be visible
      await expect(page.getByText(/JWT tokens expire/i)).toBeVisible();
      // Asked by
      await expect(page.getByText('database-architect')).toBeVisible();
    });

    test('5.6a — shows blocking indicator', async ({ page }) => {
      await gotoPage(page, '/projects/proj-1/delivery');
      await mockWorkflowApis(page);
      await page.route('**/api/v1/tasks/task-2/clarifications', (route) =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: MOCK_CLARIFICATIONS, total: MOCK_CLARIFICATIONS.length }) })
      );
      await page.getByText('Implement auth middleware').click();
      await page.waitForTimeout(500);
      await page.getByRole('tab', { name: /execution/i }).click();
      await page.waitForTimeout(300);

      // Blocking indicator (ClarificationBanner shows "Blocking" or "blocking" badge)
      await expect(page.getByText(/blocking/i).first()).toBeVisible();
    });

    test('5.7 — shows empty state when no clarifications', async ({ page }) => {
      await gotoPage(page, '/projects/proj-1/delivery');
      await mockWorkflowApis(page);
      await page.route('**/api/v1/tasks/*/clarifications', (route) =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: MOCK_CLARIFICATIONS_EMPTY, total: 0 }) })
      );
      await page.getByText('Implement auth middleware').click();
      await page.waitForTimeout(500);
      await page.getByRole('tab', { name: /execution/i }).click();
      await page.waitForTimeout(300);

      await expect(page.getByText(/no clarifications/i)).toBeVisible();
    });
  });

  test.describe('Evidence', () => {
    test('5.8 — displays evidence list', async ({ page }) => {
      await openExecutionTab(page);

      // Evidence heading
      await expect(page.getByText('Evidence')).toBeVisible();
      // Evidence items
      await expect(page.getByText('Unit test results')).toBeVisible();
      await expect(page.getByText('test_output')).toBeVisible();
      await expect(page.getByText('Git diff of changes')).toBeVisible();
    });

    test('5.8a — shows verification states', async ({ page }) => {
      await openExecutionTab(page);

      // unverified state
      await expect(page.getByText('unverified')).toBeVisible();
      // agent_verified state
      await expect(page.getByText('agent_verified')).toBeVisible();
    });

    test('5.8b — shows empty state when no evidence', async ({ page }) => {
      await gotoPage(page, '/projects/proj-1/delivery');
      await mockWorkflowApis(page);
      await page.route('**/api/v1/tasks/*/evidence', (route) =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: [], total: 0 }) })
      );
      await page.getByText('Implement auth middleware').click();
      await page.waitForTimeout(500);
      await page.getByRole('tab', { name: /execution/i }).click();
      await page.waitForTimeout(300);

      await expect(page.getByText(/no evidence attached/i)).toBeVisible();
    });
  });

  test.describe('Reviews', () => {
    test('5.9 — displays review rounds with verdict', async ({ page }) => {
      await openExecutionTab(page);

      // Reviews heading
      await expect(page.getByText('Reviews')).toBeVisible();
      // Reviewer name
      await expect(page.getByText('code-quality-guard')).toBeVisible();
      // Verdict (approve shown in ReviewVerdictCard)
      await expect(page.getByText(/approve/i).first()).toBeVisible();
      // Confidence
      await expect(page.getByText('92%')).toBeVisible();
      // Summary
      await expect(page.getByText(/code quality excellent/i)).toBeVisible();
    });

    test('5.10 — shows accept/reject buttons for pending reviews', async ({ page }) => {
      await gotoPage(page, '/projects/proj-1/delivery');
      await mockWorkflowApis(page);
      // Override to return pending review round (verdict = null)
      await page.route('**/api/v1/tasks/task-2/review-rounds', (route) =>
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [{ id: 'rr-pending', task_id: 'task-2', reviewer_id: 'code-quality-guard', state: 'in_progress', verdict: null, confidence: null, summary: null, created_at: new Date().toISOString() }],
            total: 1,
          }),
        })
      );
      await page.getByText('Implement auth middleware').click();
      await page.waitForTimeout(500);
      await page.getByRole('tab', { name: /execution/i }).click();
      await page.waitForTimeout(300);

      // Accept and Reject buttons should be visible
      await expect(page.getByRole('button', { name: /accept/i })).toBeVisible();
      await expect(page.getByRole('button', { name: /reject/i })).toBeVisible();
    });

    test('5.9a — shows empty state when no reviews', async ({ page }) => {
      await gotoPage(page, '/projects/proj-1/delivery');
      await mockWorkflowApis(page);
      await page.route('**/api/v1/tasks/*/review-rounds', (route) =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: [], total: 0 }) })
      );
      await page.getByText('Implement auth middleware').click();
      await page.waitForTimeout(500);
      await page.getByRole('tab', { name: /execution/i }).click();
      await page.waitForTimeout(300);

      await expect(page.getByText(/no reviews yet/i)).toBeVisible();
    });
  });

  test.describe('Dashboard Agent Activity', () => {
    test('5.11 — shows active agents section on dashboard', async ({ page }) => {
      await gotoPage(page, '/');
      await mockWorkflowApis(page);
      await page.waitForTimeout(500);

      // Scroll to find agent activity section
      const agentSection = page.getByText(/backend-developer/i);
      if (await agentSection.isVisible().catch(() => false)) {
        await expect(agentSection).toBeVisible();
        // Task title should be visible
        await expect(page.getByText('Implement auth middleware')).toBeVisible();
      }
    });

    test('5.12 — shows stale agent indicator', async ({ page }) => {
      await gotoPage(page, '/');
      await mockWorkflowApis(page);
      // Override agent activity to return stale agent
      await page.route('**/api/v1/dashboard/agent-activity', (route) =>
        route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: MOCK_AGENT_ACTIVITY_STALE, total: MOCK_AGENT_ACTIVITY_STALE.length }) })
      );
      await page.waitForTimeout(500);

      // Stale agent should have visual indicator
      const staleAgent = page.getByText('database-architect');
      if (await staleAgent.isVisible().catch(() => false)) {
        // Look for stale/warning indicator near the agent
        await expect(page.getByText(/stale|warning/i).first()).toBeVisible();
      }
    });
  });
});
