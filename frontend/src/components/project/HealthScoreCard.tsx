import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Activity, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { fetchProjectHealth } from '@/lib/api';

function ScoreRing({ score }: { score: number }) {
  const radius = 40;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const color =
    score >= 80
      ? 'text-emerald-500'
      : score >= 50
        ? 'text-amber-500'
        : 'text-red-500';

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width="100" height="100" className="-rotate-90">
        <circle
          cx="50"
          cy="50"
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth="8"
          className="text-muted/30"
        />
        <circle
          cx="50"
          cy="50"
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth="8"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className={color}
        />
      </svg>
      <span className="absolute text-xl font-bold">{score}</span>
    </div>
  );
}

export function HealthScoreCard({ projectId }: { projectId: string }) {
  const { data: health, isLoading } = useQuery({
    queryKey: ['project-health', projectId],
    queryFn: () => fetchProjectHealth(projectId),
    enabled: !!projectId,
  });

  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="h-[100px] w-full animate-pulse rounded bg-muted" />
        </CardContent>
      </Card>
    );
  }

  const score = health?.score ?? 0;
  const issues = health?.breakdown ?? {};
  const totalIssues =
    issues.blocked +
    issues.stale_claims +
    issues.failed_dod +
    issues.open_clarifications +
    issues.rejected;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center gap-2 space-y-0 pb-2">
        <Activity className="h-4 w-4" />
        <CardTitle>Health Score</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-6">
          <ScoreRing score={score} />
          <div className="space-y-2 flex-1">
            <div className="flex items-center gap-2">
              {score >= 80 ? (
                <TrendingUp className="h-4 w-4 text-emerald-500" />
              ) : score >= 50 ? (
                <Minus className="h-4 w-4 text-amber-500" />
              ) : (
                <TrendingDown className="h-4 w-4 text-red-500" />
              )}
              <span className="text-sm font-medium">
                {score >= 80 ? 'Healthy' : score >= 50 ? 'Needs attention' : 'Critical'}
              </span>
            </div>
            {health?.top_issue && (
              <p className="text-xs text-muted-foreground">{health.top_issue}</p>
            )}
            {totalIssues > 0 && (
              <p className="text-xs text-muted-foreground">
                {totalIssues} open issue{totalIssues !== 1 ? 's' : ''}
              </p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
