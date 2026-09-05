import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { TaskDistributionDonut } from './TaskDistributionDonut';

const mockNavigate = vi.fn();
vi.mock('@tanstack/react-router', () => ({
  useNavigate: () => mockNavigate,
}));

vi.mock('recharts', () => ({
  PieChart: ({ children }: any) => <svg data-testid="pie-chart">{children}</svg>,
  Pie: () => <g data-testid="pie" />,
  Cell: () => <rect />,
  ResponsiveContainer: ({ children }: any) => <div>{children}</div>,
  Tooltip: () => null,
}));

describe('TaskDistributionDonut', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders empty state when no counts', () => {
    render(<TaskDistributionDonut counts={undefined} />);
    expect(screen.getByText('No tasks yet')).toBeInTheDocument();
  });

  it('renders empty state when all counts are zero', () => {
    render(<TaskDistributionDonut counts={{ backlog: 0, in_progress: 0, done: 0 }} />);
    expect(screen.getByText('No tasks yet')).toBeInTheDocument();
  });

  it('renders donut chart with data', () => {
    render(<TaskDistributionDonut counts={{ backlog: 4, in_progress: 2, done: 30 }} />);
    expect(screen.getByText('36')).toBeInTheDocument(); // center total
    expect(screen.getByText('tasks')).toBeInTheDocument();
  });

  it('renders legend with correct counts', () => {
    render(<TaskDistributionDonut counts={{ backlog: 4, in_progress: 2, review: 1, done: 30, blocked: 1 }} />);
    expect(screen.getByText('Backlog')).toBeInTheDocument();
    expect(screen.getByText('In Progress')).toBeInTheDocument();
    expect(screen.getByText('Review')).toBeInTheDocument();
    expect(screen.getByText('Done')).toBeInTheDocument();
    expect(screen.getByText('Blocked')).toBeInTheDocument();
    expect(screen.getByText('30')).toBeInTheDocument();
    expect(screen.getByText('4')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument();
  });

  it('only shows non-zero statuses in legend', () => {
    render(<TaskDistributionDonut counts={{ backlog: 0, in_progress: 0, done: 10 }} />);
    expect(screen.queryByText('Backlog')).not.toBeInTheDocument();
    expect(screen.queryByText('In Progress')).not.toBeInTheDocument();
    expect(screen.getByText('Done')).toBeInTheDocument();
  });

  it('legend click navigates to delivery', () => {
    render(<TaskDistributionDonut counts={{ backlog: 4, done: 30 }} deliveryBase="/projects/p1/delivery" />);
    fireEvent.click(screen.getByText('Backlog'));
    expect(mockNavigate).toHaveBeenCalledWith({ to: '/projects/p1/delivery' });
  });

  it('legend click navigates to projects when no deliveryBase', () => {
    render(<TaskDistributionDonut counts={{ done: 30 }} />);
    fireEvent.click(screen.getByText('Done'));
    expect(mockNavigate).toHaveBeenCalledWith({ to: '/projects' });
  });

  it('renders single status correctly', () => {
    render(<TaskDistributionDonut counts={{ done: 5 }} />);
    expect(screen.getByText('Done')).toBeInTheDocument();
    expect(screen.getByText('tasks')).toBeInTheDocument();
  });

  it('renders with large numbers', () => {
    render(<TaskDistributionDonut counts={{ backlog: 9999, done: 99999 }} />);
    expect(screen.getByText('109998')).toBeInTheDocument(); // center total
  });

  it('renders SVG chart element', () => {
    const { container } = render(<TaskDistributionDonut counts={{ backlog: 4, done: 30 }} />);
    expect(container.querySelector('svg')).toBeInTheDocument();
  });

  it('handles partial counts object', () => {
    render(<TaskDistributionDonut counts={{ done: 10 }} />);
    expect(screen.getByText('Done')).toBeInTheDocument();
    expect(screen.getByText('tasks')).toBeInTheDocument();
    expect(screen.queryByText('Backlog')).not.toBeInTheDocument();
  });
});
