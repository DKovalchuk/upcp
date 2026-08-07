import { test, expect } from '@playwright/test';

test.describe('Navigation Flow', () => {
  test('login page renders correctly', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible({ timeout: 10000 });
    const inputs = page.locator('input');
    const count = await inputs.count();
    expect(count).toBeGreaterThanOrEqual(2);
  });

  test('login page has password visibility toggle', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    const passwordInput = page.getByRole('textbox', { name: 'Password' });
    await expect(passwordInput).toBeVisible({ timeout: 5000 });
    await expect(passwordInput).toHaveAttribute('type', 'password');
    const toggle = page.getByLabel('Show password');
    await toggle.click();
    await expect(passwordInput).toHaveAttribute('type', 'text');
  });

  test('login shows error on invalid credentials', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    const emailInput = page.locator('input[type="email"]');
    const passwordInput = page.locator('input[type="password"]');
    await emailInput.fill('wrong@example.com');
    await passwordInput.fill('wrongpassword');
    await page.getByRole('button', { name: /sign in/i }).click();

    await expect(page.getByText(/invalid|incorrect|error|fail/i)).toBeVisible({ timeout: 10000 });
  });
});

test.describe('Responsive Design', () => {
  test('login form is usable on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    const inputs = page.locator('input');
    const count = await inputs.count();
    expect(count).toBeGreaterThanOrEqual(2);
    await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible();
  });
});

test.describe('Accessibility', () => {
  test('login page has proper input types', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    const emailInput = page.locator('input[type="email"]');
    const passwordInput = page.locator('input[type="password"]');

    await expect(emailInput).toBeVisible();
    await expect(passwordInput).toBeVisible();
  });

  test('password toggle is keyboard accessible', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    const passwordInput = page.getByRole('textbox', { name: 'Password' });
    await passwordInput.focus();

    // Tab to toggle button
    await page.keyboard.press('Tab');
    const toggle = page.getByLabel('Show password');
    if (await toggle.isVisible().catch(() => false)) {
      await page.keyboard.press('Enter');
      await expect(passwordInput).toHaveAttribute('type', 'text');
    }
  });
});
