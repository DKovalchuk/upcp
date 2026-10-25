import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BreadcrumbBar } from './BreadcrumbBar';

const mockMatches = vi.fn();
vi.mock('@tanstack/react-router', () => ({
  useMatches: () => mockMatches(),
  Link: ({
    to,
    children,
    className,
  }: {
    to: string;
    children: React.ReactNode;
    className?: string;
  }) => (
    <a href={to} className={className}>
      {children}
    </a>
  ),
}));

vi.mock('@/hooks/use-projects', () => ({ useProject: vi.fn() }));

import { useProject } from '@/hooks/use-projects';
const mockUseProject = vi.mocked(useProject);

const PROJECT_UUID = 'a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d';

function mockPath(pathname: string) {
  mockMatches.mockReturnValue([{ pathname }]);
}

describe('BreadcrumbBar', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseProject.mockReturnValue({
      data: undefined,
      isLoading: true,
    } as ReturnType<typeof useProject>);
  });

  it('resolves project name instead of raw UUID', () => {
    mockPath(`/projects/${PROJECT_UUID}/delivery`);
    mockUseProject.mockReturnValue({
      data: { id: PROJECT_UUID, name: 'Apollo' },
      isLoading: false,
    } as ReturnType<typeof useProject>);

    render(<BreadcrumbBar />);

    expect(screen.getByText('Projects')).toBeInTheDocument();
    expect(screen.getByText('Apollo')).toBeInTheDocument();
    expect(screen.getByText('Delivery')).toBeInTheDocument();
    expect(document.body.textContent).not.toContain(PROJECT_UUID);
  });

  it('project crumb links to the project overview', () => {
    mockPath(`/projects/${PROJECT_UUID}/delivery`);
    mockUseProject.mockReturnValue({
      data: { id: PROJECT_UUID, name: 'Apollo' },
      isLoading: false,
    } as ReturnType<typeof useProject>);

    render(<BreadcrumbBar />);

    const link = screen.getByRole('link', { name: 'Apollo' });
    expect(link).toHaveAttribute('href', `/projects/${PROJECT_UUID}`);
  });

  it('shows a fallback label while the project name loads (no raw UUID)', () => {
    mockPath(`/projects/${PROJECT_UUID}/delivery`);
    mockUseProject.mockReturnValue({
      data: undefined,
      isLoading: true,
    } as ReturnType<typeof useProject>);

    render(<BreadcrumbBar />);

    expect(screen.getByText('Project')).toBeInTheDocument();
    expect(document.body.textContent).not.toContain(PROJECT_UUID);
  });

  it('does not fetch project data for paths without a project UUID', () => {
    mockPath('/settings');

    render(<BreadcrumbBar />);

    expect(screen.getByText('Settings')).toBeInTheDocument();
    expect(mockUseProject).toHaveBeenCalledWith('');
  });

  it('does not treat an agent UUID as a project id (no wrong-entity fetch)', () => {
    // Regression (TASK-0159): the first-uuid-as-project rule fetched
    // GET /api/v1/projects/<agentId> -> 404 on every agent detail page,
    // which failed CI e2e "2.4 — Agent Detail page loads" (console errors).
    const AGENT_UUID = '11111111-2222-3333-4444-555555555555';
    mockPath(`/agents/${AGENT_UUID}`);

    render(<BreadcrumbBar />);

    expect(mockUseProject).toHaveBeenCalledWith('');
    expect(screen.getByText('Agents')).toBeInTheDocument();
    expect(screen.queryByText('Project')).not.toBeInTheDocument();
  });
});
