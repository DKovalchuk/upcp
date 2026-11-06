import { test as setup } from '@playwright/test';

const authFile = 'tests/e2e/.auth/admin.json';
// Default = dev-stack admin password; the CI gate points at the seeded test
// stack and passes E2E_ADMIN_PASSWORD=TestAdmin123! (TASK-0143)
const adminPassword = process.env.E2E_ADMIN_PASSWORD || 'admin123';

setup('authenticate', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel(/email/i).fill('admin@example.com');
  await page.getByRole('textbox', { name: 'Password' }).fill(adminPassword);
  await page.getByRole('button', { name: /sign in|log in|enter/i }).click();
  await page.waitForURL('**/', { timeout: 10_000 });
  await page.context().storageState({ path: authFile });
});
