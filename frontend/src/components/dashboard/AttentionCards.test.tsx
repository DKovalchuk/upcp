import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import {
  BlockedTasksSection,
  NeedsReviewSection,
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
});

describe('useAttentionDashboard — project scoping (TASK-0125)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('passes projectId to fetch and keys the query by it', async () => {
    mockFetch.mockResolvedValue({ blocked_tasks: [] } as any);
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
    mockFetch.mockResolvedValue({ blocked_tasks: [] } as any);
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
