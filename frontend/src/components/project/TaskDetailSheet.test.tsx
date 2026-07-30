import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TaskDetailSheet } from './TaskDetailSheet';

// Mock the API functions
vi.mock('@/lib/api', () => ({
  fetchTask: vi.fn(),
  fetchTaskClaims: vi.fn(),
  fetchTaskHeartbeats: vi.fn(),
  fetchTaskClarifications: vi.fn(),
  fetchEvidence: vi.fn(),
  fetchReviewRounds: vi.fn(),
  releaseTask: vi.fn(),
}));

// Mock the toast
vi.mock('@/lib/toast', () => ({
  showToast: {
    success: vi.fn(),
    error: vi.fn(),
    created: vi.fn(),
    updated: vi.fn(),
    deleted: vi.fn(),
    mutationError: vi.fn(),
  },
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
};

describe('TaskDetailSheet', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', async () => {
    const { fetchTask } = await import('@/lib/api');
    vi.mocked(fetchTask).mockImplementation(() => new Promise(() => {}));

    render(
      <TaskDetailSheet taskId="task-123" onOpenChange={vi.fn()} />,
      { wrapper: createWrapper() }
    );

    // Should show skeleton loaders
    expect(document.querySelector('.animate-pulse')).toBeTruthy();
  });

  it('renders task details when loaded', async () => {
    const { fetchTask, fetchTaskClaims, fetchTaskHeartbeats, fetchTaskClarifications, fetchEvidence, fetchReviewRounds } = await import('@/lib/api');

    vi.mocked(fetchTask).mockResolvedValue({
      id: 'task-123',
      feature_id: 'feature-1',
      title: 'Test Task',
      description: 'Test description',
      status: 'in-progress',
      priority: 1,
      assignee_type: null,
      assignee_id: null,
      component_id: null,
      module_id: null,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    });

    vi.mocked(fetchTaskClaims).mockResolvedValue({ items: [] });
    vi.mocked(fetchTaskHeartbeats).mockResolvedValue({ items: [] });
    vi.mocked(fetchTaskClarifications).mockResolvedValue({ items: [] });
    vi.mocked(fetchEvidence).mockResolvedValue({ items: [] });
    vi.mocked(fetchReviewRounds).mockResolvedValue({ items: [] });

    render(
      <TaskDetailSheet taskId="task-123" onOpenChange={vi.fn()} />,
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(screen.getByText('Test Task')).toBeInTheDocument();
    });
  });

  it('renders execution tab with agent claim data', async () => {
    const { fetchTask, fetchTaskClaims, fetchTaskHeartbeats, fetchTaskClarifications, fetchEvidence, fetchReviewRounds } = await import('@/lib/api');

    vi.mocked(fetchTask).mockResolvedValue({
      id: 'task-123',
      feature_id: 'feature-1',
      title: 'Test Task',
      description: 'Test description',
      status: 'in-progress',
      priority: 1,
      assignee_type: null,
      assignee_id: null,
      component_id: null,
      module_id: null,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    });

    vi.mocked(fetchTaskClaims).mockResolvedValue({
      items: [{
        id: 'claim-1',
        task_id: 'task-123',
        agent_id: 'code-quality-guard',
        state: 'claimed',
        claimed_at: '2024-01-01T00:05:00Z',
      }],
    });

    vi.mocked(fetchTaskHeartbeats).mockResolvedValue({
      items: [{
        id: 'heartbeat-1',
        claim_id: 'claim-1',
        progress_percent: 50,
        current_step: 'Reviewing code',
        next_step: 'Running tests',
        blockers: null,
        eta: null,
        created_at: '2024-01-01T00:10:00Z',
      }],
    });

    vi.mocked(fetchTaskClarifications).mockResolvedValue({ items: [] });
    vi.mocked(fetchEvidence).mockResolvedValue({ items: [] });
    vi.mocked(fetchReviewRounds).mockResolvedValue({ items: [] });

    render(
      <TaskDetailSheet taskId="task-123" onOpenChange={vi.fn()} />,
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(screen.getByText('Test Task')).toBeInTheDocument();
    });

    // Click on Execution tab
    const executionTab = screen.getByRole('tab', { name: /execution/i });
    executionTab.click();

    await waitFor(() => {
      expect(screen.getByText('code-quality-guard')).toBeInTheDocument();
      expect(screen.getByText('Reviewing code')).toBeInTheDocument();
      expect(screen.getByText('50%')).toBeInTheDocument();
    });
  });

  it('renders empty states when no data exists', async () => {
    const { fetchTask, fetchTaskClaims, fetchTaskHeartbeats, fetchTaskClarifications, fetchEvidence, fetchReviewRounds } = await import('@/lib/api');

    vi.mocked(fetchTask).mockResolvedValue({
      id: 'task-123',
      feature_id: 'feature-1',
      title: 'Test Task',
      description: 'Test description',
      status: 'in-progress',
      priority: 1,
      assignee_type: null,
      assignee_id: null,
      component_id: null,
      module_id: null,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    });

    vi.mocked(fetchTaskClaims).mockResolvedValue({ items: [] });
    vi.mocked(fetchTaskHeartbeats).mockResolvedValue({ items: [] });
    vi.mocked(fetchTaskClarifications).mockResolvedValue({ items: [] });
    vi.mocked(fetchEvidence).mockResolvedValue({ items: [] });
    vi.mocked(fetchReviewRounds).mockResolvedValue({ items: [] });

    render(
      <TaskDetailSheet taskId="task-123" onOpenChange={vi.fn()} />,
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(screen.getByText('Test Task')).toBeInTheDocument();
    });

    // Click on Execution tab
    const executionTab = screen.getByRole('tab', { name: /execution/i });
    executionTab.click();

    await waitFor(() => {
      expect(screen.getByText('No agent claims yet.')).toBeInTheDocument();
      expect(screen.getByText('No clarifications requested.')).toBeInTheDocument();
      expect(screen.getByText('No evidence attached yet.')).toBeInTheDocument();
      expect(screen.getByText('No reviews yet.')).toBeInTheDocument();
    });
  });
});
