import { test as setup } from '@playwright/test';

const authFile = 'tests/e2e/.auth/admin.json';

setup('authenticate', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel(/email/i).fill('admin@example.com');
  await page.getByRole('textbox', { name: 'Password' }).fill('admin123');
  await page.getByRole('button', { name: /sign in|log in|enter/i }).click();
  await page.waitForURL('**/', { timeout: 10_000 });
  await page.context().storageState({ path: authFile });
});
