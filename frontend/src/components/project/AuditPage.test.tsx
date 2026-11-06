import { render, screen, fireEvent } from '@testing-library/react';
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
    mock.mockReturnValue({ data: undefined, isLoading: true } as ReturnType<typeof useAuditEvents>);
    const { container } = renderPage();
    expect(container.querySelectorAll('[data-slot="skeleton"]').length).toBeGreaterThan(0);
  });

  it('renders error state', () => {
    mock.mockReturnValue({ data: undefined, isLoading: false, error: new Error('fail') } as ReturnType<typeof useAuditEvents>);
    renderPage();
    expect(screen.getByText('Failed to load audit events')).toBeInTheDocument();
  });

  it('renders heading and filters', () => {
    mock.mockReturnValue({ data: { items: [], total: 0, offset: 0, limit: 20 }, isLoading: false, error: null } as ReturnType<typeof useAuditEvents>);
    renderPage();
    expect(screen.getByText('Audit Log')).toBeInTheDocument();
    expect(screen.getByText('All event types')).toBeInTheDocument();
    expect(screen.getByText('All entity types')).toBeInTheDocument();
  });

  it('renders empty state', () => {
    mock.mockReturnValue({ data: { items: [], total: 0, offset: 0, limit: 20 }, isLoading: false, error: null } as ReturnType<typeof useAuditEvents>);
    renderPage();
    expect(screen.getByText('No audit events found.')).toBeInTheDocument();
  });

  it('renders audit events', () => {
    mock.mockReturnValue({
      data: {
        items: [
          { id: 'e1', timestamp: '2026-07-24T10:00:00Z', event_type: 'created', entity_type: 'task', entity_id: '12345678-1234', actor_type: 'user', actor_id: 'user-12345678', payload: null, note: 'Test note' },
        ],
        total: 1, offset: 0, limit: 20,
      },
      isLoading: false, error: null,
    } as ReturnType<typeof useAuditEvents>);
    renderPage();
    expect(screen.getByText('created')).toBeInTheDocument();
    expect(screen.getByText('task')).toBeInTheDocument();
    expect(screen.getByText('Test note')).toBeInTheDocument();
  });

  it('renders search input', () => {
    mock.mockReturnValue({ data: { items: [], total: 0, offset: 0, limit: 20 }, isLoading: false, error: null } as ReturnType<typeof useAuditEvents>);
    renderPage();
    expect(screen.getByPlaceholderText('Search events...')).toBeInTheDocument();
  });

  it('filters events by search query', () => {
    mock.mockReturnValue({
      data: {
        items: [
          { id: 'e1', timestamp: '2026-07-24T10:00:00Z', event_type: 'created', entity_type: 'task', entity_id: '12345678-1234', actor_type: 'user', actor_id: 'user-12345678', payload: null, note: 'Created task alpha' },
          { id: 'e2', timestamp: '2026-07-24T11:00:00Z', event_type: 'updated', entity_type: 'feature', entity_id: '22345678-1234', actor_type: 'agent', actor_id: 'agent-12345678', payload: null, note: 'Updated feature beta' },
        ],
        total: 2, offset: 0, limit: 20,
      },
      isLoading: false, error: null,
    } as ReturnType<typeof useAuditEvents>);
    renderPage();

    fireEvent.change(screen.getByPlaceholderText('Search events...'), { target: { value: 'alpha' } });

    expect(screen.getByText('Created task alpha')).toBeInTheDocument();
    expect(screen.queryByText('Updated feature beta')).not.toBeInTheDocument();
  });

  it('shows no-match message when search has no results', () => {
    mock.mockReturnValue({
      data: {
        items: [
          { id: 'e1', timestamp: '2026-07-24T10:00:00Z', event_type: 'created', entity_type: 'task', entity_id: '12345678-1234', actor_type: 'user', actor_id: 'user-12345678', payload: null, note: 'Created task' },
        ],
        total: 1, offset: 0, limit: 20,
      },
      isLoading: false, error: null,
    } as ReturnType<typeof useAuditEvents>);
    renderPage();

    fireEvent.change(screen.getByPlaceholderText('Search events...'), { target: { value: 'nonexistent' } });

    expect(screen.getByText('No events match your search.')).toBeInTheDocument();
  });

  it('search is case-insensitive', () => {
    mock.mockReturnValue({
      data: {
        items: [
          { id: 'e1', timestamp: '2026-07-24T10:00:00Z', event_type: 'created', entity_type: 'Task', entity_id: '12345678-1234', actor_type: 'user', actor_id: 'user-12345678', payload: null, note: null },
        ],
        total: 1, offset: 0, limit: 20,
      },
      isLoading: false, error: null,
    } as ReturnType<typeof useAuditEvents>);
    renderPage();

    fireEvent.change(screen.getByPlaceholderText('Search events...'), { target: { value: 'TASK' } });

    expect(screen.getByText('Task')).toBeInTheDocument();
  });
});
