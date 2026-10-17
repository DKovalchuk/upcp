import { test, expect } from '@playwright/test';
import { gotoPage } from './fixtures/helpers';
import {
  MOCK_AGENT_ACTIVITY_STALE,
  MOCK_AGENT_ACTIVITY_EMPTY,
} from './fixtures/mock-data';

test.describe('Dashboard', () => {
  // KPI labels after the dashboard redesign (SPEC-0025): the old
  // "Tasks In Progress" / "Tasks Done" cards were replaced.
  test('shows stat cards', async ({ page }) => {
    await gotoPage(page, '/');
    await expect(page.getByText('Active Tasks', { exact: true })).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Done This Week', { exact: true })).toBeVisible();
    await expect(page.getByText('Health Score', { exact: true })).toBeVisible();
  });

  test('shows Needs Attention section', async ({ page }) => {
    // workflow:true loads attention data so section titles don't collide
    // with their empty-state messages ("No open questions", case-insensitive)
    await gotoPage(page, '/', { workflow: true });
    const el = page.getByText('Needs Your Review');
    await el.scrollIntoViewIfNeeded();
    await expect(el).toBeVisible({ timeout: 10000 });
    // CardTitle carries a count badge → substring match, not exact
    await expect(page.getByText('Open Questions')).toBeVisible();
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
    // Scope to the LiveActivityFeed card — MOCK_DASHBOARD_STATS.recent_activity
    // renders as actor badge + entity link rows.
    const feedCard = page.locator('[data-slot="card"]').filter({ hasText: 'Recent Activity' });
    await feedCard.scrollIntoViewIfNeeded();
    await expect(feedCard.getByText('code-quality-guard')).toBeVisible({ timeout: 10000 });
    await expect(feedCard.getByText('task-1')).toBeVisible();
    await expect(feedCard.getByText('No recent activity')).toHaveCount(0);
  });
});

test.describe('Dashboard — Agent Activity', () => {
  // workflow:true registers agent-activity mocks BEFORE navigation — the
  // query has staleTime/refetchInterval of 30s, so post-load registration
  // would leave the section empty for the whole test.
  test('5.11 — shows active agent with task info', async ({ page }) => {
    await gotoPage(page, '/', { workflow: true });

    const agentCard = page.locator('[data-slot="card"]').filter({ hasText: 'Active Agents' });
    await agentCard.scrollIntoViewIfNeeded();
    await expect(agentCard.getByText('Backend Developer')).toBeVisible({ timeout: 10000 });
    // Task title should be visible
    await expect(agentCard.getByText('Implement auth middleware')).toBeVisible();
  });

  test('5.11a — shows agent progress indicator', async ({ page }) => {
    await gotoPage(page, '/', { workflow: true });

    const agentCard = page.locator('[data-slot="card"]').filter({ hasText: 'Active Agents' });
    await agentCard.scrollIntoViewIfNeeded();
    // Progress should be visible (65%)
    await expect(agentCard.getByText('65%')).toBeVisible({ timeout: 10000 });
  });

  test('5.12 — shows stale agent with warning indicator', async ({ page }) => {
    await gotoPage(page, '/', {
      workflow: true,
      // Stale override registered before navigation → wins LIFO at initial fetch
      beforeGoto: async (p) => {
        await p.route('**/api/v1/dashboard/agent-activity', (route) =>
          route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: MOCK_AGENT_ACTIVITY_STALE, total: MOCK_AGENT_ACTIVITY_STALE.length }) })
        );
      },
    });

    const agentCard = page.locator('[data-slot="card"]').filter({ hasText: 'Active Agents' });
    await agentCard.scrollIntoViewIfNeeded();
    await expect(agentCard.getByText('Database Architect')).toBeVisible({ timeout: 10000 });
    // Stale indicator (AgentStatusBadge renders "Stale" inside the card)
    await expect(agentCard.getByText('Stale', { exact: true })).toBeVisible();
  });

  test('5.12a — shows empty state when no active agents', async ({ page }) => {
    await gotoPage(page, '/', {
      workflow: true,
      beforeGoto: async (p) => {
        await p.route('**/api/v1/dashboard/agent-activity', (route) =>
          route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: MOCK_AGENT_ACTIVITY_EMPTY, total: 0 }) })
        );
      },
    });

    const agentCard = page.locator('[data-slot="card"]').filter({ hasText: 'Active Agents' });
    await agentCard.scrollIntoViewIfNeeded();
    await expect(agentCard.getByText('No active agents')).toBeVisible({ timeout: 10000 });
  });
});

test.describe('Dashboard — Notifications', () => {
  test('notification bell shows unread count', async ({ page }) => {
    await gotoPage(page, '/');

    // NotificationBell is in the topbar; unread-count mock returns {count: 2}
    const bellButton = page.getByRole('button', { name: /notifications/i });
    await expect(bellButton).toBeVisible({ timeout: 10000 });
    await expect(bellButton.locator('span').first()).toHaveText('2');
  });

  test('notification dropdown shows items', async ({ page }) => {
    await gotoPage(page, '/');

    const bellButton = page.getByRole('button', { name: /notifications/i });
    await expect(bellButton).toBeVisible({ timeout: 10000 });
    await bellButton.click();

    // Notification items from MOCK_NOTIFICATIONS
    await expect(page.getByText('Task claimed')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Clarification requested')).toBeVisible();
  });
});

test.describe('Dashboard — Attention Sections', () => {
  test('needs review section shows pending reviews', async ({ page }) => {
    await gotoPage(page, '/', { workflow: true });
    const needsReview = page.getByText('Needs Your Review');
    await needsReview.scrollIntoViewIfNeeded();
    await expect(needsReview).toBeVisible({ timeout: 10000 });
  });

  test('open questions section shows pending clarifications', async ({ page }) => {
    await gotoPage(page, '/', { workflow: true });
    const openQuestions = page.getByText('Open Questions');
    await openQuestions.scrollIntoViewIfNeeded();
    await expect(openQuestions).toBeVisible({ timeout: 10000 });
  });

  test('blocked tasks section shows blocked items', async ({ page }) => {
    await gotoPage(page, '/', { workflow: true });
    const blocked = page.getByText('Blocked Tasks');
    await blocked.scrollIntoViewIfNeeded();
    await expect(blocked).toBeVisible({ timeout: 10000 });
  });
});
