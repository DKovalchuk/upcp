import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Dashboard } from './Dashboard';
import { mockSuccessQuery, mockLoadingQuery, mockErrorQuery } from '@/test/helpers';

// Mock Link component and useNavigate
vi.mock('@tanstack/react-router', () => ({
  Link: ({ children, to, ...props }: any) => (
    <a href={to} {...props}>{children}</a>
  ),
  useNavigate: () => vi.fn(),
}));

// Mock the hooks
vi.mock('@/hooks/use-dashboard', () => ({
  useDashboardStats: vi.fn(),
  useAgentActivity: vi.fn(),
}));

vi.mock('@/hooks/use-projects', () => ({
  useProjects: vi.fn(),
}));

import { useDashboardStats, useAgentActivity } from '@/hooks/use-dashboard';
import { useProjects } from '@/hooks/use-projects';

const mockUseDashboardStats = vi.mocked(useDashboardStats);
const mockUseProjects = vi.mocked(useProjects);
const mockUseAgentActivity = vi.mocked(useAgentActivity);

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
    mockUseAgentActivity.mockReturnValue(mockSuccessQuery({ items: [] }));
  });

  it('renders loading skeleton initially', () => {
    mockUseDashboardStats.mockReturnValue(mockLoadingQuery());
    mockUseProjects.mockReturnValue(mockLoadingQuery());

    const { container } = renderDashboard();
    const skeletons = container.querySelectorAll('[data-slot="skeleton"]');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('renders error state on failure', () => {
    mockUseDashboardStats.mockReturnValue(mockErrorQuery('API error'));
    mockUseProjects.mockReturnValue(mockSuccessQuery(undefined));

    renderDashboard();
    expect(screen.getByText('Failed to load dashboard data')).toBeInTheDocument();
  });

  it('renders empty state when no projects', () => {
    mockUseDashboardStats.mockReturnValue(mockSuccessQuery({
      project_count: 0,
      task_counts_by_status: { backlog: 0, in_progress: 0, review: 0, done: 0 },
      recent_projects: [],
      recent_activity: [],
    }));
    mockUseProjects.mockReturnValue(mockSuccessQuery([]));

    renderDashboard();
    expect(screen.getByText('No projects yet')).toBeInTheDocument();
    expect(screen.getByText('Create your first project to get started with UPCP.')).toBeInTheDocument();
  });

  it('renders stat cards with data', () => {
    mockUseDashboardStats.mockReturnValue(mockSuccessQuery({
      project_count: 5,
      task_counts_by_status: { backlog: 3, in_progress: 7, review: 2, done: 12 },
      recent_projects: [],
      recent_activity: [],
    }));
    mockUseProjects.mockReturnValue(mockSuccessQuery([{ id: '1', name: 'P1' }]));

    renderDashboard();
    expect(screen.getByText('Projects')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
    expect(screen.getByText('Tasks In Progress')).toBeInTheDocument();
    expect(screen.getByText('7')).toBeInTheDocument();
    expect(screen.getByText('Tasks Done')).toBeInTheDocument();
    expect(screen.getByText('12')).toBeInTheDocument();
  });

  it('renders recent projects list', () => {
    mockUseDashboardStats.mockReturnValue(mockSuccessQuery({
      project_count: 2,
      task_counts_by_status: { backlog: 0, in_progress: 0, review: 0, done: 0 },
      recent_projects: [
        { id: 'p1', name: 'Project Alpha', slug: 'alpha', description: 'First project', status: 'active', created_at: '2026-01-01T00:00:00Z', updated_at: '2026-07-24T00:00:00Z' },
        { id: 'p2', name: 'Project Beta', slug: 'beta', description: null, status: 'paused', created_at: '2026-01-01T00:00:00Z', updated_at: '2026-07-23T00:00:00Z' },
      ],
      recent_activity: [],
    }));
    mockUseProjects.mockReturnValue(mockSuccessQuery([]));

    renderDashboard();
    expect(screen.getByText('Recent Projects')).toBeInTheDocument();
    expect(screen.getByText('Project Alpha')).toBeInTheDocument();
    expect(screen.getByText('First project')).toBeInTheDocument();
    expect(screen.getByText('Project Beta')).toBeInTheDocument();
  });

  it('renders activity feed', () => {
    mockUseDashboardStats.mockReturnValue(mockSuccessQuery({
      project_count: 1,
      task_counts_by_status: { backlog: 0, in_progress: 0, review: 0, done: 0 },
      recent_projects: [],
      recent_activity: [],
    }));
    mockUseProjects.mockReturnValue(mockSuccessQuery([]));

    renderDashboard();
    const activityElements = screen.getAllByText('Recent Activity');
    expect(activityElements.length).toBeGreaterThanOrEqual(1);
  });

  it('shows no activity message when empty', () => {
    mockUseDashboardStats.mockReturnValue(mockSuccessQuery({
      project_count: 1,
      task_counts_by_status: { backlog: 0, in_progress: 0, review: 0, done: 0 },
      recent_projects: [],
      recent_activity: [],
    }));
    mockUseProjects.mockReturnValue(mockSuccessQuery([]));

    renderDashboard();
    expect(screen.getByText('No recent projects.')).toBeInTheDocument();
  });
});
