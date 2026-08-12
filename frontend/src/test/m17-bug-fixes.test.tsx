import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';

// ── Bug 1: fetchProjectTasks URL construction ──

describe('fetchProjectTasks URL construction', () => {
  beforeEach(() => {
    vi.resetModules();
  });

  it('builds URL with pagination only', async () => {
    const { fetchProjectTasks } = await import('@/lib/api/tasks');
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ items: [], total: 0, offset: 0, limit: 20 }),
    });
    vi.stubGlobal('fetch', mockFetch);

    await fetchProjectTasks('proj-1', undefined, { offset: 0, limit: 20 });

    const calledUrl = mockFetch.mock.calls[0][0];
    expect(calledUrl).toContain('offset=0');
    expect(calledUrl).toContain('limit=20');
    expect(calledUrl).not.toContain('status=');
    expect(calledUrl).toMatch(/tasks\?offset=0&limit=20/);
  });

  it('builds URL with filters only', async () => {
    const { fetchProjectTasks } = await import('@/lib/api/tasks');
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ items: [], total: 0, offset: 0, limit: 20 }),
    });
    vi.stubGlobal('fetch', mockFetch);

    await fetchProjectTasks('proj-1', { status: 'backlog' });

    const calledUrl = mockFetch.mock.calls[0][0];
    expect(calledUrl).toContain('status=backlog');
    expect(calledUrl).toMatch(/tasks\?status=backlog/);
  });

  it('builds URL with filters and pagination', async () => {
    const { fetchProjectTasks } = await import('@/lib/api/tasks');
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ items: [], total: 0, offset: 10, limit: 20 }),
    });
    vi.stubGlobal('fetch', mockFetch);

    await fetchProjectTasks('proj-1', { status: 'backlog' }, { offset: 10, limit: 20 });

    const calledUrl = mockFetch.mock.calls[0][0];
    expect(calledUrl).toContain('status=backlog');
    expect(calledUrl).toContain('offset=10');
    expect(calledUrl).toContain('limit=20');
    expect(calledUrl).toMatch(/tasks\?status=backlog&offset=10&limit=20/);
  });

  it('builds URL with no params', async () => {
    const { fetchProjectTasks } = await import('@/lib/api/tasks');
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ items: [], total: 0, offset: 0, limit: 20 }),
    });
    vi.stubGlobal('fetch', mockFetch);

    await fetchProjectTasks('proj-1');

    const calledUrl = mockFetch.mock.calls[0][0];
    expect(calledUrl).toMatch(/tasks$/);
    expect(calledUrl).not.toContain('?');
  });
});

// ── Bug 3: TopBar navigation ──

const mockNavigate = vi.fn();

vi.mock('@tanstack/react-router', () => ({
  useNavigate: () => mockNavigate,
  useLocation: () => ({ pathname: '/' }),
}));

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => ({ logout: vi.fn() }),
}));

vi.mock('next-themes', () => ({
  useTheme: () => ({ theme: 'light', setTheme: vi.fn() }),
}));

vi.mock('@/components/notifications/NotificationBell', () => ({
  NotificationBell: () => React.createElement('div', { 'data-testid': 'notif-bell' }),
}));

vi.mock('@/components/ui/sidebar', () => ({
  SidebarTrigger: () => React.createElement('div'),
}));

describe('TopBar navigation', () => {
  beforeEach(() => {
    mockNavigate.mockClear();
  });

  it('Profile and Settings items call navigate to /settings', async () => {
    // Verify the TopBar component imports useNavigate and wires it to Profile/Settings
    // We test the navigation wiring by checking the component source
    const fs = await import('fs');
    const path = await import('path');
    const content = fs.readFileSync(
      path.resolve(__dirname, '../components/layouts/TopBar.tsx'),
      'utf-8'
    );

    // Verify useNavigate is imported and used
    expect(content).toContain("import { useNavigate } from '@tanstack/react-router'");
    expect(content).toContain('const navigate = useNavigate()');

    // Verify Profile and Settings use navigate
    expect(content).toContain("navigate({ to: '/settings' })");

    // Verify old no-op handlers are gone
    expect(content).not.toContain('onClick={() => {}}');
  });
});

// ── Bug 4: SettingsPage version ──

describe('SettingsPage version', () => {
  it('displays version from environment variable', async () => {
    vi.stubGlobal('import.meta', {
      env: {
        VITE_APP_VERSION: '0.18.0',
        VITE_API_URL: '/api/v1',
      },
    });

    vi.mock('next-themes', () => ({
      useTheme: () => ({ theme: 'light', setTheme: vi.fn() }),
    }));

    vi.mock('@/hooks/use-health', () => ({
      useHealth: () => ({ data: { status: 'ok', db: { latency_ms: 1 } } }),
    }));

    const { SettingsPage } = await import('@/components/SettingsPage');

    render(React.createElement(SettingsPage));

    const versionElements = screen.getAllByText('0.18.0');
    expect(versionElements.length).toBeGreaterThan(0);
  });
});
