import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SettingsPage } from './SettingsPage';

vi.mock('@/hooks/use-health', () => ({
  useHealth: vi.fn(),
}));

vi.mock('next-themes', () => ({
  useTheme: vi.fn(() => ({ theme: 'light', setTheme: vi.fn() })),
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
  beforeEach(() => vi.clearAllMocks());

  it('renders Settings heading', () => {
    mock.mockReturnValue({ data: undefined, isLoading: true } as any);
    renderPage();
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });

  it('renders Appearance section', () => {
    mock.mockReturnValue({ data: undefined, isLoading: true } as any);
    renderPage();
    expect(screen.getByText('Appearance')).toBeInTheDocument();
    expect(screen.getByText('Choose your preferred color scheme. Changes apply immediately.')).toBeInTheDocument();
  });

  it('renders theme toggle buttons', () => {
    mock.mockReturnValue({ data: undefined, isLoading: true } as any);
    renderPage();
    expect(screen.getByText('Light')).toBeInTheDocument();
    expect(screen.getByText('Dark')).toBeInTheDocument();
    expect(screen.getByText('System')).toBeInTheDocument();
  });

  it('renders API Information section', () => {
    mock.mockReturnValue({ data: undefined, isLoading: true } as any);
    renderPage();
    expect(screen.getByText('API Information')).toBeInTheDocument();
    expect(screen.getByText('API Base URL')).toBeInTheDocument();
    expect(screen.getByText('/api/v1')).toBeInTheDocument();
  });

  it('renders Backend Status', () => {
    mock.mockReturnValue({ data: undefined, isLoading: true } as any);
    renderPage();
    expect(screen.getByText('Backend Status')).toBeInTheDocument();
    expect(screen.getByText('Checking...')).toBeInTheDocument();
  });

  it('shows Connected when backend is healthy', () => {
    mock.mockReturnValue({
      data: {
        status: 'ok',
        service: 'upcp-backend',
        db: { status: 'ok', latency_ms: 15 },
        redis: { status: 'ok' },
      },
      isLoading: false,
      error: null,
    } as any);
    renderPage();
    expect(screen.getByText('Connected')).toBeInTheDocument();
    expect(screen.getByText('15ms')).toBeInTheDocument();
  });

  it('shows Disconnected when backend is down', () => {
    mock.mockReturnValue({
      data: {
        status: 'error',
        service: 'upcp-backend',
        db: { status: 'error' },
        redis: { status: 'error' },
      },
      isLoading: false,
      error: null,
    } as any);
    renderPage();
    expect(screen.getByText('Disconnected')).toBeInTheDocument();
  });

  it('renders About section with version', () => {
    mock.mockReturnValue({ data: undefined, isLoading: true } as any);
    renderPage();
    expect(screen.getByText('About')).toBeInTheDocument();
    expect(screen.getByText('UPCP — Universal Project Control Plane')).toBeInTheDocument();
    expect(screen.getByText('0.14.0')).toBeInTheDocument();
  });

  it('has no emoji in content', () => {
    mock.mockReturnValue({ data: undefined, isLoading: true } as any);
    const { container } = renderPage();
    const text = container.textContent || '';
    const emojiRegex = /[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F1E0}-\u{1F1FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/u;
    expect(emojiRegex.test(text)).toBe(false);
  });
});
