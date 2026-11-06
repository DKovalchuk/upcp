import { test, expect } from '@playwright/test';
import { gotoPage } from './fixtures/helpers';

test.describe('Projects', () => {
  test('project detail page loads with overview', async ({ page }) => {
    await gotoPage(page, '/projects/proj-1');
    await expect(page.getByText('Project Details')).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Name').first()).toBeVisible();
    await expect(page.getByText('Slug').first()).toBeVisible();
  });

  test('project detail has tab navigation', async ({ page }) => {
    await gotoPage(page, '/projects/proj-1');
    await expect(page.getByRole('tab', { name: 'Overview' })).toBeVisible({ timeout: 10000 });
    await expect(page.getByRole('tab', { name: 'Structure' })).toBeVisible();
    await expect(page.getByRole('tab', { name: 'Delivery' })).toBeVisible();
    await expect(page.getByRole('tab', { name: 'Quality' })).toBeVisible();
    await expect(page.getByRole('tab', { name: 'Audit' })).toBeVisible();
  });

  test('project detail shows dates', async ({ page }) => {
    await gotoPage(page, '/projects/proj-1');
    await expect(page.getByText('Created').first()).toBeVisible({ timeout: 10000 });
    await expect(page.getByText('Updated').first()).toBeVisible();
  });

  test('tabs navigate to correct URLs', async ({ page }) => {
    await gotoPage(page, '/projects/proj-1');
    // Click Structure tab — should navigate to /projects/proj-1/structure
    await page.getByRole('tab', { name: 'Structure' }).click();
    await page.waitForTimeout(500);
    await expect(page).toHaveURL(/\/projects\/proj-1\/structure/);

    // Click Delivery tab — should navigate to /projects/proj-1/delivery
    await page.getByRole('tab', { name: 'Delivery' }).click();
    await page.waitForTimeout(500);
    await expect(page).toHaveURL(/\/projects\/proj-1\/delivery/);

    // Click Overview tab — should navigate back to /projects/proj-1
    await page.getByRole('tab', { name: 'Overview' }).click();
    await page.waitForTimeout(500);
    await expect(page).toHaveURL(/\/projects\/proj-1$/);
  });

  test('project detail has edit and delete buttons', async ({ page }) => {
    await gotoPage(page, '/projects/proj-1');
    // Header renders two icon buttons with accessible names (Pencil/Trash2 icons, no visible text)
    const editButton = page.getByRole('button', { name: 'Edit project' });
    const deleteButton = page.getByRole('button', { name: 'Delete project' });
    await expect(editButton).toBeVisible({ timeout: 10000 });
    await expect(deleteButton).toBeVisible();
  });
});
