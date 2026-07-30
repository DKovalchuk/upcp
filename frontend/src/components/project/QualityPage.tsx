import { useProjectId } from '@/hooks/use-project-id';
import { useQualityStats } from '@/hooks/use-quality-stats';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { PageSkeleton } from '@/components/ui/PageSkeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { Progress } from '@/components/ui/progress';
import { ShieldCheck } from 'lucide-react';

function StatCard({ label, value, sub }: { label: string; value: number | string; sub?: string }) {
  return (
    <Card>
      <CardContent className="p-4">
        <p className="text-sm text-muted-foreground">{label}</p>
        <p className="text-2xl font-bold">{value}</p>
        {sub && <p className="text-xs text-muted-foreground mt-1">{sub}</p>}
      </CardContent>
    </Card>
  );
}

export function QualityPage() {
  const projectId = useProjectId();

  const { data: stats, isLoading, error } = useQualityStats(projectId);

  if (isLoading) return <PageSkeleton hasCards cardCount={4} rows={5} />;
  if (error) return <ErrorState message="Failed to load quality stats" />;
  if (!stats) return null;

  const acRate = stats.total_ac > 0 ? Math.round((stats.passed_ac / stats.total_ac) * 100) : 0;
  const dodRate = stats.total_dod > 0 ? Math.round((stats.passed_dod / stats.total_dod) * 100) : 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <ShieldCheck className="h-5 w-5" />
        <h2 className="text-lg font-semibold">Quality</h2>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Total Tasks" value={stats.total_tasks} />
        <StatCard label="Tasks with AC" value={stats.tasks_with_ac} sub={`${stats.total_tasks > 0 ? Math.round((stats.tasks_with_ac / stats.total_tasks) * 100) : 0}% of tasks`} />
        <StatCard label="AC Pass Rate" value={`${acRate}%`} sub={`${stats.passed_ac}/${stats.total_ac} passed`} />
        <StatCard label="DoD Pass Rate" value={`${dodRate}%`} sub={`${stats.passed_dod}/${stats.total_dod} passed`} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Completion Progress</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span>Acceptance Criteria</span>
              <span className="text-muted-foreground">{acRate}%</span>
            </div>
            <Progress value={acRate} />
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span>Definition of Done</span>
              <span className="text-muted-foreground">{dodRate}%</span>
            </div>
            <Progress value={dodRate} />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Quality Gate</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Tasks can only be completed when all DoD items are marked as passed.
            Currently {stats.total_tasks - stats.tasks_with_ac} tasks have no acceptance criteria.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
