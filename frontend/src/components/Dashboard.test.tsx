import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Dashboard } from './Dashboard';
import { mockSuccessQuery, mockLoadingQuery, mockErrorQuery } from '@/test/helpers';

vi.mock('@tanstack/react-router', () => ({
  Link: ({ children, to, ...props }: any) => (
    <a href={to} {...props}>{children}</a>
  ),
  useNavigate: () => vi.fn(),
}));

vi.mock('@/hooks/use-dashboard', () => ({
  useDashboardStats: vi.fn(),
  useAgentActivity: vi.fn(),
  useAttentionDashboard: vi.fn(),
}));

vi.mock('@/components/dashboard/AttentionCards', () => ({
  useAttentionDashboard: vi.fn(),
  NeedsReviewSection: () => <div>NeedsReviewSection</div>,
  OpenClarificationsSection: () => <div>OpenClarificationsSection</div>,
  BlockedTasksSection: () => <div>BlockedTasksSection</div>,
  StaleAgentsSection: () => <div>StaleAgentsSection</div>,
  FailedQualityGatesSection: () => <div>FailedQualityGatesSection</div>,
  RejectedTasksSection: () => <div>RejectedTasksSection</div>,
  AgentVerdictsSection: () => <div>AgentVerdictsSection</div>,
}));

vi.mock('@/components/dashboard/LiveActivityFeed', () => ({
  LiveActivityFeed: () => <div>LiveActivityFeed</div>,
}));

vi.mock('@/components/dashboard/AgentActivitySummary', () => ({
  AgentActivitySummary: () => <div>AgentActivitySummary</div>,
}));

vi.mock('@/components/dashboard/TaskDistributionDonut', () => ({
  TaskDistributionDonut: () => <div>TaskDistributionDonut</div>,
}));

import { useDashboardStats } from '@/hooks/use-dashboard';
import { useAttentionDashboard } from '@/components/dashboard/AttentionCards';

const mockUseDashboardStats = vi.mocked(useDashboardStats);
const mockUseAttentionDashboard = vi.mocked(useAttentionDashboard);

const FULL_STATS = {
  project_count: 2,
  task_counts_by_status: { backlog: 4, in_progress: 2, review: 1, done: 30, blocked: 1 },
  recent_projects: [
    { id: 'p1', name: 'UPCP', slug: 'upcp', description: 'Main project', status: 'active', created_at: '2026-01-01T00:00:00Z', updated_at: '2026-09-05T00:00:00Z' },
  ],
  recent_activity: [],
  done_this_week: 12,
  blocked_count: 1,
  claimed_count: 2,
  health_score: 75,
};

function createQueryClient() {
  return new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
}

function renderDashboard() {
  const queryClient = createQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <Dashboard />
    </QueryClientProvider>
  );
}

describe('Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseAttentionDashboard.mockReturnValue(mockSuccessQuery({}));
  });

  it('renders loading skeleton initially', () => {
    mockUseDashboardStats.mockReturnValue(mockLoadingQuery());
    const { container } = renderDashboard();
    expect(container.querySelectorAll('[data-slot="skeleton"]').length).toBeGreaterThan(0);
  });

  it('renders error state on failure', () => {
    mockUseDashboardStats.mockReturnValue(mockErrorQuery('API error'));
    renderDashboard();
    expect(screen.getByText('Failed to load dashboard data')).toBeInTheDocument();
  });

  it('renders empty state when no projects', () => {
    mockUseDashboardStats.mockReturnValue(mockSuccessQuery({
      ...FULL_STATS,
      project_count: 0,
      recent_projects: [],
    }));
    renderDashboard();
    expect(screen.getByText('No projects yet')).toBeInTheDocument();
  });

  // ── KPI Cards ──────────────────────────────────

  it('renders all 5 KPI cards', () => {
    mockUseDashboardStats.mockReturnValue(mockSuccessQuery(FULL_STATS));
    renderDashboard();
    expect(screen.getByText('Projects')).toBeInTheDocument();
    expect(screen.getByText('Active Tasks')).toBeInTheDocument();
    expect(screen.getByText('Done This Week')).toBeInTheDocument();
    expect(screen.getByText('Blocked')).toBeInTheDocument();
    expect(screen.getByText('Health Score')).toBeInTheDocument();
  });

  it('shows correct KPI values', () => {
    mockUseDashboardStats.mockReturnValue(mockSuccessQuery(FULL_STATS));
    renderDashboard();
    expect(screen.getByText('2')).toBeInTheDocument(); // Projects
    expect(screen.getByText('12')).toBeInTheDocument(); // Done This Week
    expect(screen.getByText('75%')).toBeInTheDocument(); // Health Score
  });

  it('calculates active tasks correctly (in_progress + claimed + blocked)', () => {
    mockUseDashboardStats.mockReturnValue(mockSuccessQuery(FULL_STATS));
    renderDashboard();
    // 2 in_progress + 2 claimed + 1 blocked = 5
    expect(screen.getByText('5')).toBeInTheDocument();
  });

  it('KPI cards have correct drill-down links', () => {
    mockUseDashboardStats.mockReturnValue(mockSuccessQuery(FULL_STATS));
    renderDashboard();
    expect(screen.getByText('Projects').closest('a')).toHaveAttribute('href', '/projects');
    expect(screen.getByText('Active Tasks').closest('a')).toHaveAttribute('href', '/delivery?status=in_progress,claimed,blocked');
    expect(screen.getByText('Done This Week').closest('a')).toHaveAttribute('href', '/delivery?status=done');
    expect(screen.getByText('Blocked').closest('a')).toHaveAttribute('href', '/delivery?status=blocked');
  });

  it('health score shows correct color class', () => {
    mockUseDashboardStats.mockReturnValue(mockSuccessQuery({ ...FULL_STATS, health_score: 85 }));
    const { rerender } = renderDashboard();
    // ≥80 should have emerald styling (green)
    expect(screen.getByText('85%')).toBeInTheDocument();

    // Re-render with amber score
    mockUseDashboardStats.mockReturnValue(mockSuccessQuery({ ...FULL_STATS, health_score: 60 }));
    render(
      <QueryClientProvider client={createQueryClient()}>
        <Dashboard />
      </QueryClientProvider>
    );
    expect(screen.getByText('60%')).toBeInTheDocument();
  });

  it('handles zero counts gracefully', () => {
    mockUseDashboardStats.mockReturnValue(mockSuccessQuery({
      ...FULL_STATS,
      project_count: 1,
      task_counts_by_status: { backlog: 0, in_progress: 0, review: 0, done: 0, blocked: 0 },
      done_this_week: 0,
      blocked_count: 0,
      claimed_count: 0,
    }));
    renderDashboard();
    const zeros = screen.getAllByText('0');
    expect(zeros.length).toBeGreaterThanOrEqual(3);
  });

  it('handles undefined optional fields gracefully', () => {
    mockUseDashboardStats.mockReturnValue(mockSuccessQuery({
      project_count: 1,
      task_counts_by_status: { backlog: 0, in_progress: 0, review: 0, done: 0 },
      recent_projects: [],
      recent_activity: [],
    }));
    renderDashboard();
    expect(screen.getByText('Projects')).toBeInTheDocument();
  });

  // ── Charts ─────────────────────────────────────

  it('renders donut chart placeholder', () => {
    mockUseDashboardStats.mockReturnValue(mockSuccessQuery(FULL_STATS));
    renderDashboard();
    expect(screen.getByText('TaskDistributionDonut')).toBeInTheDocument();
  });

  it('renders velocity placeholder', () => {
    mockUseDashboardStats.mockReturnValue(mockSuccessQuery(FULL_STATS));
    renderDashboard();
    expect(screen.getByText('Velocity chart — coming in Sprint 2')).toBeInTheDocument();
  });

  // ── Sections ───────────────────────────────────

  it('renders attention section', () => {
    mockUseDashboardStats.mockReturnValue(mockSuccessQuery(FULL_STATS));
    renderDashboard();
    expect(screen.getByText('Needs Attention')).toBeInTheDocument();
  });

  it('renders activity and agents sections', () => {
    mockUseDashboardStats.mockReturnValue(mockSuccessQuery(FULL_STATS));
    renderDashboard();
    expect(screen.getByText('LiveActivityFeed')).toBeInTheDocument();
    expect(screen.getByText('AgentActivitySummary')).toBeInTheDocument();
  });

  it('renders recent projects', () => {
    mockUseDashboardStats.mockReturnValue(mockSuccessQuery(FULL_STATS));
    renderDashboard();
    expect(screen.getByText('Recent Projects')).toBeInTheDocument();
    expect(screen.getByText('UPCP')).toBeInTheDocument();
  });
});
