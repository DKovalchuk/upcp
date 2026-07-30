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

  it('shows Database connected when db.status is ok', () => {
    mock.mockReturnValue({
      data: {
        status: 'ok',
        service: 'upcp-backend',
        db: { status: 'ok', latency_ms: 12 },
        redis: { status: 'ok', latency_ms: 2 },
      },
      isLoading: false, error: null,
    } as any);
    renderPage();
    expect(screen.getByText('Database')).toBeInTheDocument();
    expect(screen.getAllByText('Connected').length).toBeGreaterThan(0);
    expect(screen.getByText('12ms')).toBeInTheDocument();
  });

  it('shows Database disconnected when db.status is error', () => {
    mock.mockReturnValue({
      data: {
        status: 'ok',
        service: 'upcp-backend',
        db: { status: 'error', error: 'connection refused' },
        redis: { status: 'ok', latency_ms: 2 },
      },
      isLoading: false, error: null,
    } as any);
    renderPage();
    expect(screen.getByText('Database')).toBeInTheDocument();
    expect(screen.getByText('connection refused')).toBeInTheDocument();
    expect(screen.getByText('Disconnected')).toBeInTheDocument();
  });

  it('shows Redis connected when redis.status is ok', () => {
    mock.mockReturnValue({
      data: {
        status: 'ok',
        service: 'upcp-backend',
        db: { status: 'ok', latency_ms: 12 },
        redis: { status: 'ok', latency_ms: 3 },
      },
      isLoading: false, error: null,
    } as any);
    renderPage();
    expect(screen.getByText('Redis')).toBeInTheDocument();
    expect(screen.getAllByText('Connected').length).toBeGreaterThan(0);
    expect(screen.getByText('3ms')).toBeInTheDocument();
  });

  it('shows Redis disconnected when redis.status is error', () => {
    mock.mockReturnValue({
      data: {
        status: 'ok',
        service: 'upcp-backend',
        db: { status: 'ok', latency_ms: 12 },
        redis: { status: 'error', error: 'timeout' },
      },
      isLoading: false, error: null,
    } as any);
    renderPage();
    expect(screen.getByText('Redis')).toBeInTheDocument();
    expect(screen.getByText('timeout')).toBeInTheDocument();
    expect(screen.getByText('Disconnected')).toBeInTheDocument();
  });
});
