import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ProjectOverview } from '../ProjectOverview';

vi.mock('@/lib/api', () => ({
  fetchProjectHealth: vi.fn(),
  fetchProjectTasks: vi.fn(),
}));

vi.mock('@/lib/api/audit', () => ({
  fetchAuditEvents: vi.fn(),
}));

vi.mock('@/lib/format', () => ({
  formatRelativeTime: vi.fn(() => '1 hour ago'),
}));

import { fetchProjectHealth, fetchProjectTasks } from '@/lib/api';
import { fetchAuditEvents } from '@/lib/api/audit';

const mockHealth = vi.mocked(fetchProjectHealth);
const mockTasks = vi.mocked(fetchProjectTasks);
const mockAudit = vi.mocked(fetchAuditEvents);

const PROJECT = {
  id: 'p1',
  name: 'Test Project',
  slug: 'test-project',
  description: 'A test project',
  status: 'active',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-08-12T00:00:00Z',
};

const HEALTH_OK = { score: 85, breakdown: { blocked: 0, stale_claims: 0, failed_dod: 0, open_clarifications: 0, rejected: 0 }, top_issue: '' };
const HEALTH_CRITICAL = { score: 20, breakdown: { blocked: 3, stale_claims: 2, failed_dod: 1, open_clarifications: 0, rejected: 0 }, top_issue: '3 blocked tasks' };

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={qc}>
      <ProjectOverview project={PROJECT} />
    </QueryClientProvider>
  );
}

describe('ProjectOverview', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockHealth.mockResolvedValue(HEALTH_OK);
    mockTasks.mockResolvedValue({ items: [], total: 0 });
    mockAudit.mockResolvedValue({ items: [], total: 0 });
  });

  it('renders project details', async () => {
    const { findByText } = renderPage();
    expect(await findByText('Test Project')).toBeInTheDocument();
    expect(screen.getByText('test-project')).toBeInTheDocument();
  });

  it('renders health score card', async () => {
    const { findByText } = renderPage();
    expect(await findByText('Health Score')).toBeInTheDocument();
    expect(screen.getByText('85')).toBeInTheDocument();
    expect(screen.getByText('Healthy')).toBeInTheDocument();
  });

  it('renders task distribution chart', async () => {
    mockTasks.mockResolvedValue({
      items: [
        { id: 't1', status: 'done', title: 'Task 1' },
        { id: 't2', status: 'in-progress', title: 'Task 2' },
        { id: 't3', status: 'backlog', title: 'Task 3' },
      ],
      total: 3,
    });
    const { findByText } = renderPage();
    expect(await findByText('Task Distribution')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('renders velocity sparkline', async () => {
    const { findByText } = renderPage();
    expect(await findByText('Velocity (8 weeks)')).toBeInTheDocument();
  });

  it('renders recent activity', async () => {
    mockAudit.mockResolvedValue({
      items: [
        { id: 'a1', event_type: 'task.created', entity_type: 'task', entity_id: 't1', actor_type: 'agent', actor_id: 'agent-1', payload: null, note: 'Created task', timestamp: '2026-08-12T10:00:00Z' },
      ],
      total: 1,
    });
    const { findByText } = renderPage();
    expect(await findByText('Recent Activity')).toBeInTheDocument();
    expect(screen.getByText('task.created')).toBeInTheDocument();
  });

  it('shows no tasks message when empty', async () => {
    const { findByText } = renderPage();
    expect(await findByText('No tasks yet')).toBeInTheDocument();
  });

  it('shows critical health for low score', async () => {
    mockHealth.mockResolvedValue(HEALTH_CRITICAL);
    const { findByText } = renderPage();
    expect(await findByText('20')).toBeInTheDocument();
    expect(screen.getByText('Critical')).toBeInTheDocument();
  });

  it('has no emoji in content', async () => {
    const { container } = renderPage();
    await screen.findByText('Health Score');
    const text = container.textContent || '';
    const emojiRegex = /[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F1E0}-\u{1F1FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/u;
    expect(emojiRegex.test(text)).toBe(false);
  });
});
