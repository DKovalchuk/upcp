// ClarificationsTab tests — TASK-0099 Sprint 3

import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ClarificationsTab } from './ClarificationsTab';

vi.mock('@/hooks/use-task-execution', () => ({
  useTaskClarifications: vi.fn(),
  useAnswerClarification: vi.fn(),
}));

import { useTaskClarifications, useAnswerClarification } from '@/hooks/use-task-execution';

const mockUseTaskClarifications = vi.mocked(useTaskClarifications);
const mockUseAnswerClarification = vi.mocked(useAnswerClarification);

function renderTab() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <ClarificationsTab taskId="t1" taskName="Test Task" />
    </QueryClientProvider>
  );
}

describe('ClarificationsTab', () => {
  beforeEach(() => vi.clearAllMocks());

  it('renders loading state', () => {
    mockUseTaskClarifications.mockReturnValue({ data: undefined, isLoading: true } as ReturnType<typeof useTaskClarifications>);
    mockUseAnswerClarification.mockReturnValue({ mutate: vi.fn() } as ReturnType<typeof useAnswerClarification>);
    renderTab();
    expect(screen.getByText('Loading...')).toBeDefined();
  });

  it('renders empty state', () => {
    mockUseTaskClarifications.mockReturnValue({ data: { items: [] }, isLoading: false } as ReturnType<typeof useTaskClarifications>);
    mockUseAnswerClarification.mockReturnValue({ mutate: vi.fn() } as ReturnType<typeof useAnswerClarification>);
    renderTab();
    expect(screen.getByText('No clarifications')).toBeDefined();
  });

  it('renders clarifications', () => {
    mockUseTaskClarifications.mockReturnValue({
      data: {
        items: [
          { id: 'c1', task_id: 't1', author_id: 'agent-1', question: 'What format?', state: 'open', blocking: false, created_at: '2026-08-01T00:00:00Z' },
        ],
      },
      isLoading: false,
    } as ReturnType<typeof useTaskClarifications>);
    mockUseAnswerClarification.mockReturnValue({ mutate: vi.fn() } as ReturnType<typeof useAnswerClarification>);
    renderTab();
    expect(screen.getByText('What format?')).toBeDefined();
  });
});
