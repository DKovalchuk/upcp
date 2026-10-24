import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { TaskDistributionDonut } from './TaskDistributionDonut';

const mockNavigate = vi.fn();
vi.mock('@tanstack/react-router', () => ({
  useNavigate: () => mockNavigate,
}));

vi.mock('recharts', () => ({
  PieChart: ({ children }: { children?: React.ReactNode }) => <svg data-testid="pie-chart">{children}</svg>,
  Pie: ({
    onClick,
    data,
  }: {
    onClick?: (datum: unknown) => void;
    data?: Array<{ name: string; value: number; status: string }>;
  }) => (
    <g data-testid="pie-sectors">
      {data?.map((d) => (
        <g
          key={d.status}
          data-testid={`pie-sector-${d.status}`}
          onClick={() => onClick?.(d)}
        />
      ))}
    </g>
  ),
  Cell: () => <rect />,
  ResponsiveContainer: ({ children }: { children?: React.ReactNode }) => <div>{children}</div>,
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

  it('legend click navigates to delivery with status filter', () => {
    render(<TaskDistributionDonut counts={{ backlog: 4, done: 30 }} deliveryBase="/projects/p1/delivery" />);
    fireEvent.click(screen.getByText('Backlog'));
    expect(mockNavigate).toHaveBeenCalledWith({
      to: '/projects/p1/delivery',
      search: { status: 'backlog' },
    });
  });

  it('legend click for done navigates with status=done', () => {
    render(<TaskDistributionDonut counts={{ backlog: 4, done: 30 }} deliveryBase="/projects/p1/delivery" />);
    fireEvent.click(screen.getByText('Done'));
    expect(mockNavigate).toHaveBeenCalledWith({
      to: '/projects/p1/delivery',
      search: { status: 'done' },
    });
  });

  it('sector click navigates to delivery with that sector status', () => {
    render(<TaskDistributionDonut counts={{ backlog: 4, done: 30 }} deliveryBase="/projects/p1/delivery" />);
    fireEvent.click(screen.getByTestId('pie-sector-backlog'));
    expect(mockNavigate).toHaveBeenCalledWith({
      to: '/projects/p1/delivery',
      search: { status: 'backlog' },
    });
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

  it('decimal counts are rounded for display (B6.4)', () => {
    render(<TaskDistributionDonut counts={{ backlog: 2.4, done: 3.6 }} />);
    // legend shows integers (2.4 → 2, 3.6 → 4), never raw decimals
    expect(screen.queryByText('2.4')).not.toBeInTheDocument();
    expect(screen.queryByText('3.6')).not.toBeInTheDocument();
    const legendValues = screen.getAllByText(/^[0-9]+$/).map((n) => n.textContent);
    expect(legendValues).toContain('2');
    expect(legendValues).toContain('4');
    // center total is the rounded sum
    expect(screen.getByText('6')).toBeInTheDocument();
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

  // ── B4: positive rows ───────────────────────────

  it('renders one sector per non-zero status (B4.2)', () => {
    const { container } = render(
      <TaskDistributionDonut counts={{ backlog: 4, in_progress: 2, review: 1, done: 30, blocked: 1 }} />,
    );
    expect(container.querySelectorAll('[data-testid^="pie-sector-"]')).toHaveLength(5);
    expect(screen.getAllByTestId('pie-sector-backlog')).toHaveLength(1);
  });

  it('legend colors match the design palette (B4.5)', () => {
    render(
      <TaskDistributionDonut counts={{ backlog: 4, in_progress: 2, review: 1, done: 30, blocked: 1 }} />,
    );
    const expected: Array<[string, string]> = [
      ['Backlog', '#94a3b8'], // slate
      ['In Progress', '#3b82f6'], // blue
      ['Review', '#f59e0b'], // amber
      ['Done', '#10b981'], // emerald
      ['Blocked', '#ef4444'], // red
    ];
    for (const [name, hex] of expected) {
      const dot = screen.getByText(name).previousElementSibling;
      const rgb = `rgb(${parseInt(hex.slice(1, 3), 16)}, ${parseInt(hex.slice(3, 5), 16)}, ${parseInt(hex.slice(5, 7), 16)})`;
      expect([hex, rgb]).toContain(dot?.style.backgroundColor);
    }
  });

  it('all statuses equal render equal values (B4.7)', () => {
    const { container } = render(
      <TaskDistributionDonut
        counts={{ backlog: 5, in_progress: 5, review: 5, done: 5, blocked: 5 }}
      />,
    );
    expect(screen.getByText('25')).toBeInTheDocument(); // center total
    expect(container.querySelectorAll('[data-testid^="pie-sector-"]')).toHaveLength(5);
    for (const name of ['Backlog', 'In Progress', 'Review', 'Done', 'Blocked']) {
      expect(screen.getByText(name)).toBeInTheDocument();
      expect(screen.getByText(name).nextElementSibling).toHaveTextContent('5');
    }
  });

  it('renders a single task (B6.2)', () => {
    const { container } = render(<TaskDistributionDonut counts={{ done: 1 }} />);
    const centerTotal = container.querySelector('span.text-2xl');
    expect(centerTotal).toHaveTextContent('1');
    expect(screen.getByText('tasks')).toBeInTheDocument();
    expect(container.querySelectorAll('[data-testid^="pie-sector-"]')).toHaveLength(1);
  });

  // ── B5: sector navigation + keyboard ────────────

  const SECTOR_CASES: Array<[string, string]> = [
    ['backlog', 'Backlog'],
    ['in_progress', 'In Progress'],
    ['review', 'Review'],
    ['done', 'Done'],
    ['blocked', 'Blocked'],
  ];

  it.each(SECTOR_CASES)('clicking %s sector filters delivery by that status (B5.x)', (status) => {
    render(
      <TaskDistributionDonut
        counts={{ backlog: 4, in_progress: 2, review: 1, done: 30, blocked: 1 }}
        deliveryBase="/projects/p1/delivery"
      />,
    );
    fireEvent.click(screen.getByTestId(`pie-sector-${status}`));
    expect(mockNavigate).toHaveBeenCalledWith({
      to: '/projects/p1/delivery',
      search: { status },
    });
  });

  it('legend entries are native buttons (keyboard-activatable) (B5.6)', () => {
    // Sectors are SVG paths (not focusable); the keyboard path is the legend,
    // which renders native <button> elements — Enter/Space activation is
    // browser-native for buttons.
    render(<TaskDistributionDonut counts={{ backlog: 4, done: 30 }} />);
    expect(screen.getByRole('button', { name: /Backlog/ }).tagName).toBe('BUTTON');
    expect(screen.getByRole('button', { name: /Done/ }).tagName).toBe('BUTTON');
  });
});
