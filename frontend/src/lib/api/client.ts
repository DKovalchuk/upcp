import { safeStorage } from '@/lib/storage';

const API_BASE = '/api/v1';

function getToken(): string | null {
  return safeStorage.getItem('upcp_access_token');
}

function getRefreshToken(): string | null {
  return safeStorage.getItem('upcp_refresh_token');
}

function setTokens(access: string, refresh: string): void {
  safeStorage.setItem('upcp_access_token', access);
  safeStorage.setItem('upcp_refresh_token', refresh);
}

function clearTokens(): void {
  safeStorage.removeItem('upcp_access_token');
  safeStorage.removeItem('upcp_refresh_token');
}

// Prevent multiple concurrent refresh attempts
let refreshPromise: Promise<boolean> | null = null;

async function tryRefreshToken(): Promise<boolean> {
  if (refreshPromise) return refreshPromise;

  refreshPromise = (async () => {
    const refreshToken = getRefreshToken();
    if (!refreshToken) return false;

    try {
      const res = await fetch(`${API_BASE.replace('/api/v1', '')}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!res.ok) return false;

      const data = await res.json();
      setTokens(data.access_token, data.refresh_token);
      return true;
    } catch {
      return false;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

export function paginationParams(params?: { offset?: number; limit?: number }): string {
  if (!params) return '';
  const parts: string[] = [];
  if (params.offset !== undefined) parts.push(`offset=${params.offset}`);
  if (params.limit !== undefined) parts.push(`limit=${params.limit}`);
  return parts.length ? `?${parts.join('&')}` : '';
}

export async function apiRequest<T>(
  url: string,
  options: RequestInit = {},
  _isRetry = false,
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...options.headers as Record<string, string>,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (response.status === 401 && !_isRetry && !url.includes('/auth/')) {
    const refreshed = await tryRefreshToken();
    if (refreshed) {
      return apiRequest<T>(url, options, true);
    }
    clearTokens();
    if (!window.location.pathname.startsWith('/login')) {
      window.location.href = '/login';
    }
    throw new Error('Unauthorized');
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      error: response.statusText,
      detail: 'Unknown error',
    }));
    throw new Error(error.detail || error.error || response.statusText);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

export { API_BASE };
