import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BoardView } from './BoardView';

vi.mock('@tanstack/react-query', async () => {
  const actual = await vi.importActual('@tanstack/react-query');
  return { ...actual, useQuery: vi.fn() };
});

vi.mock('@/hooks/use-tasks', () => ({
  useUpdateTask: vi.fn(),
}));

vi.mock('@/lib/api', () => ({
  fetchProjectTasks: vi.fn(),
}));

vi.mock('@/lib/toast', () => ({
  showToast: { created: vi.fn(), updated: vi.fn(), error: vi.fn() },
}));

import { useQuery } from '@tanstack/react-query';
import { useUpdateTask } from '@/hooks/use-tasks';

const mockUseQuery = vi.mocked(useQuery);
const mockUseUpdateTask = vi.mocked(useUpdateTask);

const ALL_TASKS = [
  { id: 't1', feature_id: 'f1', title: 'Login', description: null, status: 'backlog', priority: 0, assignee_type: null, assignee_id: null, component_id: null, module_id: null, created_at: '', updated_at: '' },
  { id: 't2', feature_id: 'f1', title: 'Register', description: null, status: 'in-progress', priority: 1, assignee_type: null, assignee_id: null, component_id: null, module_id: null, created_at: '', updated_at: '' },
  { id: 't3', feature_id: 'f2', title: 'Stats', description: null, status: 'done', priority: 2, assignee_type: null, assignee_id: null, component_id: null, module_id: null, created_at: '', updated_at: '' },
];

const FEATURES = [
  { id: 'f1', project_id: 'p1', name: 'Auth', slug: 'auth', description: null, status: 'backlog', component_id: null, created_at: '', updated_at: '' },
  { id: 'f2', project_id: 'p1', name: 'Dashboard', slug: 'dashboard', description: null, status: 'in-progress', component_id: null, created_at: '', updated_at: '' },
];

function mockQuery(tasks: any[]) {
  mockUseQuery.mockReturnValue({
    data: { items: tasks, total: tasks.length, offset: 0, limit: 100 },
    isLoading: false,
  } as any);
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
          projectId="p1"
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
    mockQuery([]);
    renderBoard();
    expect(screen.getByText('Backlog')).toBeInTheDocument();
    expect(screen.getByText('In Progress')).toBeInTheDocument();
    expect(screen.getByText('Review')).toBeInTheDocument();
    expect(screen.getByText('Done')).toBeInTheDocument();
  });

  it('shows "No tasks" in empty columns', () => {
    mockQuery([]);
    renderBoard();
    const noTasks = screen.getAllByText('No tasks');
    expect(noTasks.length).toBe(4);
  });

  it('distributes tasks to correct columns', () => {
    mockQuery(ALL_TASKS);
    renderBoard();
    expect(screen.getByText('Login')).toBeInTheDocument();
    expect(screen.getByText('Register')).toBeInTheDocument();
    expect(screen.getByText('Stats')).toBeInTheDocument();
  });

  it('shows feature name on task cards', () => {
    mockQuery([ALL_TASKS[0]]);
    renderBoard();
    expect(screen.getByText('Auth')).toBeInTheDocument();
  });

  it('calls onSelectTask when clicking a task card', () => {
    mockQuery([ALL_TASKS[0]]);
    const { onSelectTask } = renderBoard();
    fireEvent.click(screen.getByText('Login'));
    expect(onSelectTask).toHaveBeenCalledWith('t1');
  });

  it('filters tasks by search', () => {
    mockQuery(ALL_TASKS);
    renderBoard({ search: 'Login' });
    expect(screen.getByText('Login')).toBeInTheDocument();
    expect(screen.queryByText('Register')).not.toBeInTheDocument();
  });

  it('shows column counts', () => {
    mockQuery(ALL_TASKS);
    renderBoard();
    const counts = screen.getAllByText(/\(\d+\)/);
    expect(counts.length).toBe(4);
  });

  it('task cards have draggable attribute', () => {
    mockQuery([ALL_TASKS[0]]);
    renderBoard();
    const card = screen.getByText('Login').closest('[data-draggable]');
    expect(card).toBeTruthy();
  });

  it('columns have droppable attribute', () => {
    mockQuery([]);
    renderBoard();
    const droppables = document.querySelectorAll('[data-droppable]');
    expect(droppables.length).toBe(4);
  });

  it('task cards are keyboard focusable (tabIndex=0)', () => {
    mockQuery([ALL_TASKS[0]]);
    renderBoard();
    const card = screen.getByText('Login').closest('[data-draggable]');
    expect(card).toHaveAttribute('tabindex', '0');
  });

  it('task cards expose draggable ARIA semantics', () => {
    mockQuery([ALL_TASKS[0]]);
    renderBoard();
    const card = screen.getByText('Login').closest('[data-draggable]');
    expect(card).toHaveAttribute('aria-roledescription', 'draggable');
  });

  it('Enter on a task card starts a keyboard drag (KeyboardSensor)', async () => {
    mockQuery([ALL_TASKS[0]]);
    renderBoard();
    const card = screen.getByText('Login').closest('[data-draggable]');
    fireEvent.keyDown(card!, { key: 'Enter', code: 'Enter' });
    // drag start renders the active task a second time via DragOverlay
    await waitFor(() => {
      expect(screen.getAllByText('Login').length).toBeGreaterThan(1);
    });
  });
});
