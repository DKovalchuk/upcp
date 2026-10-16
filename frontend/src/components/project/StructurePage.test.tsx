import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { StructurePage } from './StructurePage';

vi.mock('@tanstack/react-router', async () => {
  const actual = await vi.importActual('@tanstack/react-router');
  return {
    ...actual,
    useLocation: () => ({ pathname: '/projects/proj-1/structure' }),
    // useFilters needs search state — no router store in tests
    useSearch: () => ({}),
    useNavigate: () => vi.fn(),
  };
});

vi.mock('@/hooks/use-components', () => ({
  useComponents: vi.fn(),
  useCreateComponent: vi.fn(),
  useDeleteComponent: vi.fn(),
}));

vi.mock('@/hooks/use-modules', () => ({
  useModules: vi.fn(),
  useCreateModule: vi.fn(),
  useDeleteModule: vi.fn(),
}));

vi.mock('@/lib/toast', () => ({
  showToast: { created: vi.fn(), deleted: vi.fn(), error: vi.fn() },
}));

import { useComponents, useCreateComponent, useDeleteComponent } from '@/hooks/use-components';
import { useModules, useCreateModule, useDeleteModule } from '@/hooks/use-modules';

const mockUseComponents = vi.mocked(useComponents);
const mockUseCreateComponent = vi.mocked(useCreateComponent);
const mockUseDeleteComponent = vi.mocked(useDeleteComponent);
const mockUseModules = vi.mocked(useModules);
const mockUseCreateModule = vi.mocked(useCreateModule);
const mockUseDeleteModule = vi.mocked(useDeleteModule);

function renderStructure() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <StructurePage />
    </QueryClientProvider>
  );
}

describe('StructurePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseCreateComponent.mockReturnValue({ mutateAsync: vi.fn() } as any);
    mockUseDeleteComponent.mockReturnValue({ mutateAsync: vi.fn() } as any);
    mockUseModules.mockReturnValue({ data: [], isLoading: false } as any);
    mockUseCreateModule.mockReturnValue({ mutateAsync: vi.fn() } as any);
    mockUseDeleteModule.mockReturnValue({ mutateAsync: vi.fn() } as any);
  });

  it('renders loading state', () => {
    mockUseComponents.mockReturnValue({ data: undefined, isLoading: true } as any);
    const { container } = renderStructure();
    expect(container.querySelectorAll('[data-slot="skeleton"]').length).toBeGreaterThan(0);
  });

  it('renders empty state when no components', () => {
    mockUseComponents.mockReturnValue({ data: [], isLoading: false } as any);
    renderStructure();
    expect(screen.getByText('No components yet')).toBeInTheDocument();
    expect(screen.getByText('Components represent the major parts of your project.')).toBeInTheDocument();
  });

  it('renders component cards', () => {
    mockUseComponents.mockReturnValue({
      data: [
        { id: 'c1', project_id: 'p1', name: 'Backend', slug: 'backend', description: 'API layer', status: 'active', created_at: '', updated_at: '' },
        { id: 'c2', project_id: 'p1', name: 'Frontend', slug: 'frontend', description: null, status: 'paused', created_at: '', updated_at: '' },
      ],
      isLoading: false,
    } as any);

    renderStructure();
    expect(screen.getByText('Backend')).toBeInTheDocument();
    expect(screen.getByText('API layer')).toBeInTheDocument();
    expect(screen.getByText('Frontend')).toBeInTheDocument();
    expect(screen.getByText('backend')).toBeInTheDocument();
  });

  it('shows Structure heading', () => {
    mockUseComponents.mockReturnValue({ data: [], isLoading: false } as any);
    renderStructure();
    expect(screen.getByText('Structure')).toBeInTheDocument();
  });

  it('renders create component button', () => {
    mockUseComponents.mockReturnValue({ data: [], isLoading: false } as any);
    renderStructure();
    const buttons = screen.getAllByRole('button');
    const hasComponentBtn = buttons.some((b) => b.textContent?.trim() === 'Component');
    expect(hasComponentBtn).toBe(true);
  });

  it('opens create component dialog on button click', async () => {
    mockUseComponents.mockReturnValue({ data: [], isLoading: false } as any);
    renderStructure();
    const buttons = screen.getAllByRole('button');
    const componentBtn = buttons.find((b) => b.textContent?.includes('Component'));
    fireEvent.click(componentBtn!);
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });
  });

  it('expands component to show modules section', () => {
    mockUseComponents.mockReturnValue({
      data: [
        { id: 'c1', project_id: 'p1', name: 'Backend', slug: 'backend', description: null, status: 'active', created_at: '', updated_at: '' },
      ],
      isLoading: false,
    } as any);
    mockUseModules.mockReturnValue({
      data: [
        { id: 'm1', component_id: 'c1', name: 'Auth', slug: 'auth', description: null, status: 'active', created_at: '', updated_at: '' },
      ],
      isLoading: false,
    } as any);

    renderStructure();
    // Click to expand
    fireEvent.click(screen.getByText('Backend'));
    expect(screen.getByText('Modules')).toBeInTheDocument();
    expect(screen.getByText('Auth')).toBeInTheDocument();
  });

  it('shows empty modules message when expanded but no modules', () => {
    mockUseComponents.mockReturnValue({
      data: [
        { id: 'c1', project_id: 'p1', name: 'Backend', slug: 'backend', description: null, status: 'active', created_at: '', updated_at: '' },
      ],
      isLoading: false,
    } as any);
    mockUseModules.mockReturnValue({ data: [], isLoading: false } as any);

    renderStructure();
    fireEvent.click(screen.getByText('Backend'));
    expect(screen.getByText('No modules in this component.')).toBeInTheDocument();
  });
});
