// ReviewsTab tests — TASK-0099 Sprint 3, TASK-0082 submit-for-review

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReviewsTab } from './ReviewsTab';

vi.mock('@/hooks/use-task-execution', () => ({
  useTaskReviewRounds: vi.fn(),
}));

vi.mock('@/lib/api', () => ({
  submitForReview: vi.fn(),
}));

vi.mock('@/lib/toast', () => ({
  showToast: {
    success: vi.fn(),
    error: vi.fn(),
    created: vi.fn(),
    updated: vi.fn(),
    mutationError: vi.fn(),
  },
}));

import { useTaskReviewRounds } from '@/hooks/use-task-execution';
import { submitForReview } from '@/lib/api';
import type { ReviewRound } from '@/types/quality';

const mockUseTaskReviewRounds = vi.mocked(useTaskReviewRounds);
const mockSubmitForReview = vi.mocked(submitForReview);

function renderTab(taskStatus?: string) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');
  render(
    <QueryClientProvider client={queryClient}>
      <ReviewsTab taskId="t1" taskStatus={taskStatus} />
    </QueryClientProvider>
  );
  return { queryClient, invalidateSpy };
}

const EMPTY_ROUNDS = { data: { items: [] }, isLoading: false } as ReturnType<
  typeof useTaskReviewRounds
>;

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

describe('ReviewsTab submit for review (TASK-0082)', () => {
  beforeEach(() => vi.clearAllMocks());

  it('renders Submit for review when task status is claimed', () => {
    mockUseTaskReviewRounds.mockReturnValue(EMPTY_ROUNDS);
    renderTab('claimed');
    expect(screen.getByRole('button', { name: /Submit for review/ })).toBeInTheDocument();
  });

  it('renders Submit for review when task status is in_progress', () => {
    mockUseTaskReviewRounds.mockReturnValue(EMPTY_ROUNDS);
    renderTab('in_progress');
    expect(screen.getByRole('button', { name: /Submit for review/ })).toBeInTheDocument();
  });

  it.each(['ready_for_review', 'in_review', 'done', 'changes_requested', 'cancelled', 'backlog'])(
    'does not render Submit for review when task status is %s',
    (status) => {
      mockUseTaskReviewRounds.mockReturnValue(EMPTY_ROUNDS);
      renderTab(status);
      expect(screen.queryByRole('button', { name: /Submit for review/ })).toBeNull();
    }
  );

  it('calls submitForReview with the task id and invalidates task/rounds queries on success', async () => {
    mockUseTaskReviewRounds.mockReturnValue(EMPTY_ROUNDS);
    mockSubmitForReview.mockResolvedValue({ id: 'rr-new' } as ReviewRound);
    const { invalidateSpy } = renderTab('claimed');

    fireEvent.click(screen.getByRole('button', { name: /Submit for review/ }));

    await waitFor(() => {
      expect(mockSubmitForReview).toHaveBeenCalledWith('t1');
    });
    await waitFor(() => {
      // task detail (['tasks','t1']) and review rounds (['tasks','t1','review-rounds'])
      // share this prefix; the status transition to ready_for_review is refetched too
      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['tasks'] });
      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['tasks', 't1'] });
    });
  });

  it('shows the server gate detail on 400 failure without crashing', async () => {
    mockUseTaskReviewRounds.mockReturnValue(EMPTY_ROUNDS);
    mockSubmitForReview.mockRejectedValue(
      new Error("dod_not_satisfied: unit tests; evidence_required: 'test_output'")
    );
    const { invalidateSpy } = renderTab('claimed');

    fireEvent.click(screen.getByRole('button', { name: /Submit for review/ }));

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(
        "dod_not_satisfied: unit tests; evidence_required: 'test_output'"
      );
    });
    // no crash: the tab still renders its controls and nothing was invalidated
    expect(screen.getByRole('button', { name: /Submit for review/ })).toBeInTheDocument();
    expect(screen.getByText('No reviews')).toBeInTheDocument();
    expect(invalidateSpy).not.toHaveBeenCalled();
  });
});
