import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { NotificationsPage } from '../NotificationsPage';
import { mockSuccessQuery, mockLoadingQuery } from '@/test/helpers';

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
    updated: vi.fn(),
    mutationError: vi.fn(),
  },
}));

import { fetchNotifications, fetchUnreadCount, markNotificationRead, markAllNotificationsRead } from '@/lib/api';
import { showToast } from '@/lib/toast';

const mockFetchNotifications = vi.mocked(fetchNotifications);
const mockFetchUnreadCount = vi.mocked(fetchUnreadCount);
const mockMarkRead = vi.mocked(markNotificationRead);
const mockMarkAll = vi.mocked(markAllNotificationsRead);
const mockShowToast = vi.mocked(showToast);

const SAMPLE_NOTIFICATIONS = [
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
    type: 'evidence.attached',
    title: 'Evidence added',
    message: 'New evidence attached to task',
    entity_type: 'task',
    entity_id: 't2',
    is_read: true,
    created_at: '2026-08-12T09:00:00Z',
  },
  {
    id: 'n3',
    type: 'review.completed',
    title: 'Review done',
    message: 'Review round completed',
    entity_type: null,
    entity_id: null,
    is_read: false,
    created_at: '2026-08-12T08:00:00Z',
  },
];

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <NotificationsPage />
    </QueryClientProvider>
  );
}

describe('NotificationsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockFetchNotifications.mockResolvedValue({ items: SAMPLE_NOTIFICATIONS });
    mockFetchUnreadCount.mockResolvedValue({ count: 2 });
  });

  it('renders heading with unread count', async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getAllByText('Notifications').length).toBeGreaterThanOrEqual(1);
    });
    await waitFor(() => {
      expect(screen.getByText('2 unread')).toBeInTheDocument();
    });
  });

  it('renders notification list', async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText('Task updated')).toBeInTheDocument();
      expect(screen.getByText('Evidence added')).toBeInTheDocument();
      expect(screen.getByText('Review done')).toBeInTheDocument();
    });
  });

  it('shows type badges for each notification', async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText('task.status_changed')).toBeInTheDocument();
      expect(screen.getByText('evidence.attached')).toBeInTheDocument();
      expect(screen.getByText('review.completed')).toBeInTheDocument();
    });
  });

  it('shows unread indicator for unread notifications', async () => {
    renderPage();
    await waitFor(() => {
      const unreadDots = screen.getAllByLabelText('Mark as read');
      expect(unreadDots.length).toBe(2);
    });
  });

  it('calls markNotificationRead when mark-as-read clicked', async () => {
    mockMarkRead.mockResolvedValue({ id: 'n1', is_read: true });
    renderPage();
    await waitFor(() => {
      expect(screen.getByText('Task updated')).toBeInTheDocument();
    });
    const markButtons = screen.getAllByLabelText('Mark as read');
    expect(markButtons.length).toBeGreaterThan(0);
    await waitFor(() => {
      fireEvent.click(markButtons[0]);
      expect(mockMarkRead).toHaveBeenCalled();
    });
  });

  it('shows mark all read button when there are unread', async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText('Mark all read')).toBeInTheDocument();
    });
  });

  it('shows empty state when no notifications', async () => {
    mockFetchNotifications.mockResolvedValue({ items: [] });
    mockFetchUnreadCount.mockResolvedValue({ count: 0 });
    renderPage();
    await waitFor(() => {
      expect(screen.getByText('No notifications')).toBeInTheDocument();
    });
  });

  it('has no emoji in content', async () => {
    renderPage();
    await waitFor(() => {
      expect(screen.getByText('Notifications')).toBeInTheDocument();
    });
    const { container } = renderPage();
    const text = container.textContent || '';
    const emojiRegex = /[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F1E0}-\u{1F1FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/u;
    expect(emojiRegex.test(text)).toBe(false);
  });
});
