import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AuthProvider, useAuth } from './AuthContext';

vi.mock('@/lib/auth', () => ({
  authMe: vi.fn(),
  authRefresh: vi.fn(),
}));

vi.mock('@/lib/storage', () => ({
  safeStorage: {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
  },
}));

import { authMe, authRefresh } from '@/lib/auth';
import { safeStorage } from '@/lib/storage';

const mockAuthMe = vi.mocked(authMe);
const mockAuthRefresh = vi.mocked(authRefresh);
const mockGetItem = vi.mocked(safeStorage.getItem);
const mockSetItem = vi.mocked(safeStorage.setItem);
const mockRemoveItem = vi.mocked(safeStorage.removeItem);

function TestConsumer() {
  const { user, token, isLoading, isAuthenticated, setTokens, logout } = useAuth();
  return (
    <div>
      <span data-testid="loading">{String(isLoading)}</span>
      <span data-testid="authenticated">{String(isAuthenticated)}</span>
      <span data-testid="token">{token ?? 'null'}</span>
      <span data-testid="user">{user?.email ?? 'null'}</span>
      <button onClick={() => setTokens('new-access', 'new-refresh')}>Set Tokens</button>
      <button onClick={() => logout()}>Logout</button>
    </div>
  );
}

function renderAuth(consumer = <TestConsumer />) {
  return render(
    <AuthProvider>{consumer}</AuthProvider>,
  );
}

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetItem.mockReturnValue(null);
  });

  it('starts unauthenticated with no token', async () => {
    renderAuth();
    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('false');
    });
    expect(screen.getByTestId('authenticated')).toHaveTextContent('false');
    expect(screen.getByTestId('token')).toHaveTextContent('null');
  });

  it('loads user when token exists in storage', async () => {
    mockGetItem.mockImplementation((key: string) => {
      if (key === 'upcp_access_token') return 'existing-token';
      return null;
    });
    mockAuthMe.mockResolvedValue({
      id: 'u1', email: 'test@example.com', display_name: 'Test',
      is_active: true, is_superuser: false, organizations: [],
    });

    renderAuth();
    await waitFor(() => {
      expect(screen.getByTestId('authenticated')).toHaveTextContent('true');
    });
    expect(screen.getByTestId('user')).toHaveTextContent('test@example.com');
    expect(mockAuthMe).toHaveBeenCalledWith('existing-token');
  });

  it('tries refresh when authMe fails', async () => {
    mockGetItem.mockImplementation((key: string) => {
      if (key === 'upcp_access_token') return 'expired-token';
      if (key === 'upcp_refresh_token') return 'refresh-token';
      return null;
    });
    mockAuthMe
      .mockRejectedValueOnce(new Error('Unauthorized'))
      .mockResolvedValueOnce({
        id: 'u1', email: 'test@example.com', display_name: 'Test',
        is_active: true, is_superuser: false, organizations: [],
      });
    mockAuthRefresh.mockResolvedValue({
      access_token: 'new-access', refresh_token: 'new-refresh', token_type: 'bearer',
    });

    renderAuth();
    await waitFor(() => {
      expect(screen.getByTestId('authenticated')).toHaveTextContent('true');
    });
    expect(mockAuthRefresh).toHaveBeenCalledWith('refresh-token');
    expect(mockSetItem).toHaveBeenCalledWith('upcp_access_token', 'new-access');
  });

  it('clears tokens when refresh fails', async () => {
    mockGetItem.mockImplementation((key: string) => {
      if (key === 'upcp_access_token') return 'expired-token';
      if (key === 'upcp_refresh_token') return 'refresh-token';
      return null;
    });
    mockAuthMe.mockRejectedValue(new Error('Unauthorized'));
    mockAuthRefresh.mockRejectedValue(new Error('Refresh failed'));

    renderAuth();
    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('false');
    });
    expect(mockRemoveItem).toHaveBeenCalledWith('upcp_access_token');
    expect(mockRemoveItem).toHaveBeenCalledWith('upcp_refresh_token');
  });

  it('setTokens stores tokens and updates state', async () => {
    renderAuth();
    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('false');
    });

    fireEvent.click(screen.getByText('Set Tokens'));

    await waitFor(() => {
      expect(screen.getByTestId('token')).toHaveTextContent('new-access');
    });
    expect(mockSetItem).toHaveBeenCalledWith('upcp_access_token', 'new-access');
    expect(mockSetItem).toHaveBeenCalledWith('upcp_refresh_token', 'new-refresh');
  });

  it('logout clears tokens and resets state', async () => {
    mockGetItem.mockImplementation((key: string) => {
      if (key === 'upcp_access_token') return 'token';
      return null;
    });
    mockAuthMe.mockResolvedValue({
      id: 'u1', email: 'test@example.com', display_name: 'Test',
      is_active: true, is_superuser: false, organizations: [],
    });

    renderAuth();
    await waitFor(() => {
      expect(screen.getByTestId('authenticated')).toHaveTextContent('true');
    });

    fireEvent.click(screen.getByText('Logout'));

    expect(mockRemoveItem).toHaveBeenCalledWith('upcp_access_token');
    expect(mockRemoveItem).toHaveBeenCalledWith('upcp_refresh_token');
    expect(screen.getByTestId('authenticated')).toHaveTextContent('false');
    expect(screen.getByTestId('token')).toHaveTextContent('null');
  });

  it('throws when useAuth used outside provider', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    expect(() => render(<TestConsumer />)).toThrow('useAuth must be used within AuthProvider');
    consoleSpy.mockRestore();
  });
});
