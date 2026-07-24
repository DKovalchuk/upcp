import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Dashboard } from './Dashboard';

// Mock Link component
vi.mock('@tanstack/react-router', () => ({
  Link: ({ children, to, ...props }: any) => (
    <a href={to} {...props}>{children}</a>
  ),
}));

// Mock the hooks
vi.mock('@/hooks/use-dashboard', () => ({
  useDashboardStats: vi.fn(),
}));

vi.mock('@/hooks/use-projects', () => ({
  useProjects: vi.fn(),
}));

import { useDashboardStats } from '@/hooks/use-dashboard';
import { useProjects } from '@/hooks/use-projects';

const mockUseDashboardStats = vi.mocked(useDashboardStats);
const mockUseProjects = vi.mocked(useProjects);

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
  });

  it('renders loading skeleton initially', () => {
    mockUseDashboardStats.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    } as any);
    mockUseProjects.mockReturnValue({
      data: undefined,
      isLoading: true,
    } as any);

    const { container } = renderDashboard();
    const skeletons = container.querySelectorAll('[data-slot="skeleton"]');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('renders error state on failure', () => {
    mockUseDashboardStats.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('API error'),
    } as any);
    mockUseProjects.mockReturnValue({
      data: undefined,
      isLoading: false,
    } as any);

    renderDashboard();
    expect(screen.getByText('Failed to load dashboard data')).toBeInTheDocument();
  });

  it('renders empty state when no projects', () => {
    mockUseDashboardStats.mockReturnValue({
      data: { project_count: 0, task_counts_by_status: { backlog: 0, in_progress: 0, review: 0, done: 0 }, recent_projects: [], recent_activity: [] },
      isLoading: false,
      error: null,
    } as any);
    mockUseProjects.mockReturnValue({
      data: [],
      isLoading: false,
    } as any);

    renderDashboard();
    expect(screen.getByText('No projects yet')).toBeInTheDocument();
    expect(screen.getByText('Create your first project to get started with UPCP.')).toBeInTheDocument();
  });

  it('renders stat cards with data', () => {
    mockUseDashboardStats.mockReturnValue({
      data: {
        project_count: 5,
        task_counts_by_status: { backlog: 3, in_progress: 7, review: 2, done: 12 },
        recent_projects: [],
        recent_activity: [],
      },
      isLoading: false,
      error: null,
    } as any);
    mockUseProjects.mockReturnValue({
      data: [{ id: '1', name: 'P1' }],
      isLoading: false,
    } as any);

    renderDashboard();
    expect(screen.getByText('Projects')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
    expect(screen.getByText('Tasks In Progress')).toBeInTheDocument();
    expect(screen.getByText('7')).toBeInTheDocument();
    expect(screen.getByText('Tasks Done')).toBeInTheDocument();
    expect(screen.getByText('12')).toBeInTheDocument();
  });

  it('renders recent projects list', () => {
    mockUseDashboardStats.mockReturnValue({
      data: {
        project_count: 2,
        task_counts_by_status: { backlog: 0, in_progress: 0, review: 0, done: 0 },
        recent_projects: [
          { id: 'p1', name: 'Project Alpha', slug: 'alpha', description: 'First project', status: 'active', created_at: '2026-01-01T00:00:00Z', updated_at: '2026-07-24T00:00:00Z' },
          { id: 'p2', name: 'Project Beta', slug: 'beta', description: null, status: 'paused', created_at: '2026-01-01T00:00:00Z', updated_at: '2026-07-23T00:00:00Z' },
        ],
        recent_activity: [],
      },
      isLoading: false,
      error: null,
    } as any);
    mockUseProjects.mockReturnValue({
      data: [],
      isLoading: false,
    } as any);

    renderDashboard();
    expect(screen.getByText('Recent Projects')).toBeInTheDocument();
    expect(screen.getByText('Project Alpha')).toBeInTheDocument();
    expect(screen.getByText('First project')).toBeInTheDocument();
    expect(screen.getByText('Project Beta')).toBeInTheDocument();
  });

  it('renders activity feed', () => {
    mockUseDashboardStats.mockReturnValue({
      data: {
        project_count: 1,
        task_counts_by_status: { backlog: 0, in_progress: 0, review: 0, done: 0 },
        recent_projects: [],
        recent_activity: [
          { id: 'e1', timestamp: '2026-07-24T10:00:00Z', event_type: 'created', entity_type: 'task', entity_id: 't1', actor_type: 'user', actor_id: 'u1', payload: null, note: null },
          { id: 'e2', timestamp: '2026-07-24T09:00:00Z', event_type: 'updated', entity_type: 'feature', entity_id: 'f1', actor_type: 'agent', actor_id: 'a1', payload: null, note: null },
        ],
      },
      isLoading: false,
      error: null,
    } as any);
    mockUseProjects.mockReturnValue({
      data: [],
      isLoading: false,
    } as any);

    renderDashboard();
    expect(screen.getByText('Activity Feed')).toBeInTheDocument();
    expect(screen.getByText('created')).toBeInTheDocument();
    expect(screen.getByText('task')).toBeInTheDocument();
    expect(screen.getByText('updated')).toBeInTheDocument();
    expect(screen.getByText('feature')).toBeInTheDocument();
  });

  it('shows no activity message when empty', () => {
    mockUseDashboardStats.mockReturnValue({
      data: {
        project_count: 1,
        task_counts_by_status: { backlog: 0, in_progress: 0, review: 0, done: 0 },
        recent_projects: [],
        recent_activity: [],
      },
      isLoading: false,
      error: null,
    } as any);
    mockUseProjects.mockReturnValue({
      data: [],
      isLoading: false,
    } as any);

    renderDashboard();
    expect(screen.getByText('No recent activity.')).toBeInTheDocument();
  });
});
