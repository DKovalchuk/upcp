import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BoardView } from './BoardView';

vi.mock('@tanstack/react-query', async () => {
  const actual = await vi.importActual('@tanstack/react-query');
  return { ...actual, useQueries: vi.fn() };
});

vi.mock('@/hooks/use-tasks', () => ({
  useUpdateTask: vi.fn(),
}));

vi.mock('@/lib/api', () => ({
  fetchTasks: vi.fn(),
}));

vi.mock('@/lib/toast', () => ({
  showToast: { created: vi.fn(), updated: vi.fn(), error: vi.fn() },
}));

import { useQueries } from '@tanstack/react-query';
import { useUpdateTask } from '@/hooks/use-tasks';

const mockUseQueries = vi.mocked(useQueries);
const mockUseUpdateTask = vi.mocked(useUpdateTask);

const FEATURES = [
  { id: 'f1', project_id: 'p1', name: 'Auth', slug: 'auth', description: null, status: 'backlog', component_id: null, created_at: '', updated_at: '' },
  { id: 'f2', project_id: 'p1', name: 'Dashboard', slug: 'dashboard', description: null, status: 'in-progress', component_id: null, created_at: '', updated_at: '' },
];

const TASKS_F1 = [
  { id: 't1', feature_id: 'f1', title: 'Login', description: null, status: 'backlog', priority: 0, assignee_type: null, assignee_id: null, component_id: null, module_id: null, created_at: '', updated_at: '' },
  { id: 't2', feature_id: 'f1', title: 'Register', description: null, status: 'in-progress', priority: 1, assignee_type: null, assignee_id: null, component_id: null, module_id: null, created_at: '', updated_at: '' },
];

const TASKS_F2 = [
  { id: 't3', feature_id: 'f2', title: 'Stats', description: null, status: 'done', priority: 2, assignee_type: null, assignee_id: null, component_id: null, module_id: null, created_at: '', updated_at: '' },
];

function mockQueries(tasksByFeature: Record<string, any[]>) {
  mockUseQueries.mockImplementation(({ queries }: any) =>
    queries.map((q: any) => {
      const featureId = q.queryKey[1];
      const items = tasksByFeature[featureId] ?? [];
      return { data: { items, total: items.length, offset: 0, limit: 20 }, isLoading: false };
    })
  );
}

function renderBoard(
  props: Partial<React.ComponentProps<typeof BoardView>> = {}
) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const onSelectTask = vi.fn();
  return {
    onSelectTask,
    ...render(
      <QueryClientProvider client={qc}>
        <BoardView
          features={FEATURES}
          search=""
          onSelectTask={onSelectTask}
          {...props}
        />
      </QueryClientProvider>
    ),
  };
}

describe('BoardView', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseUpdateTask.mockReturnValue({ mutateAsync: vi.fn() } as any);
  });

  it('renders all four status columns', () => {
    mockQueries({ f1: [], f2: [] });
    renderBoard();
    expect(screen.getByText('Backlog')).toBeInTheDocument();
    expect(screen.getByText('In Progress')).toBeInTheDocument();
    expect(screen.getByText('Review')).toBeInTheDocument();
    expect(screen.getByText('Done')).toBeInTheDocument();
  });

  it('shows "No tasks" in empty columns', () => {
    mockQueries({ f1: [], f2: [] });
    renderBoard();
    const noTasks = screen.getAllByText('No tasks');
    expect(noTasks.length).toBe(4);
  });

  it('distributes tasks to correct columns', () => {
    mockQueries({ f1: TASKS_F1, f2: TASKS_F2 });
    renderBoard();
    expect(screen.getByText('Login')).toBeInTheDocument();
    expect(screen.getByText('Register')).toBeInTheDocument();
    expect(screen.getByText('Stats')).toBeInTheDocument();
  });

  it('shows feature name on task cards', () => {
    mockQueries({ f1: [TASKS_F1[0]], f2: [] });
    renderBoard();
    expect(screen.getByText('Auth')).toBeInTheDocument();
  });

  it('calls onSelectTask when clicking a task card', () => {
    mockQueries({ f1: [TASKS_F1[0]], f2: [] });
    const { onSelectTask } = renderBoard();
    fireEvent.click(screen.getByText('Login'));
    expect(onSelectTask).toHaveBeenCalledWith('t1');
  });

  it('filters tasks by search', () => {
    mockQueries({ f1: TASKS_F1, f2: [] });
    renderBoard({ search: 'Login' });
    expect(screen.getByText('Login')).toBeInTheDocument();
    expect(screen.queryByText('Register')).not.toBeInTheDocument();
  });

  it('shows column counts', () => {
    mockQueries({ f1: TASKS_F1, f2: TASKS_F2 });
    renderBoard();
    const counts = screen.getAllByText(/\(\d+\)/);
    expect(counts.length).toBe(4);
  });

  it('task cards have draggable attribute', () => {
    mockQueries({ f1: [TASKS_F1[0]], f2: [] });
    renderBoard();
    const card = screen.getByText('Login').closest('[data-draggable]');
    expect(card).toBeTruthy();
  });

  it('columns have droppable attribute', () => {
    mockQueries({ f1: [], f2: [] });
    renderBoard();
    const droppables = document.querySelectorAll('[data-droppable]');
    expect(droppables.length).toBe(4);
  });
});
