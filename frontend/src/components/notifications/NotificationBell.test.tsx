// NotificationBell tests — TASK-0086 residual gaps:
// dropdown open + mark-as-read click path, and the empty state.

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { NotificationBell } from './NotificationBell';
import type { Notification } from '@/types/dashboard';

vi.mock('@/lib/api', () => ({
  fetchNotifications: vi.fn(),
  fetchUnreadCount: vi.fn(),
  markNotificationRead: vi.fn(),
  markAllNotificationsRead: vi.fn(),
}));

vi.mock('@tanstack/react-router', () => ({
  useNavigate: vi.fn(() => vi.fn()),
}));

vi.mock('@/lib/format', () => ({
  formatRelativeTime: vi.fn(() => '2 hours ago'),
}));

vi.mock('@/lib/toast', () => ({
  showToast: {
    mutationError: vi.fn(),
  },
}));

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(() => ({ isAuthenticated: true })),
}));

import { fetchNotifications, fetchUnreadCount, markNotificationRead } from '@/lib/api';

const mockFetchNotifications = vi.mocked(fetchNotifications);
const mockFetchUnreadCount = vi.mocked(fetchUnreadCount);
const mockMarkNotificationRead = vi.mocked(markNotificationRead);

// Inline fixture (e2e fixtures in frontend/e2e/fixtures are not editable here)
const SAMPLE_NOTIFICATIONS: Notification[] = [
  {
    id: 'n1',
    type: 'task.status_changed',
    title: 'Task updated',
    message: 'Task moved to in-progress',
    entity_type: 'task',
    entity_id: 't1',
    is_read: false,
    created_at: '2026-08-12T10:00:00Z',
  },
  {
    id: 'n2',
    type: 'review.completed',
    title: 'Review done',
    message: 'Review round completed',
    entity_type: null,
    entity_id: null,
    is_read: true,
    created_at: '2026-08-12T09:00:00Z',
  },
];

function renderBell() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <NotificationBell />
    </QueryClientProvider>
  );
}

function openBell() {
  fireEvent.click(screen.getByLabelText(/^Notifications \(/));
}

describe('NotificationBell', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockFetchNotifications.mockResolvedValue({ items: SAMPLE_NOTIFICATIONS });
    mockFetchUnreadCount.mockResolvedValue({ count: 1 });
  });

  it('opens the dropdown and lists notifications', async () => {
    renderBell();
    openBell();

    await waitFor(() => {
      expect(mockFetchNotifications).toHaveBeenCalledWith(false);
    });
    await waitFor(() => {
      expect(screen.getByText('Task updated')).toBeInTheDocument();
      expect(screen.getByText('Review done')).toBeInTheDocument();
    });
  });

  it('calls markNotificationRead when a notification item is clicked', async () => {
    mockMarkNotificationRead.mockResolvedValue({
      ...SAMPLE_NOTIFICATIONS[0],
      is_read: true,
    });
    renderBell();
    openBell();

    await waitFor(() => {
      expect(screen.getByText('Task updated')).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText('Task updated'));

    await waitFor(() => {
      expect(mockMarkNotificationRead).toHaveBeenCalledWith('n1');
    });
  });

  it('shows the empty state when there are no notifications', async () => {
    mockFetchNotifications.mockResolvedValue({ items: [] });
    mockFetchUnreadCount.mockResolvedValue({ count: 0 });
    renderBell();
    openBell();

    await waitFor(() => {
      expect(screen.getByText('No notifications')).toBeInTheDocument();
    });
  });
});
