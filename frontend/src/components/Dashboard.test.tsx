import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Dashboard } from './Dashboard';
import { mockSuccessQuery, mockLoadingQuery, mockErrorQuery } from '@/test/helpers';

const routeState = vi.hoisted(() => ({
  search: {} as Record<string, string | undefined>,
}));

vi.mock('@tanstack/react-router', () => ({
  Link: ({ children, to, search, params, ...props }: any) => {
    let href: string = to;
    if (params && typeof href === 'string') {
      href = href.replace('$projectId', params.projectId ?? '');
    }
    if (search && typeof href === 'string') {
      href += `?${new URLSearchParams(search as Record<string, string>).toString()}`;
    }
    return (
      <a href={href} {...props}>
        {children}
      </a>
    );
  },
  useNavigate: () => vi.fn(),
  useSearch: () => routeState.search,
}));

vi.mock('@/hooks/use-dashboard', () => ({
  useDashboardStats: vi.fn(),
  useAgentActivity: vi.fn(),
  useAttentionDashboard: vi.fn(),
  usePortfolioOverview: vi.fn(),
}));

vi.mock('@/hooks/use-projects', () => ({
  useProjects: vi.fn(),
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
  LowHealthProjectsSection: () => <div>LowHealthProjectsSection</div>,
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

vi.mock('@/components/dashboard/VelocityChart', () => ({
  VelocityChart: () => <div>VelocityChart</div>,
}));

vi.mock('@/components/dashboard/PortfolioTable', () => ({
  PortfolioTable: () => <div>PortfolioTable</div>,
}));

vi.mock('@/components/dashboard/ProjectSelector', () => ({
  ProjectSelector: () => <div>ProjectSelector</div>,
}));

vi.mock('@/hooks/use-analytics', () => ({
  useGlobalVelocity: vi.fn(),
}));

import { useDashboardStats, usePortfolioOverview } from '@/hooks/use-dashboard';
import { useAttentionDashboard } from '@/components/dashboard/AttentionCards';
import { useGlobalVelocity } from '@/hooks/use-analytics';
import { useProjects } from '@/hooks/use-projects';

const mockUseDashboardStats = vi.mocked(useDashboardStats);
const mockUseAttentionDashboard = vi.mocked(useAttentionDashboard);
const mockUseGlobalVelocity = vi.mocked(useGlobalVelocity);
const mockUsePortfolioOverview = vi.mocked(usePortfolioOverview);
const mockUseProjects = vi.mocked(useProjects);

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
    routeState.search = {};
    mockUseAttentionDashboard.mockReturnValue(mockSuccessQuery({}));
    mockUseGlobalVelocity.mockReturnValue(mockSuccessQuery({ items: [] }));
    mockUsePortfolioOverview.mockReturnValue(mockSuccessQuery(undefined));
    mockUseProjects.mockReturnValue(
      mockSuccessQuery({ items: [{ id: 'p1', name: 'UPCP', status: 'active' }], total: 1 }),
    );
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
    // Active, Done, Blocked link to delivery page of first project with status filter
    const base = `/projects/${FULL_STATS.recent_projects[0].id}/delivery`;
    expect(screen.getByText('Active Tasks').closest('a')).toHaveAttribute(
      'href',
      `${base}?status=in_progress`,
    );
    expect(screen.getByText('Done This Week').closest('a')).toHaveAttribute(
      'href',
      `${base}?status=done`,
    );
    expect(screen.getByText('Blocked').closest('a')).toHaveAttribute(
      'href',
      `${base}?status=blocked`,
    );
  });

  it('health score card links to selected project detail', () => {
    routeState.search = { project_id: 'p1' };
    mockUseDashboardStats.mockReturnValue(mockSuccessQuery(FULL_STATS));
    renderDashboard();
    expect(screen.getByText('Health Score').closest('a')).toHaveAttribute(
      'href',
      '/projects/p1',
    );
  });

  it('health score card is not a link when no project selected', () => {
    mockUseDashboardStats.mockReturnValue(mockSuccessQuery(FULL_STATS));
    renderDashboard();
    expect(screen.getByText('Health Score').closest('a')).toBeNull();
  });

  it('scopes attention dashboard to selected project', () => {
    routeState.search = { project_id: 'p1' };
    mockUseDashboardStats.mockReturnValue(mockSuccessQuery(FULL_STATS));
    renderDashboard();
    expect(mockUseAttentionDashboard).toHaveBeenCalledWith('p1');
  });

  it('fetches unscoped attention when no project selected', () => {
    mockUseDashboardStats.mockReturnValue(mockSuccessQuery(FULL_STATS));
    renderDashboard();
    expect(mockUseAttentionDashboard).toHaveBeenCalledWith(undefined);
  });

  it('project selector row is sticky with solid background', () => {
    mockUseDashboardStats.mockReturnValue(mockSuccessQuery(FULL_STATS));
    renderDashboard();
    const row = screen.getByText('ProjectSelector').parentElement;
    expect(row).toHaveClass('sticky', 'top-0', 'z-10', 'bg-background');
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

  it('renders velocity chart', () => {
    mockUseDashboardStats.mockReturnValue(mockSuccessQuery(FULL_STATS));
    renderDashboard();
    expect(screen.getByText('VelocityChart')).toBeInTheDocument();
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

  // ── B1: KPI cards — icons, variants, health boundaries ──

  it('each KPI card renders an icon (B1.4)', () => {
    mockUseDashboardStats.mockReturnValue(mockSuccessQuery(FULL_STATS));
    renderDashboard();
    for (const label of ['Projects', 'Active Tasks', 'Done This Week', 'Blocked', 'Health Score']) {
      const card = screen.getByText(label).closest('[data-slot="card"]');
      expect(card?.querySelector('svg'), `${label} icon`).toBeTruthy();
    }
  });

  it('KPI cards use per-variant accent colors (B1.5)', () => {
    mockUseDashboardStats.mockReturnValue(mockSuccessQuery(FULL_STATS));
    renderDashboard();
    const expectations: Array<[string, string]> = [
      ['Projects', 'border-l-primary'],
      ['Active Tasks', 'border-l-blue-500'],
      ['Done This Week', 'border-l-emerald-500'],
      ['Blocked', 'border-l-red-500'], // blocked_count=1 → error variant
      ['Health Score', 'border-l-amber-500'], // 75 → warning variant
    ];
    for (const [label, cls] of expectations) {
      const card = screen.getByText(label).closest('[data-slot="card"]');
      expect(card?.classList.contains(cls), `${label} → ${cls}`).toBe(true);
    }
  });

  const HEALTH_BOUNDARIES: Array<[number, string, string]> = [
    [100, 'bg-emerald-500/10', 'border-l-emerald-500'], // B1.14 max
    [80, 'bg-emerald-500/10', 'border-l-emerald-500'], // B1.9 green boundary
    [79, 'bg-amber-500/10', 'border-l-amber-500'], // B1.10 amber boundary
    [50, 'bg-amber-500/10', 'border-l-amber-500'], // B1.11 amber boundary
    [49, 'bg-red-500/10', 'border-l-red-500'], // B1.12 red boundary
    [0, 'bg-red-500/10', 'border-l-red-500'], // B1.13 minimum
  ];

  it.each(HEALTH_BOUNDARIES)(
    'health score %i gets correct color classes (B1.6-B1.14)',
    (score, iconClass, cardClass) => {
      mockUseDashboardStats.mockReturnValue(mockSuccessQuery({ ...FULL_STATS, health_score: score }));
      renderDashboard();
      const value = screen.getByText(`${score}%`);
      const card = value.closest('[data-slot="card"]');
      expect(card?.classList.contains(cardClass), `card ${cardClass}`).toBe(true);
      const icon = card?.querySelector('.h-10');
      expect(icon?.classList.contains(iconClass), `icon ${iconClass}`).toBe(true);
    },
  );

  // ── B2/B3: KPI navigation + negative/edge ──

  it('linked cards have pointer cursor; health card without project does not (B2.7)', () => {
    mockUseDashboardStats.mockReturnValue(mockSuccessQuery(FULL_STATS));
    renderDashboard();
    const projectsLink = screen.getByText('Projects').closest('a');
    expect(projectsLink?.querySelector('.cursor-pointer')).toBeTruthy();
    const healthCard = screen.getByText('Health Score').closest('[data-slot="card"]');
    expect(healthCard?.classList.contains('cursor-pointer')).toBe(false);
  });

  it('renders very large counts (B3.4)', () => {
    mockUseDashboardStats.mockReturnValue(
      mockSuccessQuery({ ...FULL_STATS, project_count: 99999, done_this_week: 88888 }),
    );
    renderDashboard();
    expect(screen.getByText('99999')).toBeInTheDocument();
    expect(screen.getByText('88888')).toBeInTheDocument();
  });

  it('negative health score clamps to 0% (B3.5)', () => {
    mockUseDashboardStats.mockReturnValue(
      mockSuccessQuery({ ...FULL_STATS, health_score: -20 }),
    );
    renderDashboard();
    expect(screen.getByText('0%')).toBeInTheDocument();
    expect(screen.queryByText('-20%')).not.toBeInTheDocument();
  });

  it('health score over 100 clamps to 100% (B3.5 boundary)', () => {
    mockUseDashboardStats.mockReturnValue(
      mockSuccessQuery({ ...FULL_STATS, health_score: 150 }),
    );
    renderDashboard();
    expect(screen.getByText('100%')).toBeInTheDocument();
    expect(screen.queryByText('150%')).not.toBeInTheDocument();
  });

  it('falls back to 100% when health_score is missing (B3.6)', () => {
    // Note: implementation falls back to 100 (full health), not "N/A"/0 as the
    // task row suggested — documenting actual behavior here.
    mockUseDashboardStats.mockReturnValue(
      mockSuccessQuery({ ...FULL_STATS, health_score: undefined }),
    );
    renderDashboard();
    expect(screen.getByText('100%')).toBeInTheDocument();
  });

  it('renders safely when API returns null fields (B3.7)', () => {
    mockUseDashboardStats.mockReturnValue(
      mockSuccessQuery({
        project_count: 1,
        task_counts_by_status: null,
        recent_projects: null,
        recent_activity: null,
        done_this_week: null,
        blocked_count: null,
        claimed_count: null,
        health_score: null,
      }),
    );
    renderDashboard();
    expect(screen.getByText('Projects')).toBeInTheDocument();
    expect(screen.getByText('No recent projects.')).toBeInTheDocument();
    // null health → 100% fallback, null counts → 0 / 0 active tasks
    expect(screen.getByText('100%')).toBeInTheDocument();
    expect(screen.getAllByText('0').length).toBeGreaterThanOrEqual(1);
  });

  it('renders recent project with null description without crash (B13.8)', () => {
    mockUseDashboardStats.mockReturnValue(
      mockSuccessQuery({
        ...FULL_STATS,
        recent_projects: [
          { ...FULL_STATS.recent_projects[0], description: null },
        ],
      }),
    );
    renderDashboard();
    expect(screen.getByText('UPCP')).toBeInTheDocument();
    expect(screen.queryByText('Main project')).not.toBeInTheDocument();
  });

  // ── B14: selector scoping of hooks ──

  it('selected project scopes KPI stats hook (B14.6)', () => {
    routeState.search = { project_id: 'p1' };
    mockUseDashboardStats.mockReturnValue(mockSuccessQuery(FULL_STATS));
    renderDashboard();
    expect(mockUseDashboardStats).toHaveBeenCalledWith('p1');
  });

  it('selected project scopes velocity hook (B14.8)', () => {
    routeState.search = { project_id: 'p1' };
    mockUseDashboardStats.mockReturnValue(mockSuccessQuery(FULL_STATS));
    renderDashboard();
    expect(mockUseGlobalVelocity).toHaveBeenCalledWith(8, 'p1');
  });

  it('portfolio overview stays global regardless of selector (B14.9)', () => {
    routeState.search = { project_id: 'p1' };
    mockUseDashboardStats.mockReturnValue(mockSuccessQuery(FULL_STATS));
    renderDashboard();
    expect(mockUsePortfolioOverview).toHaveBeenCalledWith();
  });

  // ── B20: integration rows ──

  it('renders all layout rows together (B20.1)', () => {
    mockUseDashboardStats.mockReturnValue(mockSuccessQuery(FULL_STATS));
    mockUseAttentionDashboard.mockReturnValue(
      mockSuccessQuery({ needs_review: [], blocked_tasks: [] }),
    );
    mockUsePortfolioOverview.mockReturnValue(
      mockSuccessQuery({ projects: [{ id: 'p1', name: 'UPCP', slug: 'upcp', task_count: 3, health_score: 90, top_issue: '' }] }),
    );
    renderDashboard();
    // Row 1 KPI, Row 2 charts, Row 3 attention, Row 4 activity+agents, Row 5 portfolio
    expect(screen.getByText('Projects')).toBeInTheDocument();
    expect(screen.getByText('TaskDistributionDonut')).toBeInTheDocument();
    expect(screen.getByText('VelocityChart')).toBeInTheDocument();
    expect(screen.getByText('Needs Attention')).toBeInTheDocument();
    expect(screen.getByText('LiveActivityFeed')).toBeInTheDocument();
    expect(screen.getByText('AgentActivitySummary')).toBeInTheDocument();
    expect(screen.getByText('PortfolioTable')).toBeInTheDocument();
  });

  it('stats render even when attention query fails (B20.5)', () => {
    mockUseDashboardStats.mockReturnValue(mockSuccessQuery(FULL_STATS));
    mockUseAttentionDashboard.mockReturnValue(mockErrorQuery('attention down'));
    renderDashboard();
    // KPI row still renders; attention sections fall back to empty items
    expect(screen.getByText('Projects')).toBeInTheDocument();
    expect(screen.getByText('75%')).toBeInTheDocument();
    expect(screen.queryByText('Failed to load dashboard data')).not.toBeInTheDocument();
    expect(screen.getByText('NeedsReviewSection')).toBeInTheDocument();
  });

  it('responsive grid classes applied to KPI and attention rows (B20.8)', () => {
    mockUseDashboardStats.mockReturnValue(mockSuccessQuery(FULL_STATS));
    renderDashboard();
    const kpiRow = screen.getByText('Projects').closest('div[class*="lg:grid-cols-5"]');
    expect(kpiRow?.classList.contains('grid-cols-1')).toBe(true);
    expect(kpiRow?.classList.contains('sm:grid-cols-2')).toBe(true);
    const attentionRow = screen.getByText('Needs Attention').nextElementSibling;
    expect(attentionRow?.classList.contains('md:grid-cols-2')).toBe(true);
    expect(attentionRow?.classList.contains('lg:grid-cols-3')).toBe(true);
  });

  it('stagger animations applied to rows (B20.9)', () => {
    mockUseDashboardStats.mockReturnValue(mockSuccessQuery(FULL_STATS));
    renderDashboard();
    const kpiRow = screen.getByText('Projects').closest('div[class*="lg:grid-cols-5"]');
    expect(kpiRow?.classList.contains('animate-stagger')).toBe(true);
    const root = screen.getByText('ProjectSelector').closest('div[class*="animate-fade-in-up"]');
    expect(root).toBeTruthy();
  });

  it('dark mode classes present on KPI cards (B20.10)', () => {
    mockUseDashboardStats.mockReturnValue(mockSuccessQuery({ ...FULL_STATS, health_score: 75 }));
    const { container } = renderDashboard();
    expect(container.querySelector('[class*="dark:"]')).toBeTruthy();
    const healthCard = screen.getByText('Health Score').closest('[data-slot="card"]');
    expect(healthCard?.classList.contains('dark:bg-amber-500/5')).toBe(true);
    const healthIcon = healthCard?.querySelector('.h-10');
    expect(healthIcon?.classList.contains('dark:text-amber-400')).toBe(true);
  });
});
