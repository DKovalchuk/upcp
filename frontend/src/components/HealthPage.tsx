import { useHealth } from '@/hooks/use-health';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { PageSkeleton } from '@/components/ui/PageSkeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { Activity, CheckCircle, XCircle } from 'lucide-react';
import type { HealthCheckResult } from '@/types/api';

function StatusCard({
  title,
  result,
  subtitle,
}: {
  title: string;
  result?: HealthCheckResult;
  subtitle: string;
}) {
  const isOk = result?.status === 'ok';

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {isOk ? (
          <CheckCircle className="h-4 w-4 text-emerald-500" />
        ) : (
          <XCircle className="h-4 w-4 text-red-500" />
        )}
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-2">
          <div className={`h-2.5 w-2.5 rounded-full ${isOk ? 'bg-emerald-500' : 'bg-red-500'}`} />
          <span className="text-sm">{isOk ? 'Connected' : 'Disconnected'}</span>
          {result?.latency_ms !== undefined && (
            <span className="text-xs text-muted-foreground">{result.latency_ms}ms</span>
          )}
        </div>
        <p className="text-xs text-muted-foreground mt-2">
          {isOk ? subtitle : result?.error ?? 'Unknown error'}
        </p>
      </CardContent>
    </Card>
  );
}

export function HealthPage() {
  const { data: health, isLoading, error } = useHealth();

  if (isLoading) return <PageSkeleton hasCards cardCount={4} />;
  if (error) return <ErrorState message="Failed to load health status" />;

  const isOk = health?.status === 'ok';

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Activity className="h-5 w-5" />
        <h1 className="text-2xl font-bold tracking-tight">System Health</h1>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Backend API</CardTitle>
            {isOk ? (
              <CheckCircle className="h-4 w-4 text-emerald-500" />
            ) : (
              <XCircle className="h-4 w-4 text-red-500" />
            )}
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <div className={`h-2.5 w-2.5 rounded-full ${isOk ? 'bg-emerald-500' : 'bg-red-500'}`} />
              <span className="text-sm">{isOk ? 'Operational' : 'Down'}</span>
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              {health?.service ?? 'unknown'}
            </p>
          </CardContent>
        </Card>

        <StatusCard
          title="Database"
          result={health?.db}
          subtitle="PostgreSQL via backend"
        />

        <StatusCard
          title="Redis"
          result={health?.redis}
          subtitle="Cache & sessions"
        />

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Auto-refresh</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Health status refreshes every 30 seconds.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
