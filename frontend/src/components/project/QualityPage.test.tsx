import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { QualityPage } from './QualityPage';

vi.mock('@tanstack/react-router', () => ({
  useLocation: () => ({ pathname: '/projects/p1/quality' }),
}));

vi.mock('@/hooks/use-quality-stats', () => ({
  useQualityStats: vi.fn(),
}));

import { useQualityStats } from '@/hooks/use-quality-stats';
const mock = vi.mocked(useQualityStats);

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={qc}><QualityPage /></QueryClientProvider>);
}

describe('QualityPage', () => {
  beforeEach(() => vi.clearAllMocks());

  it('renders loading skeleton', () => {
    mock.mockReturnValue({ data: undefined, isLoading: true } as ReturnType<typeof useQualityStats>);
    const { container } = renderPage();
    expect(container.querySelectorAll('[data-slot="skeleton"]').length).toBeGreaterThan(0);
  });

  it('renders error state', () => {
    mock.mockReturnValue({ data: undefined, isLoading: false, error: new Error('fail') } as ReturnType<typeof useQualityStats>);
    renderPage();
    expect(screen.getByText('Failed to load quality stats')).toBeInTheDocument();
  });

  it('renders stats cards', () => {
    mock.mockReturnValue({
      data: { total_tasks: 10, tasks_with_ac: 7, total_ac: 20, passed_ac: 15, total_dod: 12, passed_dod: 10, pass_rate: 83.3 },
      isLoading: false, error: null,
    } as ReturnType<typeof useQualityStats>);
    renderPage();
    expect(screen.getByText('Quality')).toBeInTheDocument();
    expect(screen.getByText('10')).toBeInTheDocument();
    expect(screen.getByText('7')).toBeInTheDocument();
    // 75% appears in both stat card and progress section
    const p75 = screen.getAllByText('75%');
    expect(p75.length).toBeGreaterThanOrEqual(1);
  });

  it('renders progress bars', () => {
    mock.mockReturnValue({
      data: { total_tasks: 5, tasks_with_ac: 3, total_ac: 10, passed_ac: 8, total_dod: 6, passed_dod: 3, pass_rate: 50 },
      isLoading: false, error: null,
    } as ReturnType<typeof useQualityStats>);
    renderPage();
    expect(screen.getByText('Acceptance Criteria')).toBeInTheDocument();
    expect(screen.getByText('Definition of Done')).toBeInTheDocument();
    // 80% and 50% appear in stat cards and progress sections
    const p80 = screen.getAllByText('80%');
    expect(p80.length).toBeGreaterThanOrEqual(1);
    const p50 = screen.getAllByText('50%');
    expect(p50.length).toBeGreaterThanOrEqual(1);
  });
});
