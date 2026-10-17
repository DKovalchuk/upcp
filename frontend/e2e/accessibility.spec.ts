import { test, expect } from '@playwright/test';
import { gotoDashboard, tabUntilFocused } from './fixtures/dashboard-fixtures';

// Uses the new dashboard fixture (the legacy gotoPage catch-all intercepted
// /src/lib/api/index.ts and left the app unmounted — see dashboard-fixtures.ts).

test.describe('Accessibility', () => {
  test('main content has id for skip link', async ({ page }) => {
    await gotoDashboard(page, '/');
    const main = page.locator('#main-content');
    await expect(main).toBeVisible();
  });

  test('skip-to-content link exists', async ({ page }) => {
    await gotoDashboard(page, '/');
    const skipLink = page.getByText('Skip to main content');
    await expect(skipLink).toHaveAttribute('href', '#main-content');
  });

  test('headings follow hierarchy', async ({ page }) => {
    await gotoDashboard(page, '/');
    const h1 = await page.locator('h1').count();
    expect(h1).toBeLessThanOrEqual(1);
  });

  test('tables have proper structure', async ({ page }) => {
    await gotoDashboard(page, '/projects/proj-1');
    const tables = page.locator('table');
    const tableCount = await tables.count();
    if (tableCount > 0) {
      await expect(tables.first().locator('thead')).toBeVisible();
      await expect(tables.first().locator('tbody')).toBeVisible();
    }
  });

  test('badges have text content', async ({ page }) => {
    await gotoDashboard(page, '/');
    const badges = page.locator('[data-slot="badge"]');
    const count = await badges.count();
    for (let i = 0; i < Math.min(count, 10); i++) {
      const badge = badges.nth(i);
      const text = await badge.textContent();
      expect(text?.trim().length).toBeGreaterThan(0);
    }
  });

  test('interactive elements are focusable', async ({ page }) => {
    await gotoDashboard(page, '/');
    for (let i = 0; i < 5; i++) {
      await page.keyboard.press('Tab');
    }
    const focused = await page.evaluate(() => document.activeElement?.tagName);
    expect(focused).toBeTruthy();
  });

  test('links have accessible names', async ({ page }) => {
    await gotoDashboard(page, '/');
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

test.describe('Dashboard accessibility — TASK-0128 D1–D8', () => {
  test('D1: KPI cards expose aria-labels describing value and action', async ({ page }) => {
    // project_id set → all 5 KPI cards are links (incl. Health Score)
    await gotoDashboard(page, '/?project_id=proj-1');
    const kpiRow = page.locator('#main-content [class*="lg:grid-cols-5"]');
    // wait for scoped KPI data first (guards against slow module transforms)
    await expect(kpiRow.getByText('91%', { exact: true })).toBeVisible({ timeout: 15000 });
    const links = kpiRow.locator('a');
    await expect(links).toHaveCount(5, { timeout: 15000 });
    const labels = ['Projects', 'Active Tasks', 'Done This Week', 'Blocked', 'Health Score'];
    for (let i = 0; i < labels.length; i++) {
      await expect(links.nth(i)).toHaveAttribute(
        'aria-label',
        new RegExp(`^${labels[i]}: .+, click to view$`)
      );
    }
  });

  test('D2: donut sectors expose aria-labels with status, count and action', async ({ page }) => {
    await gotoDashboard(page, '/');
    await expect(page.locator('.recharts-pie-sector').first()).toBeVisible({ timeout: 10000 });
    // every non-zero-status sector path carries an aria-label
    const labeled = await page.locator('.recharts-pie-sector path[aria-label]').count();
    expect(labeled).toBe(5);
    await expect(page.locator('path[aria-label="Done: 12 tasks, click to filter"]')).toHaveCount(1);
  });

  test('D3: attention items are keyboard navigable (Tab + Enter)', async ({ page }) => {
    await gotoDashboard(page, '/');
    const firstReviewLink = page
      .locator('[data-slot="card"]')
      .filter({ hasText: 'Needs Your Review' })
      .locator('a[href="/projects/proj-1/delivery"]')
      .first();
    await expect(firstReviewLink).toBeVisible({ timeout: 10000 });
    const reached = await tabUntilFocused(page, firstReviewLink);
    expect(reached).toBe(true);
    await page.keyboard.press('Enter');
    await expect(page).toHaveURL(/\/projects\/proj-1\/delivery/);
  });

  test('D4: portfolio rows are keyboard navigable (Tab + Enter)', async ({ page }) => {
    await gotoDashboard(page, '/');
    const portfolio = page.locator('[data-slot="card"]').filter({ has: page.locator('table') });
    await expect(portfolio).toBeVisible({ timeout: 10000 });
    const firstRowLink = portfolio.locator('a[href="/projects/proj-1"]').first();
    const reached = await tabUntilFocused(page, firstRowLink);
    expect(reached).toBe(true);
    await page.keyboard.press('Enter');
    await expect(page).toHaveURL(/\/projects\/proj-1$/);
  });

  test('D5: health is conveyed by text, not color alone', async ({ page }) => {
    await gotoDashboard(page, '/');
    // KPI health value is textual
    const kpiRow = page.locator('#main-content [class*="lg:grid-cols-5"]');
    await expect(kpiRow.getByText(/\d+%/).first()).toBeVisible();
    // portfolio health cell pairs the colored bar with a numeric percentage
    const portfolio = page.locator('[data-slot="card"]').filter({ has: page.locator('table') });
    await expect(portfolio.getByText(/\d+%/).first()).toBeVisible({ timeout: 10000 });
  });

  test('D6: heading hierarchy on dashboard is sequential from h1', async ({ page }) => {
    await gotoDashboard(page, '/');
    await expect(page.locator('#main-content').getByText('Needs Attention')).toBeVisible({ timeout: 10000 });
    const levels = await page.evaluate(() =>
      Array.from(document.querySelectorAll('h1,h2,h3,h4,h5,h6')).map((h) => Number(h.tagName[1]))
    );
    expect(levels.length).toBeGreaterThanOrEqual(2);
    expect(levels[0]).toBe(1);
    for (let i = 1; i < levels.length; i++) {
      expect(levels[i], `heading level jump at index ${i}`).toBeLessThanOrEqual(levels[i - 1] + 1);
    }
  });

  test('D7: focused interactive elements have a visible focus indicator', async ({ page }) => {
    await gotoDashboard(page, '/');
    // keyboard-focused skip link (global :focus-visible rule)
    await page.keyboard.press('Tab');
    const focus1 = await page.evaluate(() => {
      const el = document.activeElement as HTMLElement;
      const cs = getComputedStyle(el);
      return { tag: el.tagName, outlineStyle: cs.outlineStyle, boxShadow: cs.boxShadow };
    });
    expect(focus1.tag).toBe('A');
    expect(focus1.outlineStyle === 'solid' || focus1.boxShadow !== 'none').toBe(true);

    // keyboard-focused KPI card link
    const kpiLink = page
      .locator('#main-content [class*="lg:grid-cols-5"] a')
      .first();
    const reached = await tabUntilFocused(page, kpiLink);
    expect(reached).toBe(true);
    const focus2 = await kpiLink.evaluate((el) => {
      const cs = getComputedStyle(el);
      return { outlineStyle: cs.outlineStyle, boxShadow: cs.boxShadow };
    });
    expect(focus2.outlineStyle === 'solid' || focus2.boxShadow !== 'none').toBe(true);
  });

  test('D8: chart data is available as text (legend and axis labels)', async ({ page }) => {
    await gotoDashboard(page, '/');
    const donut = page
      .locator('[data-slot="card"]')
      .filter({ hasText: 'Task Distribution' });
    await expect(donut).toBeVisible({ timeout: 10000 });
    // text fallback: every non-zero status name + count rendered as text
    for (const [name, count] of [
      ['Backlog', '5'],
      ['In Progress', '3'],
      ['Review', '2'],
      ['Done', '12'],
      ['Blocked', '2'],
    ]) {
      const legendBtn = donut.getByRole('button', { name: new RegExp(name) });
      await expect(legendBtn).toBeVisible();
      await expect(legendBtn.getByText(count, { exact: true })).toBeVisible();
    }
    // velocity axis labels are real text nodes
    const velocity = page
      .locator('[data-slot="card"]')
      .filter({ hasText: 'Velocity (8 weeks)' });
    const hasWeekLabel = await velocity.evaluate((el) =>
      Array.from(el.querySelectorAll('svg text')).some((t) => /W\d{2}/.test(t.textContent ?? ''))
    );
    expect(hasWeekLabel).toBe(true);
  });
});
