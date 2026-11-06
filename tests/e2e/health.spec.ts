import { test, expect } from '@playwright/test';

const API = process.env.E2E_API_BASE || 'http://127.0.0.1:38080';

test.describe('Health checks', () => {
  test('backend /health returns ok', async ({ request }) => {
    const resp = await request.get(`${API}/health`);
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(body.status).toBe('ok');
    expect(body.db.status).toBe('ok');
    expect(body.redis.status).toBe('ok');
  });

  test('frontend serves HTML via nginx', async ({ page }) => {
    const resp = await page.goto('/');
    expect(resp?.status()).toBe(200);
    const title = await page.title();
    expect(title).toContain('UPCP');
  });
});
