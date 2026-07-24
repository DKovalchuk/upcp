import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { HealthPage } from './HealthPage';

vi.mock('@/hooks/use-health', () => ({
  useHealth: vi.fn(),
}));

import { useHealth } from '@/hooks/use-health';
const mock = vi.mocked(useHealth);

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={qc}><HealthPage /></QueryClientProvider>);
}

describe('HealthPage', () => {
  beforeEach(() => vi.clearAllMocks());

  it('renders loading state', () => {
    mock.mockReturnValue({ data: undefined, isLoading: true } as any);
    const { container } = renderPage();
    expect(container.querySelectorAll('[data-slot="skeleton"]').length).toBeGreaterThan(0);
  });

  it('renders error state', () => {
    mock.mockReturnValue({ data: undefined, isLoading: false, error: new Error('fail') } as any);
    renderPage();
    expect(screen.getByText('Failed to load health status')).toBeInTheDocument();
  });

  it('renders healthy status', () => {
    mock.mockReturnValue({
      data: { status: 'ok', service: 'upcp-backend' },
      isLoading: false, error: null,
    } as any);
    renderPage();
    expect(screen.getByText('System Health')).toBeInTheDocument();
    expect(screen.getByText('Backend API')).toBeInTheDocument();
    expect(screen.getByText('Operational')).toBeInTheDocument();
    expect(screen.getByText('upcp-backend')).toBeInTheDocument();
  });

  it('renders down status', () => {
    mock.mockReturnValue({
      data: { status: 'error', service: 'upcp-backend' },
      isLoading: false, error: null,
    } as any);
    renderPage();
    expect(screen.getByText('Down')).toBeInTheDocument();
  });
});
