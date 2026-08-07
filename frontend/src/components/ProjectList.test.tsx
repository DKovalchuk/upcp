import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ProjectList } from './ProjectList';

const mockNavigate = vi.fn();
vi.mock('@tanstack/react-router', () => ({
  useNavigate: () => mockNavigate,
}));

vi.mock('@/hooks/use-projects', () => ({
  useProjects: vi.fn(),
  useCreateProject: vi.fn(),
}));

vi.mock('@/hooks/use-url-pagination', () => ({
  useUrlPagination: () => ({
    offset: 0,
    limit: 20,
    setOffset: vi.fn(),
    setPageSize: vi.fn(),
  }),
}));

vi.mock('@/lib/toast', () => ({
  showToast: { created: vi.fn() },
}));

import { useProjects, useCreateProject } from '@/hooks/use-projects';

const mockUseProjects = vi.mocked(useProjects);
const mockUseCreateProject = vi.mocked(useCreateProject);

function renderProjectList() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <ProjectList />
    </QueryClientProvider>,
  );
}

describe('ProjectList', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseProjects.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
      refetch: vi.fn(),
    } as ReturnType<typeof useProjects>);
    mockUseCreateProject.mockReturnValue({
      mutateAsync: vi.fn(),
      isPending: false,
    } as ReturnType<typeof useCreateProject>);
  });

  it('shows skeleton while loading', () => {
    renderProjectList();
    // Skeleton component uses data-slot="skeleton"
    const skeletons = document.querySelectorAll('[data-slot="skeleton"]');
    expect(skeletons.length).toBeGreaterThanOrEqual(5);
  });

  it('shows error state on failure', () => {
    mockUseProjects.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('Network error'),
      refetch: vi.fn(),
    } as ReturnType<typeof useProjects>);

    renderProjectList();
    expect(screen.getByText('Network error')).toBeInTheDocument();
  });

  it('shows empty state when no projects', () => {
    mockUseProjects.mockReturnValue({
      data: { items: [], total: 0 },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    } as ReturnType<typeof useProjects>);

    renderProjectList();
    expect(screen.getByText('No projects yet')).toBeInTheDocument();
    expect(screen.getByText('New Project')).toBeInTheDocument();
  });

  it('renders project table with data', () => {
    mockUseProjects.mockReturnValue({
      data: {
        items: [
          { id: 'p1', name: 'Test Project', status: 'active', created_at: '2026-01-01T00:00:00Z', slug: 'test' },
          { id: 'p2', name: 'Another Project', status: 'paused', created_at: '2026-02-01T00:00:00Z', slug: 'another' },
        ],
        total: 2,
      },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    } as ReturnType<typeof useProjects>);

    renderProjectList();
    expect(screen.getByText('Test Project')).toBeInTheDocument();
    expect(screen.getByText('Another Project')).toBeInTheDocument();
    expect(screen.getByText('Projects')).toBeInTheDocument();
  });

  it('opens create dialog when New Project clicked', async () => {
    mockUseProjects.mockReturnValue({
      data: { items: [], total: 0 },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    } as ReturnType<typeof useProjects>);

    renderProjectList();
    fireEvent.click(screen.getByText('New Project'));
    expect(screen.getByText('Create')).toBeInTheDocument();
  });

  it('navigates to project on row click', async () => {
    mockUseProjects.mockReturnValue({
      data: {
        items: [{ id: 'p1', name: 'Test Project', status: 'active', created_at: '2026-01-01T00:00:00Z', slug: 'test' }],
        total: 1,
      },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    } as ReturnType<typeof useProjects>);

    renderProjectList();
    fireEvent.click(screen.getByText('Test Project'));
    expect(mockNavigate).toHaveBeenCalledWith({
      to: '/projects/$projectId',
      params: { projectId: 'p1' },
    });
  });
});
