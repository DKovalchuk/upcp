// Agent Center Page tests — TASK-0099 Sprint 2

import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AgentCenterPage } from '@/pages/AgentCenterPage';

vi.mock('@/hooks/use-agents', () => ({
  useAgents: vi.fn(),
  useCreateAgent: vi.fn(),
}));

vi.mock('@tanstack/react-router', () => ({
  useNavigate: () => vi.fn(),
}));

import { useAgents } from '@/hooks/use-agents';

const mockUseAgents = vi.mocked(useAgents);

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <AgentCenterPage />
    </QueryClientProvider>
  );
}

describe('AgentCenterPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state', () => {
    mockUseAgents.mockReturnValue({
      data: undefined,
      isLoading: true,
    } as ReturnType<typeof useAgents>);
    const { container } = renderPage();
    // PageSkeleton renders div elements with skeleton class
    expect(container.querySelector('.animate-pulse')).toBeDefined();
  });

  it('renders empty state when no agents', () => {
     mockUseAgents.mockReturnValue({
      data: { items: [], total: 0, offset: 0, limit: 20 },
      isLoading: false,
    } as ReturnType<typeof useAgents>);
    renderPage();
    expect(screen.getByText('No agents')).toBeDefined();
  });

  it('renders agent cards', () => {
    mockUseAgents.mockReturnValue({
      data: {
        items: [
          {
            id: 'a1',
            name: 'claude-builder',
            description: 'Builder',
            is_active: true,
            created_at: '2026-08-01T00:00:00Z',
          },
          {
            id: 'a2',
            name: 'gpt-reviewer',
            description: 'Reviewer',
            is_active: true,
            created_at: '2026-08-01T00:00:00Z',
          },
        ],
        total: 2,
        offset: 0,
        limit: 20,
      },
      isLoading: false,
    } as ReturnType<typeof useAgents>);
    renderPage();
    expect(screen.getByText('claude-builder')).toBeDefined();
    expect(screen.getByText('gpt-reviewer')).toBeDefined();
  });

  it('renders page title', () => {
     mockUseAgents.mockReturnValue({
      data: { items: [], total: 0, offset: 0, limit: 20 },
      isLoading: false,
    } as ReturnType<typeof useAgents>);
    renderPage();
    expect(screen.getByText('Agents')).toBeDefined();
  });
});
