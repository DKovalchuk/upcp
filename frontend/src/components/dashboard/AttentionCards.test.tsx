import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import {
  BlockedTasksSection,
  FailedQualityGatesSection,
  NeedsReviewSection,
  OpenClarificationsSection,
  RejectedTasksSection,
  StaleAgentsSection,
  AgentVerdictsSection,
  LowHealthProjectsSection,
  useAttentionDashboard,
} from './AttentionCards';
import { fetchAttentionDashboard } from '@/lib/api';
import type { AttentionItem } from '@/types/dashboard';

vi.mock('@/lib/api', () => ({
  fetchAttentionDashboard: vi.fn(),
}));

vi.mock('@tanstack/react-router', () => ({
  Link: ({ children, to, params, search, className }: any) => {
    let href: string = to;
    if (params && typeof href === 'string') {
      href = href.replace('$projectId', params.projectId ?? '');
    }
    if (search) {
      href += `?${new URLSearchParams(search as Record<string, string>).toString()}`;
    }
    return (
      <a href={href} className={className}>
        {children}
      </a>
    );
  },
}));

const mockFetch = vi.mocked(fetchAttentionDashboard);

function makeItems(count: number, projectId?: string): AttentionItem[] {
  return Array.from({ length: count }, (_, i) => ({
    task_id: `task-${i + 1}`,
    project_id: projectId,
    title: `Task ${i + 1}`,
  }));
}

describe('AttentionSections — View all link (TASK-0123)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows View all link when section has more than 3 items', () => {
    render(<BlockedTasksSection items={makeItems(4, 'p1')} />);
    const link = screen.getByRole('link', { name: /view all/i });
    expect(link).toHaveAttribute('href', '/projects/p1/delivery?status=blocked');
  });

  it('omits View all link when section has 3 or fewer items', () => {
    render(<BlockedTasksSection items={makeItems(3, 'p1')} />);
    expect(screen.queryByRole('link', { name: /view all/i })).not.toBeInTheDocument();
  });

  it('needs review section links with status=review filter', () => {
    render(<NeedsReviewSection items={makeItems(4, 'p1')} />);
    const link = screen.getByRole('link', { name: /view all/i });
    expect(link).toHaveAttribute('href', '/projects/p1/delivery?status=review');
  });

  it('falls back to /projects when items carry no project_id', () => {
    render(<BlockedTasksSection items={makeItems(4)} />);
    const link = screen.getByRole('link', { name: /view all/i });
    expect(link).toHaveAttribute('href', '/projects');
  });

  it('task items are links when task_id and project_id are present', () => {
    render(<BlockedTasksSection items={[{ task_id: 't1', project_id: 'p1', title: 'Blocked one' }]} />);
    const link = screen.getByRole('link', { name: 'Blocked one' });
    expect(link).toHaveAttribute('href', '/projects/p1/delivery');
  });

  it('task items without project render as non-link blocks', () => {
    render(<BlockedTasksSection items={[{ task_id: 't1', title: 'Blocked one' }]} />);
    expect(screen.queryByRole('link', { name: 'Blocked one' })).not.toBeInTheDocument();
    expect(screen.getByText('Blocked one')).toBeInTheDocument();
  });

  // ── B9: positive rows ───────────────────────────

  it('renders all 7 attention sections with titles (B9.1)', () => {
    render(
      <>
        <NeedsReviewSection items={[]} />
        <OpenClarificationsSection items={[]} />
        <BlockedTasksSection items={[]} />
        <StaleAgentsSection items={[]} />
        <FailedQualityGatesSection items={[]} />
        <RejectedTasksSection items={[]} />
        <AgentVerdictsSection items={[]} />
      </>,
    );
    for (const title of [
      'Needs Your Review',
      'Open Questions',
      'Blocked Tasks',
      'Stale Agent Claims',
      'Failed Quality Gates',
      'Rejected Tasks',
      'Verdicts Waiting',
    ]) {
      expect(screen.getByText(title), title).toBeInTheDocument();
    }
  });

  it('renders the Low Health Projects section as 8th section (B9.2)', () => {
    render(
      <LowHealthProjectsSection
        items={[{ project_id: 'p9', project_name: 'Alpha', health_score: 42, top_issue: 'stale' }]}
      />,
    );
    expect(screen.getByText('Low Health Projects')).toBeInTheDocument();
  });

  it('shows count badge when section has items (B9.3)', () => {
    render(<BlockedTasksSection items={makeItems(4, 'p1')} />);
    expect(screen.getByText('4')).toBeInTheDocument();
  });

  it('hides count badge when section is empty (B9.4)', () => {
    const { container } = render(<BlockedTasksSection items={[]} />);
    expect(screen.queryByText('0')).not.toBeInTheDocument();
    expect(container.querySelector('[class*="bg-primary/10"]')).toBeNull();
    expect(screen.getByText('No blocked tasks')).toBeInTheDocument();
  });

  it('items show metadata: author, failed items, verdict confidence (B9.6)', () => {
    render(
      <>
        <NeedsReviewSection
          items={[{ task_id: 't1', project_id: 'p1', requested_by: 'alice' }]}
        />
        <OpenClarificationsSection
          items={[{ task_id: 't2', project_id: 'p1', question: 'Why?', author: 'bob' }]}
        />
        <FailedQualityGatesSection
          items={[{ task_id: 't3', project_id: 'p1', failed_items: ['tests', 'lint'] }]}
        />
        <AgentVerdictsSection
          items={[{ task_id: 't4', project_id: 'p1', verdict: 'approve', confidence: 92 }]}
        />
      </>,
    );
    expect(screen.getByText('by alice')).toBeInTheDocument();
    expect(screen.getByText('Why?')).toBeInTheDocument();
    expect(screen.getByText('from bob')).toBeInTheDocument();
    expect(screen.getByText('failed: tests, lint')).toBeInTheDocument();
    expect(screen.getByText('approve')).toBeInTheDocument();
    expect(screen.getByText('92% confidence')).toBeInTheDocument();
  });

  // ── B10: navigation rows ────────────────────────

  it('review item links to task detail (B10.1)', () => {
    render(<NeedsReviewSection items={[{ task_id: 't1', project_id: 'p1', requested_by: 'a' }]} />);
    expect(screen.getByRole('link', { name: /t1/ })).toHaveAttribute('href', '/projects/p1/delivery');
  });

  it('verdict item links to task detail (B10.7 equivalent — shared TaskLink)', () => {
    render(
      <AgentVerdictsSection
        items={[{ task_id: 't1', project_id: 'p1', verdict: 'reject', confidence: 80 }]}
      />,
    );
    expect(screen.getByRole('link', { name: /reject/ })).toHaveAttribute(
      'href',
      '/projects/p1/delivery',
    );
  });

  it('low health project links to project detail (B10.8)', () => {
    render(
      <LowHealthProjectsSection
        items={[{ project_id: 'p9', project_name: 'Alpha', health_score: 42 }]}
      />,
    );
    expect(screen.getByRole('link', { name: /Alpha/ })).toHaveAttribute('href', '/projects/p9');
  });

  // ── B11: edge cases ─────────────────────────────

  it('all sections show empty messages when empty (B11.1)', () => {
    render(
      <>
        <NeedsReviewSection items={[]} />
        <OpenClarificationsSection items={[]} />
        <BlockedTasksSection items={[]} />
        <StaleAgentsSection items={[]} />
        <FailedQualityGatesSection items={[]} />
        <RejectedTasksSection items={[]} />
        <AgentVerdictsSection items={[]} />
      </>,
    );
    for (const msg of [
      'No items awaiting review',
      'No open questions',
      'No blocked tasks',
      'All agents are active',
      'All quality gates passing',
      'No rejected tasks',
      'No verdicts awaiting confirmation',
    ]) {
      expect(screen.getByText(msg), msg).toBeInTheDocument();
    }
    expect(screen.queryByText('Low Health Projects')).not.toBeInTheDocument();
  });

  it('renders 50 items in one section (B11.2)', () => {
    render(<BlockedTasksSection items={makeItems(50, 'p1')} />);
    expect(screen.getAllByRole('link', { name: /^Task \d+$/ })).toHaveLength(50);
    expect(screen.getByText('50')).toBeInTheDocument(); // count badge
  });

  it('long question title gets truncation class (B11.3)', () => {
    const longQuestion = 'Q'.repeat(300);
    render(
      <OpenClarificationsSection
        items={[{ task_id: 't1', project_id: 'p1', question: longQuestion, author: 'bob' }]}
      />,
    );
    expect(screen.getByText(longQuestion)).toHaveClass('truncate');
  });

  it('item with empty title still renders as link, no crash (B11.4)', () => {
    const { container } = render(
      <BlockedTasksSection items={[{ task_id: 't1', project_id: 'p1', title: '' }]} />,
    );
    expect(container.querySelector('a')).toBeTruthy();
  });

  it('stale claim without heartbeat renders fine (B11.6)', () => {
    // Section displays task id + agent id only; heartbeat is not part of the
    // render path, so a NULL heartbeat cannot break it.
    render(
      <StaleAgentsSection items={[{ task_id: 'task-12345678', project_id: 'p1', agent_id: 'agent-1' }]} />,
    );
    expect(screen.getByText('task-123')).toBeInTheDocument();
    expect(screen.getByText('agent: agent-1')).toBeInTheDocument();
  });

  it('failed DoD section with empty list shows empty message (B11.7)', () => {
    render(<FailedQualityGatesSection items={[]} />);
    // Copy is "All quality gates passing" (task row said "No failed items")
    expect(screen.getByText('All quality gates passing')).toBeInTheDocument();
  });
});

describe('useAttentionDashboard — project scoping (TASK-0125)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('passes projectId to fetch and keys the query by it', async () => {
    mockFetch.mockResolvedValue({ blocked_tasks: [] } as ReturnType<typeof fetchAttentionDashboard>);
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    const { result } = renderHook(() => useAttentionDashboard('p1'), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockFetch).toHaveBeenCalledWith('p1');
    expect(queryClient.getQueryData(['attention-dashboard', 'p1'])).toEqual({
      blocked_tasks: [],
    });
  });

  it('fetches without project when no projectId given', async () => {
    mockFetch.mockResolvedValue({ blocked_tasks: [] } as ReturnType<typeof fetchAttentionDashboard>);
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );

    const { result } = renderHook(() => useAttentionDashboard(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(mockFetch).toHaveBeenCalledWith(undefined);
  });
});
