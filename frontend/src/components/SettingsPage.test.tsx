import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SettingsPage } from './SettingsPage';
import { mockSuccessQuery, mockLoadingQuery } from '@/test/helpers';

vi.mock('@/hooks/use-health', () => ({
  useHealth: vi.fn(),
}));

vi.mock('@/hooks/use-analytics', () => ({
  useNotificationChannels: vi.fn(() => ({ data: { items: [] }, isLoading: false })),
}));

vi.mock('next-themes', () => ({
  useTheme: vi.fn(() => ({ theme: 'light', setTheme: vi.fn() })),
}));

// ProfileTab reads auth context — render outside AuthProvider in tests
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(() => ({
    user: { display_name: 'Default User', email: 'user@example.com', is_superuser: false },
    token: 'test-token',
  })),
}));

import { useHealth } from '@/hooks/use-health';
const mock = vi.mocked(useHealth);

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <SettingsPage />
    </QueryClientProvider>
  );
}

describe('SettingsPage', () => {
  const localStorageBackup = { ...localStorage };

  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
    Object.assign(localStorage, localStorageBackup);
  });

  it('renders Settings heading', () => {
    mock.mockReturnValue(mockLoadingQuery());
    renderPage();
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });

  it('renders all 5 tab triggers', () => {
    mock.mockReturnValue(mockLoadingQuery());
    renderPage();
    expect(screen.getByRole('tab', { name: /profile/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /notifications/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /channels/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /appearance/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /about/i })).toBeInTheDocument();
  });

  it('has tablist with aria-label', () => {
    mock.mockReturnValue(mockLoadingQuery());
    renderPage();
    expect(screen.getByRole('tablist', { name: /settings sections/i })).toBeInTheDocument();
  });

  it('defaults to Profile tab', () => {
    mock.mockReturnValue(mockLoadingQuery());
    renderPage();
    expect(screen.getByRole('tab', { name: /profile/i })).toHaveAttribute('aria-selected', 'true');
    expect(screen.getAllByText('Profile').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('Default User')).toBeInTheDocument();
  });

  it('switches to Notifications tab on click', () => {
    mock.mockReturnValue(mockLoadingQuery());
    renderPage();
    fireEvent.click(screen.getByRole('tab', { name: /notifications/i }));
    expect(screen.getByText('Notification Preferences')).toBeInTheDocument();
    expect(screen.getByText('Task Created')).toBeInTheDocument();
    expect(screen.getByText('Task Status Changed')).toBeInTheDocument();
  });

  it('switches to Channels tab on click', () => {
    mock.mockReturnValue(mockLoadingQuery());
    renderPage();
    fireEvent.click(screen.getByRole('tab', { name: /channels/i }));
    expect(screen.getByText('Notification Channels')).toBeInTheDocument();
    expect(screen.getByText(/No channels configured/)).toBeInTheDocument();
  });

  it('switches to Appearance tab on click', () => {
    mock.mockReturnValue(mockLoadingQuery());
    renderPage();
    fireEvent.click(screen.getByRole('tab', { name: /appearance/i }));
    expect(screen.getAllByText('Appearance').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('Choose your preferred color scheme. Changes apply immediately.')).toBeInTheDocument();
  });

  it('switches to About tab on click', () => {
    mock.mockReturnValue(mockLoadingQuery());
    renderPage();
    fireEvent.click(screen.getByRole('tab', { name: /about/i }));
    expect(screen.getAllByText('About').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('UPCP — Universal Project Control Plane')).toBeInTheDocument();
    expect(screen.getByText('System Health')).toBeInTheDocument();
  });

  it('shows Connected when backend is healthy on About tab', () => {
    mock.mockReturnValue(mockSuccessQuery({
      status: 'ok',
      service: 'upcp-backend',
      db: { status: 'ok', latency_ms: 15 },
      redis: { status: 'ok' },
    }));
    renderPage();
    fireEvent.click(screen.getByRole('tab', { name: /about/i }));
    expect(screen.getByText('Connected')).toBeInTheDocument();
    expect(screen.getByText('15ms')).toBeInTheDocument();
  });

  it('toggles notification preference', () => {
    mock.mockReturnValue(mockLoadingQuery());
    renderPage();
    fireEvent.click(screen.getByRole('tab', { name: /notifications/i }));
    const toggle = screen.getByRole('switch', { name: /toggle task created/i });
    expect(toggle).toHaveAttribute('aria-checked', 'true');
    fireEvent.click(toggle);
    expect(toggle).toHaveAttribute('aria-checked', 'false');
  });

  it('has no emoji in content', () => {
    mock.mockReturnValue(mockLoadingQuery());
    const { container } = renderPage();
    const text = container.textContent || '';
    const emojiRegex = /[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F1E0}-\u{1F1FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/u;
    expect(emojiRegex.test(text)).toBe(false);
  });
});
