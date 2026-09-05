import { test, expect } from '@playwright/test';

const API = 'http://127.0.0.1:38080';

let token: string;

test.beforeAll(async ({ request }) => {
  const resp = await request.post(`${API}/auth/login`, {
    data: { email: 'admin@example.com', password: 'admin123' },
  });
  token = (await resp.json()).access_token;
});

function authHeaders() {
  return { Authorization: `Bearer ${token}` };
}

test.describe('Projects API', () => {
  test('GET /api/v1/projects returns list', async ({ request }) => {
    const resp = await request.get(`${API}/api/v1/projects`, { headers: authHeaders() });
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(body.items.length).toBeGreaterThan(0);
  });

  test('project has required fields', async ({ request }) => {
    const resp = await request.get(`${API}/api/v1/projects`, { headers: authHeaders() });
    const { items } = await resp.json();
    const project = items[0];
    expect(project).toHaveProperty('id');
    expect(project).toHaveProperty('name');
    expect(project).toHaveProperty('status');
  });
});

test.describe('Dashboard API', () => {
  test('GET /api/v1/dashboard/stats returns counts', async ({ request }) => {
    const resp = await request.get(`${API}/api/v1/dashboard/stats`, { headers: authHeaders() });
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(body.project_count).toBeGreaterThan(0);
    expect(body.task_counts_by_status).toBeDefined();
  });
});

test.describe('Agents API', () => {
  test('GET /api/v1/agents returns data', async ({ request }) => {
    const resp = await request.get(`${API}/api/v1/agents`, { headers: authHeaders() });
    expect(resp.ok()).toBeTruthy();
    const body = await resp.json();
    expect(body).toBeDefined();
  });
});

test.describe('OpenAPI spec', () => {
  test('/openapi.json is accessible and valid', async ({ request }) => {
    const resp = await request.get(`${API}/openapi.json`);
    expect(resp.ok()).toBeTruthy();
    const spec = await resp.json();
    expect(spec.openapi).toBeDefined();
    expect(spec.paths).toBeDefined();
    expect(Object.keys(spec.paths).length).toBeGreaterThan(50);
  });
});

test.describe('Metrics endpoint', () => {
  test('GET /metrics returns prometheus text', async ({ request }) => {
    const resp = await request.get(`${API}/metrics`);
    expect(resp.ok()).toBeTruthy();
    const text = await resp.text();
    expect(text).toContain('# HELP');
    expect(text).toContain('http_requests');
  });
});
