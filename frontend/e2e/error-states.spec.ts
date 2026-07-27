import { test, expect } from '@playwright/test';
import { gotoPage } from './fixtures/helpers';

test.describe('Error & Empty States', () => {
  test('404 page shows for unknown routes', async ({ page }) => {
    await gotoPage(page, '/completely-unknown-route');
    await expect(page.getByText(/404|not found/i).first()).toBeVisible({ timeout: 10000 });
  });

  test('error boundary shows on API failure', async ({ page }) => {
    await page.route('**/api/v1/dashboard/stats', (route) =>
      route.fulfill({ status: 500, contentType: 'application/json', body: JSON.stringify({ error: 'Internal Server Error' }) })
    );
    await gotoPage(page, '/');
    await expect(page.getByText(/error|failed/i).first()).toBeVisible({ timeout: 10000 });
  });
});
