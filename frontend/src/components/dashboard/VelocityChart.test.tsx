import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { VelocityChart } from './VelocityChart';

const mockNavigate = vi.fn();
vi.mock('@tanstack/react-router', () => ({
  useNavigate: () => mockNavigate,
}));

vi.mock('recharts', () => ({
  AreaChart: ({ onClick, data }: any) => (
    <svg data-testid="area-chart" onClick={() => onClick?.({ activePayload: data })} />
  ),
  Area: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
  ResponsiveContainer: ({ children }: any) => <div>{children}</div>,
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
});
