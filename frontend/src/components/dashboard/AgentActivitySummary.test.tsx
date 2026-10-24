import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AgentActivitySummary } from './AgentActivitySummary';
import { mockSuccessQuery } from '@/test/helpers';

// Mock the hook
vi.mock('@/hooks/use-dashboard', () => ({
  useAgentActivity: vi.fn(),
}));

// Rows link to /agents/:id (B18.10) — mock the router Link to its href
// contract, the same pattern as Dashboard.test/PortfolioTable.test.
vi.mock('@tanstack/react-router', () => ({
  Link: ({
    to,
    params,
    children,
    className,
    ...rest
  }: {
    to: string;
    params?: Record<string, string>;
    children?: React.ReactNode;
    className?: string;
  }) => {
    const href =
      params && typeof to === 'string'
        ? to.replace('$agentId', params.agentId ?? '')
        : to;
    return (
      <a href={href} className={className} {...rest}>
        {children}
      </a>
    );
  },
  useNavigate: () => vi.fn(),
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
    } as ReturnType<typeof useAgentActivity>);

    const { container } = renderAgentActivitySummary();
    const skeletons = container.querySelectorAll('[data-slot="skeleton"]');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('renders empty state when no agents', () => {
    mockUseAgentActivity.mockReturnValue({
      data: { items: [] },
      isLoading: false,
      error: null,
    } as ReturnType<typeof useAgentActivity>);

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
    } as ReturnType<typeof useAgentActivity>);

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
    } as ReturnType<typeof useAgentActivity>);

    renderAgentActivitySummary();

    expect(screen.getByText('Stale Agent')).toBeInTheDocument();
    expect(screen.getByText('Stale')).toBeInTheDocument(); // AgentStatusBadge label
  });

  // ── B18: positive rows ──────────────────────────

  it('renders agent avatar with initials (B18.2)', () => {
    mockUseAgentActivity.mockReturnValue(
      mockSuccessQuery({
        items: [
          {
            agent_id: 'a1',
            agent_name: 'Commander',
            task_id: 't1',
            task_title: 'Do thing',
            claimed_at: '2026-07-30T10:00:00Z',
            last_heartbeat_at: '2026-07-30T10:05:00Z',
            progress_percent: 65,
            current_step: 'Implementation',
            is_stale: false,
          },
        ],
      }),
    );
    renderAgentActivitySummary();
    expect(screen.getByText('C')).toBeInTheDocument(); // initials avatar fallback
  });

  function findBarByWidth(container: HTMLElement, width: string): HTMLElement | undefined {
    return Array.from(container.querySelectorAll<HTMLElement>('div')).find(
      (el) => el.style.width === width,
    );
  }

  it('active agent gets emerald progress bar (B18.6)', () => {
    mockUseAgentActivity.mockReturnValue(
      mockSuccessQuery({
        items: [
          {
            agent_id: 'a1',
            agent_name: 'Commander',
            task_id: 't1',
            task_title: 'Do thing',
            claimed_at: '2026-07-30T10:00:00Z',
            last_heartbeat_at: '2026-07-30T10:05:00Z',
            progress_percent: 65,
            current_step: 'Implementation',
            is_stale: false,
          },
        ],
      }),
    );
    const view = renderAgentActivitySummary();
    const bar = findBarByWidth(view.container, '65%');
    expect(bar).toBeTruthy();
    expect(bar?.classList.contains('bg-emerald-500')).toBe(true);
  });

  it('stale agent gets orange progress bar (B18.7)', () => {
    mockUseAgentActivity.mockReturnValue(
      mockSuccessQuery({
        items: [
          {
            agent_id: 'a1',
            agent_name: 'Stale One',
            task_id: 't1',
            task_title: 'Old task',
            claimed_at: '2026-07-30T08:00:00Z',
            last_heartbeat_at: '2026-07-30T08:10:00Z',
            progress_percent: 30,
            current_step: 'Blocked',
            is_stale: true,
          },
        ],
      }),
    );
    const { container } = renderAgentActivitySummary();
    const bar = findBarByWidth(container, '30%');
    expect(bar).toBeTruthy();
    expect(bar?.classList.contains('bg-orange-500')).toBe(true);
  });

  it('active agent avatar has pulse animation (B18.8)', () => {
    mockUseAgentActivity.mockReturnValue(
      mockSuccessQuery({
        items: [
          {
            agent_id: 'a1',
            agent_name: 'Commander',
            task_id: 't1',
            task_title: 'Do thing',
            claimed_at: '2026-07-30T10:00:00Z',
            last_heartbeat_at: '2026-07-30T10:05:00Z',
            progress_percent: 65,
            current_step: 'Implementation',
            is_stale: false,
          },
        ],
      }),
    );
    renderAgentActivitySummary();
    const avatarWrap = screen.getByText('C').closest('div.relative.inline-flex');
    expect(avatarWrap?.querySelector('.animate-heartbeat-pulse')).toBeTruthy();
  });

  // ── B19: edge cases ─────────────────────────────

  it('agent with 0% progress renders bar at start (B19.2)', () => {
    mockUseAgentActivity.mockReturnValue(
      mockSuccessQuery({
        items: [
          {
            agent_id: 'a1',
            agent_name: 'Fresh Agent',
            task_id: 't1',
            task_title: 'Just started',
            claimed_at: '2026-07-30T10:00:00Z',
            last_heartbeat_at: '2026-07-30T10:05:00Z',
            progress_percent: 0,
            current_step: 'Start',
            is_stale: false,
          },
        ],
      }),
    );
    const { container } = renderAgentActivitySummary();
    expect(screen.getByText('0%')).toBeInTheDocument();
    expect(findBarByWidth(container, '0%')).toBeTruthy();
  });

  it('agent with empty task title renders without crash (B19.4)', () => {
    // Note: no explicit "Idle" placeholder — empty title renders an empty line.
    mockUseAgentActivity.mockReturnValue(
      mockSuccessQuery({
        items: [
          {
            agent_id: 'a1',
            agent_name: 'Idle Agent',
            task_id: 't1',
            task_title: '',
            claimed_at: '2026-07-30T10:00:00Z',
            last_heartbeat_at: '2026-07-30T10:05:00Z',
            progress_percent: 0,
            current_step: 'Idle',
            is_stale: false,
          },
        ],
      }),
    );
    renderAgentActivitySummary();
    expect(screen.getByText('Idle Agent')).toBeInTheDocument();
    expect(screen.getByText('0%')).toBeInTheDocument();
  });

  it('agent with NULL heartbeat shows fallback text (B19.5)', () => {
    // Copy is "No heartbeat" (task row said "Unknown") — documenting actual behavior.
    mockUseAgentActivity.mockReturnValue(
      mockSuccessQuery({
        items: [
          {
            agent_id: 'a1',
            agent_name: 'Silent Agent',
            task_id: 't1',
            task_title: 'Something',
            claimed_at: '2026-07-30T10:00:00Z',
            last_heartbeat_at: null,
            progress_percent: 50,
            current_step: 'Working',
            is_stale: false,
          },
        ],
      }),
    );
    renderAgentActivitySummary();
    expect(screen.getByText('No heartbeat')).toBeInTheDocument();
  });

  it('all agents stale → every progress bar orange (B19.6)', () => {
    const staleItem = (i: number) => ({
      agent_id: `a${i}`,
      agent_name: `Stale ${i}`,
      task_id: `t${i}`,
      task_title: `Task ${i}`,
      claimed_at: '2026-07-30T08:00:00Z',
      last_heartbeat_at: '2026-07-30T08:10:00Z',
      progress_percent: 20 + i,
      current_step: 'Blocked',
      is_stale: true,
    });
    mockUseAgentActivity.mockReturnValue(mockSuccessQuery({ items: [staleItem(1), staleItem(2)] }));
    const { container } = renderAgentActivitySummary();
    const bar1 = findBarByWidth(container, '21%');
    const bar2 = findBarByWidth(container, '22%');
    expect(bar1?.classList.contains('bg-orange-500')).toBe(true);
    expect(bar2?.classList.contains('bg-orange-500')).toBe(true);
  });

  // ── B18.10 / B19.7: follow-ups closed in TASK-0154 ──────────

  it('clicking an agent row navigates to /agents/:id (B18.10)', () => {
    mockUseAgentActivity.mockReturnValue(
      mockSuccessQuery({
        items: [
          {
            agent_id: 'a1',
            agent_name: 'Commander',
            task_id: 't1',
            task_title: 'Do thing',
            claimed_at: '2026-07-30T10:00:00Z',
            last_heartbeat_at: '2026-07-30T10:05:00Z',
            progress_percent: 65,
            current_step: 'Implementation',
            is_stale: false,
          },
        ],
      }),
    );
    renderAgentActivitySummary();
    const link = screen.getByRole('link', { name: /Commander/ });
    expect(link).toHaveAttribute('href', '/agents/a1');
  });

  it('progress above 100 caps at 100% and below 0 floors at 0% (B19.7)', () => {
    mockUseAgentActivity.mockReturnValue(
      mockSuccessQuery({
        items: [
          {
            agent_id: 'a1',
            agent_name: 'Overdoer',
            task_id: 't1',
            task_title: 'Too much',
            claimed_at: '2026-07-30T10:00:00Z',
            last_heartbeat_at: '2026-07-30T10:05:00Z',
            progress_percent: 150,
            current_step: 'Implementation',
            is_stale: false,
          },
          {
            agent_id: 'a2',
            agent_name: 'Negative',
            task_id: 't2',
            task_title: 'Below zero',
            claimed_at: '2026-07-30T10:00:00Z',
            last_heartbeat_at: '2026-07-30T10:05:00Z',
            progress_percent: -20,
            current_step: 'Start',
            is_stale: false,
          },
        ],
      }),
    );
    const { container } = renderAgentActivitySummary();
    expect(screen.queryByText('150%')).not.toBeInTheDocument();
    expect(screen.queryByText('-20%')).not.toBeInTheDocument();
    expect(screen.getByText('100%')).toBeInTheDocument();
    expect(screen.getByText('0%')).toBeInTheDocument();
    expect(findBarByWidth(container, '100%')).toBeTruthy();
    expect(findBarByWidth(container, '0%')).toBeTruthy();
  });
});
