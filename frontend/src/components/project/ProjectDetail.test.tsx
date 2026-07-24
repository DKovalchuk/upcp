import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ProjectDetail } from './ProjectDetail';

// Mock useLocation
vi.mock('@tanstack/react-router', async () => {
  const actual = await vi.importActual('@tanstack/react-router');
  return {
    ...actual,
    useLocation: () => ({ pathname: '/projects/test-project-id' }),
  };
});

// Mock hooks
vi.mock('@/hooks/use-projects', () => ({
  useProject: vi.fn(),
}));

vi.mock('@/hooks/use-components', () => ({
  useComponents: vi.fn(() => ({ data: [], isLoading: false })),
}));

vi.mock('@/hooks/use-features', () => ({
  useFeatures: vi.fn(() => ({ data: [], isLoading: false })),
}));

import { useProject } from '@/hooks/use-projects';
const mockUseProject = vi.mocked(useProject);

function renderProjectDetail() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <ProjectDetail />
    </QueryClientProvider>
  );
}

describe('ProjectDetail', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state', () => {
    mockUseProject.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    } as any);

    const { container } = renderProjectDetail();
    const skeletons = container.querySelectorAll('[data-slot="skeleton"]');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('renders error state when project not found', () => {
    mockUseProject.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('Not found'),
    } as any);

    renderProjectDetail();
    expect(screen.getByText('Not found')).toBeInTheDocument();
  });

  it('renders project name and description', () => {
    mockUseProject.mockReturnValue({
      data: {
        id: 'test-project-id',
        name: 'Test Project',
        slug: 'test-project',
        description: 'A test project description',
        status: 'active',
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-07-24T00:00:00Z',
      },
      isLoading: false,
      error: null,
    } as any);

    renderProjectDetail();
    // Name appears in header and in overview table
    const nameElements = screen.getAllByText('Test Project');
    expect(nameElements.length).toBeGreaterThanOrEqual(2);
    // Description appears in header and in overview table
    const descElements = screen.getAllByText('A test project description');
    expect(descElements.length).toBeGreaterThanOrEqual(2);
  });

  it('renders tab navigation', () => {
    mockUseProject.mockReturnValue({
      data: {
        id: 'test-project-id',
        name: 'Project',
        slug: 'project',
        description: null,
        status: 'active',
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-07-24T00:00:00Z',
      },
      isLoading: false,
      error: null,
    } as any);

    renderProjectDetail();
    expect(screen.getByRole('tab', { name: 'Overview' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Structure' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Delivery' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Quality' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Audit' })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Settings' })).toBeInTheDocument();
  });

  it('renders status badge', () => {
    mockUseProject.mockReturnValue({
      data: {
        id: 'test-project-id',
        name: 'P',
        slug: 'p',
        description: null,
        status: 'active',
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-07-24T00:00:00Z',
      },
      isLoading: false,
      error: null,
    } as any);

    renderProjectDetail();
    // Status badge appears in header
    const badges = screen.getAllByText('active');
    expect(badges.length).toBeGreaterThanOrEqual(1);
  });

  it('renders overview tab content by default', () => {
    mockUseProject.mockReturnValue({
      data: {
        id: 'test-project-id',
        name: 'My Project',
        slug: 'my-project',
        description: 'Desc',
        status: 'paused',
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-07-24T00:00:00Z',
      },
      isLoading: false,
      error: null,
    } as any);

    renderProjectDetail();
    expect(screen.getByText('Project Details')).toBeInTheDocument();
    expect(screen.getByText('Name')).toBeInTheDocument();
    expect(screen.getByText('Slug')).toBeInTheDocument();
    // my-project appears in slug field and sidebar nav
    const slugElements = screen.getAllByText('my-project');
    expect(slugElements.length).toBeGreaterThanOrEqual(1);
  });

  it('renders edit and delete buttons', () => {
    mockUseProject.mockReturnValue({
      data: {
        id: 'test-project-id',
        name: 'P',
        slug: 'p',
        description: null,
        status: 'active',
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-07-24T00:00:00Z',
      },
      isLoading: false,
      error: null,
    } as any);

    renderProjectDetail();
    // Edit (pencil) and Delete (trash) buttons
    const iconButtons = screen.getAllByRole('button');
    expect(iconButtons.length).toBeGreaterThanOrEqual(2);
  });
});
