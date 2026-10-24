// ReviewsTab tests — TASK-0099 Sprint 3

import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReviewsTab } from './ReviewsTab';

vi.mock('@/hooks/use-task-execution', () => ({
  useTaskReviewRounds: vi.fn(),
}));

import { useTaskReviewRounds } from '@/hooks/use-task-execution';

const mockUseTaskReviewRounds = vi.mocked(useTaskReviewRounds);

function renderTab() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <ReviewsTab taskId="t1" />
    </QueryClientProvider>
  );
}

describe('ReviewsTab', () => {
  beforeEach(() => vi.clearAllMocks());

  it('renders loading state', () => {
    mockUseTaskReviewRounds.mockReturnValue({ data: undefined, isLoading: true } as ReturnType<typeof useTaskReviewRounds>);
    renderTab();
    expect(screen.getByText('Loading...')).toBeDefined();
  });

  it('renders empty state', () => {
    mockUseTaskReviewRounds.mockReturnValue({ data: [], isLoading: false } as ReturnType<typeof useTaskReviewRounds>);
    renderTab();
    expect(screen.getByText('No reviews')).toBeDefined();
  });

  it('renders review rounds', () => {
    mockUseTaskReviewRounds.mockReturnValue({
      data: {
        items: [
          { id: 'r1', task_id: 't1', reviewer_id: 'reviewer-1', state: 'completed', verdict: 'approve', confidence: 90, summary: 'Looks good', created_at: '2026-08-01T00:00:00Z' },
        ],
      },
      isLoading: false,
    } as ReturnType<typeof useTaskReviewRounds>);
    renderTab();
    expect(screen.getByText('reviewer-1')).toBeDefined();
    expect(screen.getByText('Looks good')).toBeDefined();
  });
});
