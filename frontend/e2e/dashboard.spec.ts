import { test, expect, type Page } from '@playwright/test';
import { gotoPage } from './fixtures/helpers';
import {
  MOCK_AGENT_ACTIVITY_STALE,
  MOCK_AGENT_ACTIVITY_EMPTY,
  MOCK_ATTENTION,
} from './fixtures/mock-data';

// Attention section title locator that is valid in BOTH section states:
// with data the CardTitle text carries a count badge ("Open Questions 2"),
// empty it collides case-insensitively with the empty-state ("No open
// questions") — plain getByText broke schedule quality gate #515.
const attentionTitle = (page: Page, sectionText: string) =>
  page
    .locator('[data-slot="card"]')
    .filter({ hasText: sectionText })
    .locator('[data-slot="card-title"]');

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
    // workflow:true loads attention data; the card-scoped title locator
    // stays valid whether sections carry data or render empty-states.
    await gotoPage(page, '/', { workflow: true });
    const el = attentionTitle(page, 'Needs Your Review');
    await el.scrollIntoViewIfNeeded();
    await expect(el).toContainText('Needs Your Review', { timeout: 10000 });
    await expect(attentionTitle(page, 'Open Questions')).toContainText('Open Questions');
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
  // Titles resolve via attentionTitle(): plain getByText hit strict-mode
  // violations in schedule quality gate #515 (2026-10-31, e2e_fe=1) —
  // substring collides with empty-states, exact collides with count badges.
  test('needs review section shows pending reviews', async ({ page }) => {
    await gotoPage(page, '/', { workflow: true });
    const needsReview = attentionTitle(page, 'Needs Your Review');
    await needsReview.scrollIntoViewIfNeeded();
    await expect(needsReview).toContainText('Needs Your Review', { timeout: 10000 });
  });

  test('open questions section shows pending clarifications', async ({ page }) => {
    await gotoPage(page, '/', { workflow: true });
    const openQuestions = attentionTitle(page, 'Open Questions');
    await openQuestions.scrollIntoViewIfNeeded();
    await expect(openQuestions).toContainText('Open Questions', { timeout: 10000 });
  });

  test('blocked tasks section shows blocked items', async ({ page }) => {
    await gotoPage(page, '/', { workflow: true });
    const blocked = attentionTitle(page, 'Blocked Tasks');
    await blocked.scrollIntoViewIfNeeded();
    await expect(blocked).toContainText('Blocked Tasks', { timeout: 10000 });
  });

  test('empty sections: title stays unique while empty-state collides for substring locators', async ({
    page,
  }) => {
    // Force every attention section empty (LIFO override of workflow mocks).
    const emptyAttention = Object.fromEntries(Object.keys(MOCK_ATTENTION).map((k) => [k, []]));
    await gotoPage(page, '/', {
      workflow: true,
      beforeGoto: async (p) => {
        await p.route('**/api/v1/dashboard/attention*', (route) =>
          route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(emptyAttention),
          })
        );
      },
    });

    // The #515 trap: the raw substring matcher sees title AND empty-state.
    await expect(page.getByText('Open Questions')).toHaveCount(2);
    // Robust locator: exactly one card title, and the empty-state shows.
    const title = attentionTitle(page, 'Open Questions');
    await expect(title).toHaveCount(1);
    await expect(title).toContainText('Open Questions');
    await expect(page.getByText('No open questions', { exact: true })).toBeVisible();
    await expect(attentionTitle(page, 'Blocked Tasks')).toHaveCount(1);
    await expect(page.getByText('No blocked tasks', { exact: true })).toBeVisible();
  });
});
