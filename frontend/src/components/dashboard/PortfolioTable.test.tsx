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
    tasks_done: i,
    tasks_total: i + 1,
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

  // ── B12: positive rows ──────────────────────────

  it('renders all expected columns (B12.2)', () => {
    render(<PortfolioTable projects={makeProjects(2)} projectStatuses={{ p1: 'active', p2: 'active' }} />);
    const headers = screen.getAllByRole('columnheader').map((th) => th.textContent);
    expect(headers).toEqual(['Project', 'Health', 'Tasks', 'Status', 'Top Issue']);
  });

  function findBarByWidth(container: HTMLElement, width: string): HTMLElement | undefined {
    return Array.from(container.querySelectorAll<HTMLElement>('div')).find(
      (el) => el.style.width === width,
    );
  }

  it('renders health progress bar with score (B12.3)', () => {
    const { container } = render(<PortfolioTable projects={makeProjects(2)} />);
    const bar = findBarByWidth(container, '61%');
    expect(bar).toBeTruthy();
    expect(screen.getByText('61%')).toBeInTheDocument();
  });

  const HEALTH_COLORS: Array<[number, string]> = [
    [85, 'bg-emerald-500'], // B12.4 ≥80 green
    [60, 'bg-amber-500'], // B12.5 50-79 amber
    [30, 'bg-red-500'], // B12.6 <50 red
    [0, 'bg-red-500'], // B13.10 minimum
  ];

  it.each(HEALTH_COLORS)('health %i uses color %s (B12.4-B12.6, B13.10)', (score, colorClass) => {
    const { container } = render(
      <PortfolioTable
        projects={[
          { id: 'p1', name: 'Alpha', slug: 'alpha', task_count: 3, tasks_done: 1, tasks_total: 3, health_score: score, top_issue: '' },
          { id: 'p2', name: 'Beta', slug: 'beta', task_count: 4, tasks_done: 2, tasks_total: 4, health_score: 70, top_issue: '' },
        ]}
      />,
    );
    const bar = findBarByWidth(container, `${score}%`);
    expect(bar, `bar for score ${score}`).toBeTruthy();
    expect(bar?.classList.contains(colorClass)).toBe(true);
  });

  // ── B12.7 / B13.7: done/total schema (closed in TASK-0154) ──

  it('tasks column shows done/total format (B12.7)', () => {
    render(
      <PortfolioTable
        projects={[
          { id: 'p1', name: 'Alpha', slug: 'alpha', task_count: 36, tasks_done: 30, tasks_total: 36, health_score: 70, top_issue: '' },
          { id: 'p2', name: 'Beta', slug: 'beta', task_count: 4, tasks_done: 3, tasks_total: 4, health_score: 80, top_issue: '' },
        ]}
      />,
    );
    expect(screen.getByText('30/36')).toBeInTheDocument();
    expect(screen.getByText('3/4')).toBeInTheDocument();
  });

  it('project with zero tasks shows 0/0 (B13.7)', () => {
    render(
      <PortfolioTable
        projects={[
          { id: 'p1', name: 'Alpha', slug: 'alpha', task_count: 0, tasks_done: 0, tasks_total: 0, health_score: 70, top_issue: '' },
          { id: 'p2', name: 'Beta', slug: 'beta', task_count: 4, tasks_done: 3, tasks_total: 4, health_score: 80, top_issue: '' },
        ]}
      />,
    );
    expect(screen.getByText('0/0')).toBeInTheDocument();
  });

  it('shows all 5 projects when exactly 5 (B13.4)', () => {
    render(<PortfolioTable projects={makeProjects(5)} />);
    for (let i = 1; i <= 5; i++) {
      expect(screen.getByText(`Project ${i}`)).toBeInTheDocument();
    }
  });

  it('renders two projects → table visible (B13.3)', () => {
    const { container } = render(<PortfolioTable projects={makeProjects(2)} />);
    expect(container.querySelector('table')).toBeInTheDocument();
    expect(screen.getByText('Project 1')).toBeInTheDocument();
    expect(screen.getByText('Project 2')).toBeInTheDocument();
  });
});
