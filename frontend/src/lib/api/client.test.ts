import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { apiRequest, paginationParams } from './client';

vi.mock('@/lib/storage', () => ({
  safeStorage: {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
  },
}));

import { safeStorage } from '@/lib/storage';
const mockGetItem = vi.mocked(safeStorage.getItem);
const mockRemoveItem = vi.mocked(safeStorage.removeItem);

const originalFetch = globalThis.fetch;
let mockFetch: ReturnType<typeof vi.fn>;

describe('apiRequest', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetItem.mockReturnValue(null);
    mockFetch = vi.fn();
    globalThis.fetch = mockFetch;
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it('makes request with correct headers', async () => {
    mockFetch.mockResolvedValueOnce(new Response(JSON.stringify({ ok: true }), { status: 200 }));
    await apiRequest('/api/v1/test');
    expect(mockFetch).toHaveBeenCalledWith('/api/v1/test', expect.objectContaining({
      headers: expect.objectContaining({ 'Content-Type': 'application/json' }),
    }));
  });

  it('includes Authorization header when token exists', async () => {
    mockGetItem.mockImplementation((key: string) => {
      if (key === 'upcp_access_token') return 'my-token';
      return null;
    });
    mockFetch.mockResolvedValueOnce(new Response(JSON.stringify({ ok: true }), { status: 200 }));
    await apiRequest('/api/v1/test');
    expect(mockFetch).toHaveBeenCalledWith('/api/v1/test', expect.objectContaining({
      headers: expect.objectContaining({ Authorization: 'Bearer my-token' }),
    }));
  });

  it('throws on non-ok response', async () => {
    mockFetch.mockResolvedValueOnce(new Response(
      JSON.stringify({ detail: 'Not found' }),
      { status: 404 },
    ));
    await expect(apiRequest('/api/v1/missing')).rejects.toThrow('Not found');
  });

  it('returns fallback error when body is not JSON', async () => {
    mockFetch.mockResolvedValueOnce(new Response('error', { status: 500, statusText: 'Internal Server Error' }));
    await expect(apiRequest('/api/v1/error')).rejects.toThrow('Unknown error');
  });

  it('returns undefined for 204 No Content', async () => {
    mockFetch.mockResolvedValueOnce(new Response(null, { status: 204 }));
    const result = await apiRequest('/api/v1/delete');
    expect(result).toBeUndefined();
  });

  it('tries refresh on 401 and retries once', async () => {
    mockGetItem.mockImplementation((key: string) => {
      if (key === 'upcp_access_token') return 'expired';
      if (key === 'upcp_refresh_token') return 'refresh-token';
      return null;
    });

    // First call: 401
    mockFetch.mockResolvedValueOnce(new Response(null, { status: 401 }));
    // Refresh call: 200
    mockFetch.mockResolvedValueOnce(new Response(JSON.stringify({
      access_token: 'new-token', refresh_token: 'new-refresh',
    }), { status: 200 }));
    // Retry call: 200
    mockFetch.mockResolvedValueOnce(new Response(JSON.stringify({ ok: true }), { status: 200 }));

    const result = await apiRequest('/api/v1/test');
    expect(result).toEqual({ ok: true });
    expect(mockFetch).toHaveBeenCalledTimes(3);
  });

  it('redirects to /login when refresh fails', async () => {
    mockGetItem.mockImplementation((key: string) => {
      if (key === 'upcp_access_token') return 'expired';
      if (key === 'upcp_refresh_token') return 'refresh-token';
      return null;
    });

    // First call: 401
    mockFetch.mockResolvedValueOnce(new Response(null, { status: 401 }));
    // Refresh call: 401
    mockFetch.mockResolvedValueOnce(new Response(null, { status: 401 }));

    const originalHref = window.location.href;
    const originalPathname = window.location.pathname;
    Object.defineProperty(window, 'location', {
      value: { pathname: '/projects', href: originalHref },
      writable: true,
    });

    await expect(apiRequest('/api/v1/test')).rejects.toThrow('Unauthorized');
    expect(mockRemoveItem).toHaveBeenCalledWith('upcp_access_token');

    // Restore
    Object.defineProperty(window, 'location', {
      value: { pathname: originalPathname, href: originalHref },
      writable: true,
    });
  });

  it('does not redirect when already on /login', async () => {
    mockGetItem.mockImplementation((key: string) => {
      if (key === 'upcp_access_token') return 'expired';
      if (key === 'upcp_refresh_token') return 'refresh-token';
      return null;
    });

    mockFetch.mockResolvedValueOnce(new Response(null, { status: 401 }));
    mockFetch.mockResolvedValueOnce(new Response(null, { status: 401 }));

    const originalHref = window.location.href;
    const originalPathname = window.location.pathname;
    Object.defineProperty(window, 'location', {
      value: { pathname: '/login', href: originalHref },
      writable: true,
    });

    await expect(apiRequest('/api/v1/test')).rejects.toThrow('Unauthorized');

    // Restore
    Object.defineProperty(window, 'location', {
      value: { pathname: originalPathname, href: originalHref },
      writable: true,
    });
  });

  it('does not refresh for /auth/ endpoints', async () => {
    mockFetch.mockResolvedValueOnce(new Response(
      JSON.stringify({ detail: 'Invalid credentials' }),
      { status: 401 },
    ));

    await expect(apiRequest('/auth/login')).rejects.toThrow('Invalid credentials');
    expect(mockFetch).toHaveBeenCalledTimes(1);
  });
});

describe('paginationParams', () => {
  it('returns empty string for undefined', () => {
    expect(paginationParams()).toBe('');
  });

  it('returns empty string for empty object', () => {
    expect(paginationParams({})).toBe('');
  });

  it('builds offset param', () => {
    expect(paginationParams({ offset: 10 })).toBe('?offset=10');
  });

  it('builds limit param', () => {
    expect(paginationParams({ limit: 20 })).toBe('?limit=20');
  });

  it('builds both params', () => {
    expect(paginationParams({ offset: 10, limit: 20 })).toBe('?offset=10&limit=20');
  });
});
