import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { GitIntegrationPage } from './GitIntegrationPage';

vi.mock('@tanstack/react-router', () => ({
  useLocation: () => ({ pathname: '/projects/p1/git' }),
}));

vi.mock('@/hooks/use-git', () => ({
  useGitProviders: vi.fn(),
  useCreateGitProvider: vi.fn(),
  useDeleteGitProvider: vi.fn(),
  useGitBranches: vi.fn(),
  useGitCommits: vi.fn(),
}));

import {
  useGitProviders,
  useGitBranches,
  useGitCommits,
} from '@/hooks/use-git';

const mockUseGitProviders = vi.mocked(useGitProviders);
const mockUseGitBranches = vi.mocked(useGitBranches);
const mockUseGitCommits = vi.mocked(useGitCommits);

const PROVIDERS = [
  { id: 'gp1', name: 'local', provider_type: 'local', url: '/tmp/repo', status: 'active' },
];

const BRANCHES = [
  { id: 'b1', name: 'main', last_commit_sha: 'abc123', is_default: true },
  { id: 'b2', name: 'feature/x', last_commit_sha: 'def456', is_default: false },
];

const COMMITS = [
  { id: 'c1', sha: 'abc123', message: 'Initial commit', author: 'dev', committed_at: '2026-07-24T10:00:00Z' },
];

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <GitIntegrationPage />
    </QueryClientProvider>
  );
}

describe('GitIntegrationPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseGitProviders.mockReturnValue({ data: PROVIDERS, isLoading: false } as any);
    mockUseGitBranches.mockReturnValue({ data: BRANCHES, isLoading: false } as any);
    mockUseGitCommits.mockReturnValue({ data: COMMITS, isLoading: false } as any);
  });

  it('renders Git Integration heading', () => {
    renderPage();
    expect(screen.getByText('Git Integration')).toBeInTheDocument();
  });

  it('shows provider name', () => {
    renderPage();
    expect(screen.getAllByText('local').length).toBeGreaterThanOrEqual(1);
  });

  it('shows branches', () => {
    renderPage();
    expect(screen.getByText('main')).toBeInTheDocument();
    expect(screen.getByText('feature/x')).toBeInTheDocument();
  });

  it('shows commits', () => {
    renderPage();
    expect(screen.getByText('Initial commit')).toBeInTheDocument();
  });

  it('shows default branch indicator', () => {
    renderPage();
    expect(screen.getByText('default')).toBeInTheDocument();
  });
});
