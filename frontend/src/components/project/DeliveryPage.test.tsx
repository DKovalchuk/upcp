import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { DeliveryPage } from './DeliveryPage';

vi.mock('@tanstack/react-router', async () => {
  const actual = await vi.importActual('@tanstack/react-router');
  return {
    ...actual,
    useLocation: () => ({ pathname: '/projects/proj-1/delivery' }),
  };
});

vi.mock('@/hooks/use-features', () => ({
  useFeatures: vi.fn(),
  useCreateFeature: vi.fn(),
  useDeleteFeature: vi.fn(),
}));

vi.mock('@/hooks/use-tasks', () => ({
  useTasks: vi.fn(),
  useTask: vi.fn(() => ({ data: null, isLoading: false })),
  useCreateTask: vi.fn(),
  useUpdateTask: vi.fn(),
  useDeleteTask: vi.fn(),
}));

vi.mock('@/hooks/use-quality', () => ({
  useAcceptanceCriteria: vi.fn(() => ({ data: [] })),
  useDoDItems: vi.fn(() => ({ data: [] })),
  useCreateAcceptanceCriterion: vi.fn(() => ({ mutateAsync: vi.fn() })),
  useCreateDoDItem: vi.fn(() => ({ mutateAsync: vi.fn() })),
  useSubmitReviewVerdict: vi.fn(() => ({ mutateAsync: vi.fn() })),
}));

vi.mock('@/hooks/use-subtasks', () => ({
  useSubtasks: vi.fn(() => ({ data: [] })),
  useCreateSubtask: vi.fn(() => ({ mutateAsync: vi.fn() })),
}));

vi.mock('@/lib/toast', () => ({
  showToast: { created: vi.fn(), updated: vi.fn(), deleted: vi.fn(), error: vi.fn(), mutationError: vi.fn(), success: vi.fn(), info: vi.fn() },
}));

import { useFeatures, useCreateFeature, useDeleteFeature } from '@/hooks/use-features';
import { useTasks, useCreateTask } from '@/hooks/use-tasks';

const mockUseFeatures = vi.mocked(useFeatures);
const mockUseCreateFeature = vi.mocked(useCreateFeature);
const mockUseDeleteFeature = vi.mocked(useDeleteFeature);
const mockUseTasks = vi.mocked(useTasks);
const mockUseCreateTask = vi.mocked(useCreateTask);

function renderDelivery() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <DeliveryPage />
    </QueryClientProvider>
  );
}

describe('DeliveryPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseCreateFeature.mockReturnValue({ mutateAsync: vi.fn() } as any);
    mockUseDeleteFeature.mockReturnValue({ mutateAsync: vi.fn() } as any);
    mockUseCreateTask.mockReturnValue({ mutateAsync: vi.fn() } as any);
    mockUseTasks.mockReturnValue({ data: [], isLoading: false } as any);
  });

  it('renders loading state', () => {
    mockUseFeatures.mockReturnValue({ data: undefined, isLoading: true } as any);
    const { container } = renderDelivery();
    expect(container.querySelectorAll('[data-slot="skeleton"]').length).toBeGreaterThan(0);
  });

  it('renders empty state when no features', () => {
    mockUseFeatures.mockReturnValue({ data: { items: [], total: 0, offset: 0, limit: 20 }, isLoading: false } as any);
    renderDelivery();
    expect(screen.getByText('No features yet')).toBeInTheDocument();
  });

  it('renders Delivery heading', () => {
    mockUseFeatures.mockReturnValue({ data: { items: [], total: 0, offset: 0, limit: 20 }, isLoading: false } as any);
    renderDelivery();
    expect(screen.getByRole('heading', { name: 'Delivery' })).toBeInTheDocument();
  });

  it('renders create feature button in header', () => {
    mockUseFeatures.mockReturnValue({ data: { items: [], total: 0, offset: 0, limit: 20 }, isLoading: false } as any);
    renderDelivery();
    const buttons = screen.getAllByRole('button');
    const featureBtn = buttons.find((b) => b.textContent?.trim() === 'Feature');
    expect(featureBtn).toBeInTheDocument();
  });

  it('shows task count per feature', () => {
    mockUseFeatures.mockReturnValue({
      data: {
        items: [
          { id: 'f1', project_id: 'p1', name: 'Auth', slug: 'auth', description: null, status: 'backlog', component_id: null, created_at: '', updated_at: '' },
          { id: 'f2', project_id: 'p1', name: 'Dashboard', slug: 'dashboard', description: null, status: 'in-progress', component_id: null, created_at: '', updated_at: '' },
        ],
        total: 2, offset: 0, limit: 20,
      },
      isLoading: false,
    } as any);

    renderDelivery();
    expect(screen.getByText('Auth')).toBeInTheDocument();
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    // Both features show (0 tasks) when collapsed
    const taskCounts = screen.getAllByText('(0 tasks)');
    expect(taskCounts.length).toBe(2);
  });

  it('expands feature to show tasks', () => {
    mockUseFeatures.mockReturnValue({
      data: {
        items: [
          { id: 'f1', project_id: 'p1', name: 'Auth', slug: 'auth', description: null, status: 'backlog', component_id: null, created_at: '', updated_at: '' },
        ],
        total: 1, offset: 0, limit: 20,
      },
      isLoading: false,
    } as any);
    mockUseTasks.mockReturnValue({
      data: {
        items: [
          { id: 't1', feature_id: 'f1', title: 'Login form', description: null, status: 'backlog', priority: 1, assignee_type: null, assignee_id: null, component_id: null, module_id: null, created_at: '2026-01-01T00:00:00Z', updated_at: '2026-07-24T00:00:00Z' },
        ],
        total: 1, offset: 0, limit: 20,
      },
      isLoading: false,
    } as any);

    renderDelivery();
    fireEvent.click(screen.getByText('Auth'));
    expect(screen.getByText('Tasks')).toBeInTheDocument();
    expect(screen.getByText('Login form')).toBeInTheDocument();
  });

  it('opens create feature dialog', async () => {
    mockUseFeatures.mockReturnValue({ data: { items: [], total: 0, offset: 0, limit: 20 }, isLoading: false } as any);
    renderDelivery();
    const buttons = screen.getAllByRole('button');
    const featureBtn = buttons.find((b) => b.textContent?.trim() === 'Feature');
    fireEvent.click(featureBtn!);
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });
  });

  it('shows search input', () => {
    mockUseFeatures.mockReturnValue({ data: { items: [], total: 0, offset: 0, limit: 20 }, isLoading: false } as any);
    renderDelivery();
    expect(screen.getByPlaceholderText('Filter tasks...')).toBeInTheDocument();
  });

  it('filters tasks by search', () => {
    mockUseFeatures.mockReturnValue({
      data: {
        items: [
          { id: 'f1', project_id: 'p1', name: 'Auth', slug: 'auth', description: null, status: 'backlog', component_id: null, created_at: '', updated_at: '' },
        ],
        total: 1, offset: 0, limit: 20,
      },
      isLoading: false,
    } as any);
    mockUseTasks.mockReturnValue({
      data: {
        items: [
          { id: 't1', feature_id: 'f1', title: 'Login form', description: null, status: 'backlog', priority: 0, assignee_type: null, assignee_id: null, component_id: null, module_id: null, created_at: '', updated_at: '' },
          { id: 't2', feature_id: 'f1', title: 'Register form', description: null, status: 'backlog', priority: 1, assignee_type: null, assignee_id: null, component_id: null, module_id: null, created_at: '', updated_at: '' },
        ],
        total: 2, offset: 0, limit: 20,
      },
      isLoading: false,
    } as any);

    renderDelivery();
    fireEvent.click(screen.getByText('Auth'));

    // Both visible initially
    expect(screen.getByText('Login form')).toBeInTheDocument();
    expect(screen.getByText('Register form')).toBeInTheDocument();

    // Search for "login" - filter is client-side via title match
    fireEvent.change(screen.getByPlaceholderText('Filter tasks...'), {
      target: { value: 'Login' },
    });

    // Login form should still be visible
    expect(screen.getByText('Login form')).toBeInTheDocument();
  });
});
