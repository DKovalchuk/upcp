import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ProjectSelector } from './ProjectSelector';
import { mockSuccessQuery } from '@/test/helpers';

const routeState = vi.hoisted(() => ({
  search: {} as Record<string, string | undefined>,
}));
const mockNavigate = vi.fn();

vi.mock('@tanstack/react-router', () => ({
  useNavigate: () => mockNavigate,
  useSearch: () => routeState.search,
}));

vi.mock('@/hooks/use-projects', () => ({
  useProjects: vi.fn(),
}));

// The select UI primitive (Base UI) is mocked to its contract: value flow +
// onValueChange wiring — the same child-mocking pattern used in Dashboard.test.
// Base UI popups need pointer-event support unavailable in plain jsdom.
const selectState = vi.hoisted(() => ({
  onValueChange: undefined as ((value: string | null) => void) | undefined,
}));

vi.mock('@/components/ui/select', () => ({
  Select: ({
    value,
    onValueChange,
    children,
  }: {
    value?: string;
    onValueChange?: (value: string | null) => void;
    children?: React.ReactNode;
  }) => {
    selectState.onValueChange = onValueChange;
    return (
      <div data-testid="select-root" data-value={value}>
        {children}
      </div>
    );
  },
  SelectTrigger: ({ children }: { children?: React.ReactNode }) => (
    <div data-testid="select-trigger">{children}</div>
  ),
  SelectValue: ({ placeholder }: { placeholder?: string }) => (
    <span data-testid="select-value">{placeholder}</span>
  ),
  SelectContent: ({ children }: { children?: React.ReactNode }) => (
    <div data-testid="select-content">{children}</div>
  ),
  SelectItem: ({ value, children }: { value?: string; children?: React.ReactNode }) => (
    <button
      type="button"
      data-testid={`select-item-${value}`}
      onClick={() => selectState.onValueChange?.(value ?? null)}
    >
      {children}
    </button>
  ),
}));

import { useProjects } from '@/hooks/use-projects';

const mockUseProjects = vi.mocked(useProjects);

function makeProjects(count: number) {
  return Array.from({ length: count }, (_, i) => ({
    id: `p${i + 1}`,
    name: `Project ${i + 1}`,
    slug: `project-${i + 1}`,
    description: null,
    status: 'active',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  }));
}

function givenProjects(count: number) {
  mockUseProjects.mockReturnValue(
    mockSuccessQuery({ items: makeProjects(count), total: count }),
  );
}

function getSelectValue(): string | undefined {
  return document.querySelector('[data-testid="select-root"]')?.getAttribute('data-value') ?? undefined;
}

describe('ProjectSelector', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    routeState.search = {};
    selectState.onValueChange = undefined;
  });

  // ── B15: edge cases ─────────────────────────────

  it('hidden when 0 projects (B15.1)', () => {
    givenProjects(0);
    const { container } = render(<ProjectSelector />);
    expect(container.firstChild).toBeNull();
  });

  it('hidden when only 1 project (B15.2) — implementation hides at ≤1, no "All + 1" two-option state exists', () => {
    givenProjects(1);
    const { container } = render(<ProjectSelector />);
    expect(container.firstChild).toBeNull();
  });

  // ── B14: positive rows ──────────────────────────

  it('defaults to All Projects with no project_id in URL (B14.1)', () => {
    givenProjects(3);
    render(<ProjectSelector />);
    expect(getSelectValue()).toBe('all');
    expect(screen.getByTestId('select-value')).toHaveTextContent('All Projects');
  });

  it('lists all projects from API data plus All Projects (B14.2)', () => {
    givenProjects(3);
    render(<ProjectSelector />);
    expect(screen.getByTestId('select-item-all')).toHaveTextContent('All Projects');
    expect(screen.getByTestId('select-item-p1')).toHaveTextContent('Project 1');
    expect(screen.getByTestId('select-item-p3')).toHaveTextContent('Project 3');
  });

  it('selecting a project updates URL with ?project_id (B14.3)', () => {
    givenProjects(3);
    render(<ProjectSelector />);
    fireEvent.click(screen.getByTestId('select-item-p2'));
    expect(mockNavigate).toHaveBeenCalledWith({ search: { project_id: 'p2' } });
  });

  it('selecting All Projects clears project_id from URL (B14.4)', () => {
    givenProjects(3);
    render(<ProjectSelector />);
    fireEvent.click(screen.getByTestId('select-item-all'));
    expect(mockNavigate).toHaveBeenCalledWith({ search: {} });
  });

  it('URL with project_id preselects that project (B14.5)', () => {
    routeState.search = { project_id: 'p2' };
    givenProjects(3);
    render(<ProjectSelector />);
    expect(getSelectValue()).toBe('p2');
    expect(screen.getByTestId('select-item-p2')).toBeInTheDocument();
  });

  // ── B15: more edge cases ────────────────────────

  it('unknown project_id in URL does not crash; selector stays usable (B15.3)', () => {
    // Component passes the URL value through without validation (no explicit
    // fallback to "All"); backend treats unknown project ids as global scope.
    routeState.search = { project_id: 'missing-id' };
    givenProjects(3);
    render(<ProjectSelector />);
    expect(getSelectValue()).toBe('missing-id');
    expect(screen.getByTestId('select-item-all')).toBeInTheDocument();
    fireEvent.click(screen.getByTestId('select-item-all'));
    expect(mockNavigate).toHaveBeenCalledWith({ search: {} });
  });

  it('non-UUID project_id in URL does not crash; selector stays usable (B15.4)', () => {
    routeState.search = { project_id: 'not-a-uuid' };
    givenProjects(3);
    render(<ProjectSelector />);
    expect(getSelectValue()).toBe('not-a-uuid');
    expect(screen.getByTestId('select-item-p1')).toBeInTheDocument();
  });

  it('rapid selection changes navigate with each selection, ending on the last (B15.5)', () => {
    givenProjects(3);
    render(<ProjectSelector />);
    fireEvent.click(screen.getByTestId('select-item-p1'));
    fireEvent.click(screen.getByTestId('select-item-p3'));
    expect(mockNavigate).toHaveBeenCalledTimes(2);
    expect(mockNavigate).toHaveBeenLastCalledWith({ search: { project_id: 'p3' } });
  });

  it('project deleted while viewing → selector renders and drops the option (B15.6)', () => {
    routeState.search = { project_id: 'p1' };
    const remaining = makeProjects(3).slice(1); // p1 no longer exists
    mockUseProjects.mockReturnValue(
      mockSuccessQuery({ items: remaining, total: 2 }),
    );
    render(<ProjectSelector />);
    expect(document.querySelector('[data-testid="select-root"]')).toBeTruthy();
    expect(screen.queryByTestId('select-item-p1')).not.toBeInTheDocument();
    expect(screen.getByTestId('select-item-p2')).toBeInTheDocument();
  });
});
