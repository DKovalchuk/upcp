import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { PortfolioTable } from './PortfolioTable';
import type { PortfolioProject } from '@/types/dashboard';

const mockNavigate = vi.fn();
vi.mock('@tanstack/react-router', () => ({
  Link: ({ children, to, params, onClick, ...rest }: any) => {
    const href =
      typeof to === 'string' ? to.replace('$projectId', params?.projectId ?? '') : to;
    return (
      <a
        href={href}
        {...rest}
        onClick={(e) => {
          e.preventDefault();
          onClick?.(e);
        }}
      >
        {children}
      </a>
    );
  },
  useNavigate: () => mockNavigate,
}));

function makeProjects(count: number): PortfolioProject[] {
  return Array.from({ length: count }, (_, i) => ({
    id: `p${i + 1}`,
    name: `Project ${i + 1}`,
    slug: `project-${i + 1}`,
    task_count: i + 1,
    health_score: 60 + i,
    top_issue: '',
  }));
}

describe('PortfolioTable — TASK-0124', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('is hidden when only one project exists', () => {
    const { container } = render(<PortfolioTable projects={makeProjects(1)} />);
    expect(container.firstChild).toBeNull();
  });

  it('is hidden when projects are undefined', () => {
    const { container } = render(<PortfolioTable projects={undefined} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders a Status column with status badges', () => {
    render(
      <PortfolioTable
        projects={makeProjects(2)}
        projectStatuses={{ p1: 'active', p2: 'archived' }}
      />,
    );
    expect(screen.getByText('Status')).toBeInTheDocument();
    expect(screen.getByText('Active')).toBeInTheDocument();
    expect(screen.getByText('Archived')).toBeInTheDocument();
  });

  it('renders placeholder when status is unknown', () => {
    render(<PortfolioTable projects={makeProjects(2)} projectStatuses={{}} />);
    expect(screen.getAllByText('—').length).toBeGreaterThan(0);
  });

  it('row click navigates to project detail', () => {
    render(<PortfolioTable projects={makeProjects(3)} />);
    // Click a non-link cell (health percent) so only the row handler fires
    fireEvent.click(screen.getByText('61%'));
    expect(mockNavigate).toHaveBeenCalledWith({
      to: '/projects/$projectId',
      params: { projectId: 'p2' },
    });
  });

  it('name link keeps working without double row navigation', () => {
    render(<PortfolioTable projects={makeProjects(3)} />);
    const link = screen.getByRole('link', { name: 'Project 1' });
    expect(link).toHaveAttribute('href', '/projects/p1');
    fireEvent.click(link);
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('shows first 5 projects with a Show more button when over 5', () => {
    render(<PortfolioTable projects={makeProjects(6)} />);
    expect(screen.getByText('Project 5')).toBeInTheDocument();
    expect(screen.queryByText('Project 6')).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /show more/i }));
    expect(screen.getByText('Project 6')).toBeInTheDocument();
  });

  it('no Show more button when 5 or fewer projects', () => {
    render(<PortfolioTable projects={makeProjects(5)} />);
    expect(screen.queryByRole('button', { name: /show more/i })).not.toBeInTheDocument();
    expect(screen.getByText('Project 5')).toBeInTheDocument();
  });

  it('renders loading skeleton while loading', () => {
    render(<PortfolioTable projects={makeProjects(2)} isLoading />);
    expect(screen.getByText('Portfolio')).toBeInTheDocument();
    expect(screen.queryByText('Project 1')).not.toBeInTheDocument();
  });
});
