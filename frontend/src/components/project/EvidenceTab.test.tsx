// EvidenceTab tests — TASK-0099 Sprint 3

import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { EvidenceTab } from './EvidenceTab';

vi.mock('@/hooks/use-task-execution', () => ({
  useTaskEvidence: vi.fn(),
}));

import { useTaskEvidence } from '@/hooks/use-task-execution';

const mockUseTaskEvidence = vi.mocked(useTaskEvidence);

function renderTab() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <EvidenceTab taskId="t1" />
    </QueryClientProvider>
  );
}

describe('EvidenceTab', () => {
  beforeEach(() => vi.clearAllMocks());

  it('renders loading state', () => {
    mockUseTaskEvidence.mockReturnValue({ data: undefined, isLoading: true } as any);
    renderTab();
    expect(screen.getByText('Loading...')).toBeDefined();
  });

  it('renders empty state', () => {
    mockUseTaskEvidence.mockReturnValue({ data: [], isLoading: false } as any);
    renderTab();
    expect(screen.getByText('No evidence')).toBeDefined();
  });

  it('renders evidence items', () => {
    mockUseTaskEvidence.mockReturnValue({
      data: [
        { id: 'e1', task_id: 't1', type: 'test_output', title: 'Test Results', description: 'All tests pass', verification_state: 'unverified', created_at: '2026-08-01T00:00:00Z', created_by_id: 'agent-1' },
      ],
      isLoading: false,
    } as any);
    renderTab();
    expect(screen.getByText('Test Results')).toBeDefined();
    expect(screen.getByText('All tests pass')).toBeDefined();
  });
});
