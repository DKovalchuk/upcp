import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AnalyticsPage } from './AnalyticsPage';
import type { TrendData, VelocityData, AgentPerformance } from '@/types/analytics';

vi.mock('@/hooks/use-project-id', () => ({ useProjectId: () => 'proj-1' }));

vi.mock('@/hooks/use-analytics', () => ({
  useProjectTrends: vi.fn(),
  useProjectVelocity: vi.fn(),
  useAgentsOverview: vi.fn(),
}));

import {
  useProjectTrends,
  useProjectVelocity,
  useAgentsOverview,
} from '@/hooks/use-analytics';

const mockTrends = vi.mocked(useProjectTrends);
const mockVelocity = vi.mocked(useProjectVelocity);
const mockAgents = vi.mocked(useAgentsOverview);

const TRENDS: TrendData[] = [
  { week: '2026-W40', completed: 2, created: 4 },
  { week: '2026-W41', completed: 3, created: 5 },
];

const VELOCITY: VelocityData[] = [
  { week: '2026-W40', count: 4 },
  { week: '2026-W41', count: 0 },
];

const AGENTS: AgentPerformance[] = [
  {
    agent_id: 'agent-1',
    total_claims: 2,
    completed: 1,
    success_rate: 50,
    avg_hours: 2.5,
  },
  {
    agent_id: 'agent-2',
    total_claims: 3,
    completed: 3,
    success_rate: 100,
    avg_hours: null,
  },
];

function mockLoaded(
  trends: TrendData[] = TRENDS,
  velocity: VelocityData[] = VELOCITY,
  agents: AgentPerformance[] = AGENTS
) {
  mockTrends.mockReturnValue({
    data: { items: trends },
    isLoading: false,
  } as ReturnType<typeof useProjectTrends>);
  mockVelocity.mockReturnValue({
    data: { items: velocity },
    isLoading: false,
  } as ReturnType<typeof useProjectVelocity>);
  mockAgents.mockReturnValue({
    data: { items: agents },
    isLoading: false,
  } as ReturnType<typeof useAgentsOverview>);
}

describe('AnalyticsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockLoaded();
  });

  it('shows loading skeleton while analytics are loading', () => {
    mockTrends.mockReturnValue({
      data: undefined,
      isLoading: true,
    } as ReturnType<typeof useProjectTrends>);

    const { container } = render(<AnalyticsPage />);
    expect(
      container.querySelectorAll('[data-slot="skeleton"]').length
    ).toBeGreaterThan(0);
    expect(screen.queryByText('Task Trends')).not.toBeInTheDocument();
  });

  it('renders heading and all three sections', () => {
    render(<AnalyticsPage />);
    expect(
      screen.getByRole('heading', { name: 'Analytics' })
    ).toBeInTheDocument();
    expect(screen.getByText('Task Trends')).toBeInTheDocument();
    expect(screen.getByText('Velocity')).toBeInTheDocument();
    expect(screen.getByText('Agent Performance')).toBeInTheDocument();
  });

  it('renders trend bars from data', () => {
    render(<AnalyticsPage />);
    expect(screen.getByTitle('Completed: 3')).toBeInTheDocument();
    expect(screen.getByTitle('Created: 5')).toBeInTheDocument();
    expect(screen.getByTitle('Completed: 2')).toBeInTheDocument();
  });

  it('renders velocity bars with task counts', () => {
    render(<AnalyticsPage />);
    expect(screen.getByTitle('4 tasks')).toBeInTheDocument();
    expect(screen.getByTitle('0 tasks')).toBeInTheDocument();
  });

  it('renders agent rows and skips avg when null', () => {
    render(<AnalyticsPage />);
    expect(screen.getByText('agent-1')).toBeInTheDocument();
    expect(screen.getByText('2 claims')).toBeInTheDocument();
    expect(screen.getByText('50%')).toBeInTheDocument();
    expect(screen.getByText('2.5h avg')).toBeInTheDocument();

    expect(screen.getByText('agent-2')).toBeInTheDocument();
    expect(screen.getByText('100%')).toBeInTheDocument();
    // avg_hours is null for agent-2 — no avg span rendered for it
    expect(screen.getAllByText(/h avg/)).toHaveLength(1);
  });

  it('shows empty states when there is no data', () => {
    mockLoaded([], [], []);

    render(<AnalyticsPage />);
    expect(screen.getAllByText('No data')).toHaveLength(2);
    expect(screen.getByText('No agents yet')).toBeInTheDocument();
  });

  it('renders week labels under chart bars', () => {
    render(<AnalyticsPage />);
    expect(screen.getAllByText('W41')).toHaveLength(2);
  });
});
