import { useState, useMemo } from 'react';
import { useProjectId } from '@/hooks/use-project-id';
import { useReports, useCreateReport } from '@/hooks/use-reports';
import { useUrlPagination } from '@/hooks/use-url-pagination';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { PageSkeleton } from '@/components/ui/PageSkeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { EmptyState } from '@/components/ui/EmptyState';
import { DataTablePagination } from '@/components/ui/DataTablePagination';
import { BarChart3, Plus, FileText, Download, Calendar } from 'lucide-react';
import { showToast } from '@/lib/toast';
import { exportReportMarkdown } from '@/lib/api';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import type { Report } from '@/types/report';

export function ReportsPage() {
  const projectId = useProjectId();

  const { offset, limit, setOffset, setPageSize } = useUrlPagination(20);
  const { data, isLoading, error } = useReports(projectId, { offset, limit });
  const reports = useMemo(() => data?.items ?? [], [data]);
  const total = data?.total ?? 0;
  const createReport = useCreateReport();
  const [generating, setGenerating] = useState(false);
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  const filteredReports = useMemo(() => {
    if (!dateFrom && !dateTo) return reports;
    return reports.filter((r) => {
      const d = new Date(r.created_at);
      if (dateFrom && d < new Date(dateFrom)) return false;
      if (dateTo) {
        const to = new Date(dateTo);
        to.setHours(23, 59, 59, 999);
        if (d > to) return false;
      }
      return true;
    });
  }, [reports, dateFrom, dateTo]);

  if (!projectId) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-2">
          <BarChart3 className="h-5 w-5" />
          <h2 className="text-lg font-semibold">Reports</h2>
        </div>
        <EmptyState
          icon={FileText}
          title="Select a project"
          description="Navigate to a project to view and generate reports."
          action={{ label: 'Go to Projects', onClick: () => window.location.assign('/projects') }}
        />
      </div>
    );
  }

  if (isLoading) return <PageSkeleton rows={5} />;
  if (error) return <ErrorState message="Failed to load reports" />;

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      await createReport.mutateAsync({
        projectId,
        data: { report_type: 'daily' },
      });
      showToast.created('Report');
    } catch {
      showToast.mutationError('generate', 'report');
    } finally {
      setGenerating(false);
    }
  };

  const handleExportMarkdown = async (reportId: string) => {
    try {
      const data = await exportReportMarkdown(reportId);
      const blob = new Blob([data.markdown], { type: 'text/markdown' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `report-${reportId.slice(0, 8)}.md`;
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 100);
      showToast.success('Report exported');
    } catch {
      showToast.mutationError('export', 'report');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BarChart3 className="h-5 w-5" />
          <h2 className="text-lg font-semibold">Reports</h2>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Calendar className="h-4 w-4" />
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="h-9 rounded-md border bg-transparent px-2 text-sm"
              aria-label="Filter from date"
            />
            <span>—</span>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="h-9 rounded-md border bg-transparent px-2 text-sm"
              aria-label="Filter to date"
            />
          </div>
          <Button size="sm" onClick={handleGenerate} disabled={generating}>
            <Plus className="mr-2 h-4 w-4" />
            {generating ? 'Generating...' : 'Daily Report'}
          </Button>
        </div>
      </div>

      {!filteredReports.length ? (
        <EmptyState
          icon={FileText}
          title={reports.length ? 'No reports in date range' : 'No reports yet'}
          description={reports.length ? 'Try adjusting the date filters.' : 'Generate your first daily report to see project status.'}
          action={reports.length ? undefined : { label: 'Generate Report', onClick: handleGenerate }}
        />
      ) : (
        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Type</TableHead>
                  <TableHead>Summary</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="w-[100px]" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredReports.map((report: Report) => (
                  <TableRow key={report.id}>
                    <TableCell>
                      <StatusBadge status={report.report_type} />
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground max-w-[300px] truncate">
                      {report.summary ?? 'No summary'}
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {new Date(report.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="min-h-[44px] min-w-[44px]"
                        onClick={() => handleExportMarkdown(report.id)}
                        aria-label="Export report"
                      >
                        <Download className="h-3.5 w-3.5" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
      {total > limit && (
        <DataTablePagination
          offset={offset}
          limit={limit}
          total={total}
          onPageChange={setOffset}
          onPageSizeChange={setPageSize}
        />
      )}
    </div>
  );
}
