import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AgentActivitySummary } from './AgentActivitySummary';

// Mock the hook
vi.mock('@/hooks/use-dashboard', () => ({
  useAgentActivity: vi.fn(),
}));

import { useAgentActivity } from '@/hooks/use-dashboard';

const mockUseAgentActivity = vi.mocked(useAgentActivity);

function createQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
}

function renderAgentActivitySummary() {
  const queryClient = createQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <AgentActivitySummary />
    </QueryClientProvider>
  );
}

describe('AgentActivitySummary', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading skeleton initially', () => {
    mockUseAgentActivity.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    } as any);

    const { container } = renderAgentActivitySummary();
    const skeletons = container.querySelectorAll('[data-slot="skeleton"]');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('renders empty state when no agents', () => {
    mockUseAgentActivity.mockReturnValue({
      data: { items: [] },
      isLoading: false,
      error: null,
    } as any);

    renderAgentActivitySummary();
    expect(screen.getByText('No active agents')).toBeInTheDocument();
    expect(screen.getByText('Agent activity will appear here when tasks are running.')).toBeInTheDocument();
  });

  it('renders agent cards with data', () => {
    const mockItems = [
      {
        agent_id: 'agent-1',
        agent_name: 'Commander',
        task_id: 'task-1',
        task_title: 'Implement auth system',
        claimed_at: '2026-07-30T10:00:00Z',
        last_heartbeat_at: '2026-07-30T10:05:00Z',
        progress_percent: 65,
        current_step: 'Implementation',
        is_stale: false,
      },
      {
        agent_id: 'agent-2',
        agent_name: 'Frontend Dev',
        task_id: 'task-2',
        task_title: 'Build dashboard UI',
        claimed_at: '2026-07-30T10:10:00Z',
        last_heartbeat_at: '2026-07-30T10:15:00Z',
        progress_percent: 100,
        current_step: 'Completed',
        is_stale: false,
      },
    ];

    mockUseAgentActivity.mockReturnValue({
      data: { items: mockItems },
      isLoading: false,
      error: null,
    } as any);

    renderAgentActivitySummary();

    expect(screen.getByText('Commander')).toBeInTheDocument();
    expect(screen.getByText('Implement auth system')).toBeInTheDocument();
    expect(screen.getByText('65%')).toBeInTheDocument();

    expect(screen.getByText('Frontend Dev')).toBeInTheDocument();
    expect(screen.getByText('Build dashboard UI')).toBeInTheDocument();
    expect(screen.getByText('100%')).toBeInTheDocument();
  });

  it('renders stale agents with warning indicator', () => {
    const mockItems = [
      {
        agent_id: 'agent-stale',
        agent_name: 'Stale Agent',
        task_id: 'task-stale',
        task_title: 'Stale task',
        claimed_at: '2026-07-30T08:00:00Z',
        last_heartbeat_at: '2026-07-30T08:10:00Z',
        progress_percent: 30,
        current_step: 'Blocked',
        is_stale: true,
      },
    ];

    mockUseAgentActivity.mockReturnValue({
      data: { items: mockItems },
      isLoading: false,
      error: null,
    } as any);

    renderAgentActivitySummary();

    expect(screen.getByText('Stale Agent')).toBeInTheDocument();
    expect(screen.getByText('Stale')).toBeInTheDocument(); // AgentStatusBadge label
  });
});
