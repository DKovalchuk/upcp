import { useLocation } from '@tanstack/react-router';
import { useMemo, useState } from 'react';
import { useReports, useCreateReport } from '@/hooks/use-reports';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { PageSkeleton } from '@/components/ui/PageSkeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { EmptyState } from '@/components/ui/EmptyState';
import { BarChart3, Plus, FileText, Download } from 'lucide-react';
import { showToast } from '@/lib/toast';
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
  const location = useLocation();
  const projectId = useMemo(() => {
    const match = location.pathname.match(/^\/projects\/([^/]+)/);
    return match?.[1] ?? '';
  }, [location.pathname]);

  const { data: reports, isLoading, error } = useReports(projectId);
  const createReport = useCreateReport();
  const [generating, setGenerating] = useState(false);

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
      const res = await fetch(`/api/v1/reports/${reportId}/markdown`);
      const data = await res.json();
      const blob = new Blob([data.markdown], { type: 'text/markdown' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `report-${reportId.slice(0, 8)}.md`;
      a.click();
      URL.revokeObjectURL(url);
      showToast.success('Report exported');
    } catch {
      showToast.mutationError('export', 'report');
    }
  };

  const items = reports ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BarChart3 className="h-5 w-5" />
          <h2 className="text-lg font-semibold">Reports</h2>
        </div>
        <Button size="sm" onClick={handleGenerate} disabled={generating}>
          <Plus className="mr-2 h-4 w-4" />
          {generating ? 'Generating...' : 'Daily Report'}
        </Button>
      </div>

      {!items.length ? (
        <EmptyState
          icon={FileText}
          title="No reports yet"
          description="Generate your first daily report to see project status."
          action={{ label: 'Generate Report', onClick: handleGenerate }}
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
                {items.map((report: Report) => (
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
                        className="h-7 w-7"
                        onClick={() => handleExportMarkdown(report.id)}
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
    </div>
  );
}
