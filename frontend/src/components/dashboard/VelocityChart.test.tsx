import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { VelocityChart } from './VelocityChart';

const mockNavigate = vi.fn();
vi.mock('@tanstack/react-router', () => ({
  useNavigate: () => mockNavigate,
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
});
