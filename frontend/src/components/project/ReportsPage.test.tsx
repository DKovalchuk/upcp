import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReportsPage } from './ReportsPage';

vi.mock('@/hooks/use-project-id', () => ({
  useProjectId: () => 'project-1',
}));

vi.mock('@/hooks/use-reports', () => ({
  useReports: vi.fn(),
  useCreateReport: vi.fn(),
}));

vi.mock('@/lib/api', () => ({
  exportReportMarkdown: vi.fn(),
}));

import { useReports, useCreateReport } from '@/hooks/use-reports';
const mockUseReports = vi.mocked(useReports);
const mockUseCreateReport = vi.mocked(useCreateReport);

function renderPage() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  mockUseCreateReport.mockReturnValue({ mutateAsync: vi.fn() } as ReturnType<typeof useCreateReport>);
  return render(
    <QueryClientProvider client={qc}>
      <ReportsPage />
    </QueryClientProvider>,
  );
}

const makeReport = (id: string, createdAt: string, type = 'daily') => ({
  id,
  report_type: type,
  summary: `Report ${id}`,
  created_at: createdAt,
  updated_at: createdAt,
});

describe('ReportsPage', () => {
  beforeEach(() => vi.clearAllMocks());

  it('renders date range filter inputs', () => {
    mockUseReports.mockReturnValue({ data: { items: [], total: 0 }, isLoading: false, error: null } as ReturnType<typeof useReports>);
    renderPage();
    expect(screen.getByLabelText('Filter from date')).toBeInTheDocument();
    expect(screen.getByLabelText('Filter to date')).toBeInTheDocument();
  });

  it('filters reports by date range', () => {
    mockUseReports.mockReturnValue({
      data: {
        items: [
          makeReport('r1', '2026-07-01T10:00:00Z'),
          makeReport('r2', '2026-07-15T10:00:00Z'),
          makeReport('r3', '2026-08-01T10:00:00Z'),
        ],
        total: 3,
      },
      isLoading: false,
      error: null,
    } as ReturnType<typeof useReports>);
    renderPage();

    // All three reports should be visible initially
    expect(screen.getByText('Report r1')).toBeInTheDocument();
    expect(screen.getByText('Report r2')).toBeInTheDocument();
    expect(screen.getByText('Report r3')).toBeInTheDocument();

    // Filter from July 10 to July 20
    fireEvent.change(screen.getByLabelText('Filter from date'), { target: { value: '2026-07-10' } });
    fireEvent.change(screen.getByLabelText('Filter to date'), { target: { value: '2026-07-20' } });

    expect(screen.queryByText('Report r1')).not.toBeInTheDocument();
    expect(screen.getByText('Report r2')).toBeInTheDocument();
    expect(screen.queryByText('Report r3')).not.toBeInTheDocument();
  });

  it('shows no-reports-in-range message when filter excludes all', () => {
    mockUseReports.mockReturnValue({
      data: {
        items: [makeReport('r1', '2026-07-01T10:00:00Z')],
        total: 1,
      },
      isLoading: false,
      error: null,
    } as ReturnType<typeof useReports>);
    renderPage();

    fireEvent.change(screen.getByLabelText('Filter from date'), { target: { value: '2026-12-01' } });

    expect(screen.getByText('No reports in date range')).toBeInTheDocument();
  });

  it('shows empty state when no reports exist', () => {
    mockUseReports.mockReturnValue({ data: { items: [], total: 0 }, isLoading: false, error: null } as ReturnType<typeof useReports>);
    renderPage();
    expect(screen.getByText('No reports yet')).toBeInTheDocument();
  });

  it('renders Reports heading', () => {
    mockUseReports.mockReturnValue({ data: { items: [], total: 0 }, isLoading: false, error: null } as ReturnType<typeof useReports>);
    renderPage();
    expect(screen.getByText('Reports')).toBeInTheDocument();
  });

  it('renders loading state', () => {
    mockUseReports.mockReturnValue({ data: undefined, isLoading: true } as ReturnType<typeof useReports>);
    const { container } = renderPage();
    expect(container.querySelectorAll('[data-slot="skeleton"]').length).toBeGreaterThan(0);
  });
});
