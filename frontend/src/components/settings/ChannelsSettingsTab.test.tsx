import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ChannelsSettingsTab } from './ChannelsSettingsTab';

vi.mock('@/hooks/use-analytics', () => ({
  useNotificationChannels: vi.fn(),
}));

vi.mock('@/lib/api/analytics', () => ({
  createNotificationChannel: vi.fn(),
  deleteNotificationChannel: vi.fn(),
  toggleNotificationChannel: vi.fn(),
  testNotificationChannel: vi.fn(),
  updateNotificationChannel: vi.fn(),
}));

vi.mock('@/lib/toast', () => ({
  showToast: {
    created: vi.fn(),
    updated: vi.fn(),
    deleted: vi.fn(),
    error: vi.fn(),
    mutationError: vi.fn(),
  },
}));

import { useNotificationChannels } from '@/hooks/use-analytics';
import { updateNotificationChannel } from '@/lib/api/analytics';

const mockUseChannels = vi.mocked(useNotificationChannels);
const mockUpdate = vi.mocked(updateNotificationChannel);

const EMAIL_CH = {
  id: 'ch1',
  channel_type: 'email',
  name: 'DevOps alerts',
  config: {
    smtp_host: 'smtp.example.com',
    smtp_port: 587,
    from_address: 'noreply@example.com',
    to_address: 'alerts@example.com',
  },
  is_active: true,
  created_at: '',
  updated_at: '',
};

const WEBHOOK_CH = {
  id: 'ch2',
  channel_type: 'webhook',
  name: 'Slack',
  config: { url: 'https://hooks.slack.com/x' },
  is_active: false,
  created_at: '',
  updated_at: '',
};

function renderTab() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const invalidateSpy = vi.spyOn(qc, 'invalidateQueries');
  render(
    <QueryClientProvider client={qc}>
      <ChannelsSettingsTab />
    </QueryClientProvider>
  );
  return { invalidateSpy };
}

describe('ChannelsSettingsTab — channel edit (TASK-0109 AC4)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseChannels.mockReturnValue({
      data: { items: [EMAIL_CH, WEBHOOK_CH] },
      isLoading: false,
    } as ReturnType<typeof useNotificationChannels>);
    mockUpdate.mockResolvedValue(undefined as never);
  });

  it('shows an edit button per channel', () => {
    renderTab();
    expect(screen.getByLabelText('Edit channel DevOps alerts')).toBeInTheDocument();
    expect(screen.getByLabelText('Edit channel Slack')).toBeInTheDocument();
  });

  it('opens the edit dialog prefilled with name and email target', () => {
    renderTab();
    fireEvent.click(screen.getByLabelText('Edit channel DevOps alerts'));

    const dialog = screen.getByRole('dialog');
    expect(within(dialog).getByText('Edit Notification Channel')).toBeInTheDocument();
    expect(within(dialog).getByLabelText('Name')).toHaveValue('DevOps alerts');
    expect(within(dialog).getByLabelText('Email Address')).toHaveValue(
      'alerts@example.com'
    );
  });

  it('extracts the webhook url as target for webhook channels', () => {
    renderTab();
    fireEvent.click(screen.getByLabelText('Edit channel Slack'));

    const dialog = screen.getByRole('dialog');
    expect(within(dialog).getByLabelText('Name')).toHaveValue('Slack');
    expect(within(dialog).getByLabelText('Webhook URL')).toHaveValue(
      'https://hooks.slack.com/x'
    );
  });

  it('saves edited name and config, preserving other config keys', async () => {
    const { invalidateSpy } = renderTab();
    fireEvent.click(screen.getByLabelText('Edit channel DevOps alerts'));

    const dialog = screen.getByRole('dialog');
    fireEvent.change(within(dialog).getByLabelText('Name'), {
      target: { value: 'Ops alerts' },
    });
    fireEvent.change(within(dialog).getByLabelText('Email Address'), {
      target: { value: 'oncall@example.com' },
    });
    fireEvent.click(within(dialog).getByRole('button', { name: 'Save Changes' }));

    await waitFor(() => {
      expect(mockUpdate).toHaveBeenCalledWith('ch1', {
        name: 'Ops alerts',
        config: {
          smtp_host: 'smtp.example.com',
          smtp_port: 587,
          from_address: 'noreply@example.com',
          to_address: 'oncall@example.com',
        },
      });
    });
    expect(invalidateSpy).toHaveBeenCalledWith({
      queryKey: ['notification-channels'],
    });
    await waitFor(() => {
      expect(screen.queryByText('Edit Notification Channel')).not.toBeInTheDocument();
    });
  });

  it('cancel closes the dialog without calling the API', async () => {
    renderTab();
    fireEvent.click(screen.getByLabelText('Edit channel DevOps alerts'));

    const dialog = screen.getByRole('dialog');
    fireEvent.click(within(dialog).getByRole('button', { name: 'Cancel' }));

    expect(mockUpdate).not.toHaveBeenCalled();
    await waitFor(() => {
      expect(
        screen.queryByText('Edit Notification Channel')
      ).not.toBeInTheDocument();
    });
  });
});
