import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuditPage } from './AuditPage';

vi.mock('@tanstack/react-router', () => ({
  useLocation: () => ({ pathname: '/projects/p1/audit' }),
}));

vi.mock('@/hooks/use-audit', () => ({
  useAuditEvents: vi.fn(),
}));

import { useAuditEvents } from '@/hooks/use-audit';
const mock = vi.mocked(useAuditEvents);

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={qc}><AuditPage /></QueryClientProvider>);
}

describe('AuditPage', () => {
  beforeEach(() => vi.clearAllMocks());

  it('renders loading state', () => {
    mock.mockReturnValue({ data: undefined, isLoading: true } as any);
    const { container } = renderPage();
    expect(container.querySelectorAll('[data-slot="skeleton"]').length).toBeGreaterThan(0);
  });

  it('renders error state', () => {
    mock.mockReturnValue({ data: undefined, isLoading: false, error: new Error('fail') } as any);
    renderPage();
    expect(screen.getByText('Failed to load audit events')).toBeInTheDocument();
  });

  it('renders heading and filters', () => {
    mock.mockReturnValue({ data: [], isLoading: false, error: null } as any);
    renderPage();
    expect(screen.getByText('Audit Log')).toBeInTheDocument();
    expect(screen.getByText('All event types')).toBeInTheDocument();
    expect(screen.getByText('All entity types')).toBeInTheDocument();
  });

  it('renders empty state', () => {
    mock.mockReturnValue({ data: [], isLoading: false, error: null } as any);
    renderPage();
    expect(screen.getByText('No audit events found.')).toBeInTheDocument();
  });

  it('renders audit events', () => {
    mock.mockReturnValue({
      data: [
        { id: 'e1', timestamp: '2026-07-24T10:00:00Z', event_type: 'created', entity_type: 'task', entity_id: '12345678-1234', actor_type: 'user', actor_id: 'user-12345678', payload: null, note: 'Test note' },
      ],
      isLoading: false, error: null,
    } as any);
    renderPage();
    expect(screen.getByText('created')).toBeInTheDocument();
    expect(screen.getByText('task')).toBeInTheDocument();
    expect(screen.getByText('Test note')).toBeInTheDocument();
  });
});
