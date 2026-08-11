// Agent Detail Page tests — TASK-0099 Sprint 2

import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AgentDetailPage } from '@/pages/AgentDetailPage';

vi.mock('@/hooks/use-agents', () => ({
  useAgent: vi.fn(),
}));

vi.mock('@tanstack/react-router', () => ({
  useParams: () => ({ agentId: 'agent-1' }),
}));

import { useAgent } from '@/hooks/use-agents';

const mockUseAgent = vi.mocked(useAgent);

const mockAgent = {
  id: 'agent-1',
  name: 'claude-builder',
  description: 'Code builder agent',
  is_active: true,
  created_by: 'user-1',
  created_at: '2026-08-01T10:00:00Z',
  metrics: {
    tasks_completed: 12,
    tasks_failed: 1,
    success_rate: 92.3,
    current_task_id: null,
    current_task_title: null,
    current_progress_percent: null,
    last_heartbeat_at: null,
    is_stale: false,
    status: 'idle',
  },
  tokens: [],
};

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <AgentDetailPage />
    </QueryClientProvider>
  );
}

describe('AgentDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state', () => {
    mockUseAgent.mockReturnValue({
      data: undefined,
      isLoading: true,
    } as any);
    const { container } = renderPage();
    expect(container.querySelector('.animate-pulse')).toBeDefined();
  });

  it('renders error state when agent not found', () => {
    mockUseAgent.mockReturnValue({
      data: null,
      isLoading: false,
      error: new Error('not found'),
    } as any);
    renderPage();
    expect(screen.getByText('Agent not found')).toBeDefined();
  });

  it('renders agent name and metrics', () => {
    mockUseAgent.mockReturnValue({
      data: mockAgent,
      isLoading: false,
    } as any);
    renderPage();
    expect(screen.getByText('claude-builder')).toBeDefined();
    expect(screen.getByText('12')).toBeDefined();
    expect(screen.getByText('92.3%')).toBeDefined();
  });

  it('renders tab list', () => {
    mockUseAgent.mockReturnValue({
      data: mockAgent,
      isLoading: false,
    } as any);
    renderPage();
    expect(screen.getByText('Overview')).toBeDefined();
    expect(screen.getByText('Claims')).toBeDefined();
    expect(screen.getByText('Activity')).toBeDefined();
    expect(screen.getByText('Clarifications')).toBeDefined();
    expect(screen.getByText('Tokens')).toBeDefined();
  });

  it('renders current task when agent is working', () => {
    const workingAgent = {
      ...mockAgent,
      metrics: {
        ...mockAgent.metrics,
        current_task_id: 'task-1',
        current_task_title: 'Implement feature',
        current_progress_percent: 67,
        status: 'working',
      },
    };
    mockUseAgent.mockReturnValue({
      data: workingAgent,
      isLoading: false,
    } as any);
    renderPage();
    expect(screen.getByText('Implement feature')).toBeDefined();
    expect(screen.getByText('67%')).toBeDefined();
  });
});
