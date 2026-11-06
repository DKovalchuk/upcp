import { render, screen, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { NotificationBell } from '../NotificationBell';

vi.mock('@/lib/api', () => ({
  fetchNotifications: vi.fn().mockResolvedValue({ items: [] }),
  fetchUnreadCount: vi.fn().mockResolvedValue({ count: 0 }),
  markNotificationRead: vi.fn(),
  markAllNotificationsRead: vi.fn(),
}));

vi.mock('@tanstack/react-router', () => ({
  useNavigate: vi.fn(() => vi.fn()),
}));

vi.mock('@/lib/toast', () => ({
  showToast: {
    updated: vi.fn(),
    mutationError: vi.fn(),
    info: vi.fn(),
  },
}));

// Component reads auth state (post-TASK-0139 fix); mocked so the test
// controls authentication without a provider.
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

import { fetchUnreadCount } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';

const mockFetchUnreadCount = vi.mocked(fetchUnreadCount);
const mockUseAuth = vi.mocked(useAuth);

function renderBell() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <NotificationBell />
    </QueryClientProvider>,
  );
}

describe('NotificationBell auth gating (TASK-0139)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('does not poll unread-count when unauthenticated', async () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: false } as never);
    renderBell();
    // Flush mount effects + react-query scheduling. Before the fix the
    // query fires on mount regardless of auth → assertion fails (red).
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 50));
    });
    expect(fetchUnreadCount).not.toHaveBeenCalled();
    expect(screen.getByRole('button', { name: /notifications/i })).toBeInTheDocument();
  });

  it('polls unread-count when authenticated (control)', async () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: true } as never);
    renderBell();
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 50));
    });
    expect(mockFetchUnreadCount).toHaveBeenCalled();
  });
});
