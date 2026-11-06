import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { VelocityChart } from './VelocityChart';

const mockNavigate = vi.fn();
vi.mock('@tanstack/react-router', () => ({
  useNavigate: () => mockNavigate,
}));

vi.mock('recharts', () => ({
  AreaChart: ({
    onClick,
    data,
    children,
  }: {
    onClick?: (payload: unknown) => void;
    data?: unknown[];
    children?: React.ReactNode;
  }) => (
    <svg data-testid="area-chart" onClick={() => onClick?.({ activePayload: data })}>
      {children}
      {Array.isArray(data) && data.map((_, i) => <g key={i} data-testid="area-point" />)}
    </svg>
  ),
  Area: ({ fill }: { fill?: string }) => <path data-testid="area-fill" fill={fill} />,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
  ResponsiveContainer: ({ children }: { children?: React.ReactNode }) => <div>{children}</div>,
}));

describe('VelocityChart', () => {
  it('renders loading state', () => {
    render(<VelocityChart data={undefined} isLoading />);
    expect(screen.getByText('Velocity (8 weeks)')).toBeInTheDocument();
  });

  it('renders empty state when no data', () => {
    render(<VelocityChart data={[]} isLoading={false} />);
    expect(screen.getByText('No completed tasks yet')).toBeInTheDocument();
  });

  it('renders empty state when all counts are zero', () => {
    render(<VelocityChart data={[{ week: '2026-W35', count: 0 }, { week: '2026-W36', count: 0 }]} isLoading={false} />);
    expect(screen.getByText('No completed tasks yet')).toBeInTheDocument();
  });

  it('renders chart with data', () => {
    render(
      <VelocityChart
        data={[
          { week: '2026-W33', count: 5 },
          { week: '2026-W34', count: 8 },
          { week: '2026-W35', count: 3 },
        ]}
        isLoading={false}
      />,
    );
    expect(screen.getByText('Velocity (8 weeks)')).toBeInTheDocument();
  });

  it('shows title always', () => {
    render(<VelocityChart data={[{ week: '2026-W35', count: 1 }]} isLoading={false} />);
    expect(screen.getByText('Velocity (8 weeks)')).toBeInTheDocument();
  });

  it('renders with large spike', () => {
    render(
      <VelocityChart
        data={[
          { week: '2026-W34', count: 0 },
          { week: '2026-W35', count: 100 },
        ]}
        isLoading={false}
      />,
    );
    expect(screen.getByText('Velocity (8 weeks)')).toBeInTheDocument();
  });

  it('renders with single data point', () => {
    render(<VelocityChart data={[{ week: '2026-W36', count: 7 }]} isLoading={false} />);
    expect(screen.getByText('Velocity (8 weeks)')).toBeInTheDocument();
    expect(screen.queryByText('No completed tasks yet')).not.toBeInTheDocument();
  });

  it('chart click navigates to delivery filtered by status=done', () => {
    render(
      <VelocityChart
        data={[{ week: '2026-W35', count: 5 }]}
        isLoading={false}
        deliveryBase="/projects/p1/delivery"
      />,
    );
    fireEvent.click(screen.getByTestId('area-chart'));
    expect(mockNavigate).toHaveBeenCalledWith({
      to: '/projects/p1/delivery',
      search: { status: 'done' },
    });
  });

  it('chart click navigates to projects when no deliveryBase', () => {
    render(<VelocityChart data={[{ week: '2026-W35', count: 5 }]} isLoading={false} />);
    fireEvent.click(screen.getByTestId('area-chart'));
    expect(mockNavigate).toHaveBeenCalledWith({ to: '/projects' });
  });

  // ── B7: positive rows ───────────────────────────

  it('renders 8 data points for default weeks (B7.2)', () => {
    const data = Array.from({ length: 8 }, (_, i) => ({ week: `2026-W${30 + i}`, count: i }));
    render(<VelocityChart data={data} isLoading={false} />);
    expect(screen.getAllByTestId('area-point')).toHaveLength(8);
    expect(screen.getByTestId('area-chart')).toBeInTheDocument();
  });

  it('renders custom weeks count (B7.3)', () => {
    const data = [
      { week: '2026-W35', count: 1 },
      { week: '2026-W36', count: 2 },
      { week: '2026-W37', count: 3 },
      { week: '2026-W38', count: 4 },
    ];
    render(<VelocityChart data={data} isLoading={false} />);
    expect(screen.getAllByTestId('area-point')).toHaveLength(4);
  });

  it('gradient fill defined and referenced by the area (B7.7)', () => {
    const { container } = render(
      <VelocityChart data={[{ week: '2026-W35', count: 5 }]} isLoading={false} />,
    );
    const gradient = container.querySelector('#velocityGradient');
    expect(gradient).toBeTruthy();
    expect(gradient?.tagName.toLowerCase()).toBe('lineargradient');
    expect(screen.getByTestId('area-fill')).toHaveAttribute('fill', 'url(#velocityGradient)');
  });

  // ── B8: edge cases ──────────────────────────────

  it('renders across year boundary W52 → W1 (B8.5)', () => {
    render(
      <VelocityChart
        data={[
          { week: '2026-W52', count: 4 },
          { week: '2027-W01', count: 6 },
        ]}
        isLoading={false}
      />,
    );
    expect(screen.getAllByTestId('area-point')).toHaveLength(2);
    expect(screen.queryByText('No completed tasks yet')).not.toBeInTheDocument();
  });

  it('falls back to empty state on API error (no data, not loading) (B8.6)', () => {
    // Component has no explicit error branch: a failed query yields
    // data=undefined + isLoading=false → graceful empty state, no crash.
    render(<VelocityChart data={undefined} isLoading={false} />);
    expect(screen.getByText('No completed tasks yet')).toBeInTheDocument();
    expect(screen.getByText('Velocity (8 weeks)')).toBeInTheDocument();
  });
});
