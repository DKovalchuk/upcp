import { Link } from '@tanstack/react-router';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { PortfolioProject } from '@/types/dashboard';

function healthBarColor(score: number): string {
  if (score >= 80) return 'bg-emerald-500';
  if (score >= 50) return 'bg-amber-500';
  return 'bg-red-500';
}

export function PortfolioTable({
  projects,
  isLoading,
}: {
  projects?: PortfolioProject[];
  isLoading?: boolean;
}) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Portfolio</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-10 animate-pulse rounded bg-muted" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!projects || projects.length <= 1) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Portfolio</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-muted-foreground">
                <th className="pb-2 font-medium">Project</th>
                <th className="pb-2 font-medium">Health</th>
                <th className="pb-2 font-medium">Tasks</th>
                <th className="pb-2 font-medium hidden sm:table-cell">Top Issue</th>
              </tr>
            </thead>
            <tbody>
              {projects.map((p) => (
                <tr key={p.id} className="border-b last:border-0">
                  <td className="py-2">
                    <Link
                      to="/projects/$projectId"
                      params={{ projectId: p.id }}
                      className="font-medium hover:text-primary transition-colors"
                    >
                      {p.name}
                    </Link>
                  </td>
                  <td className="py-2">
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 w-16 rounded-full bg-muted">
                        <div
                          className={`h-full rounded-full ${healthBarColor(p.health_score)}`}
                          style={{ width: `${p.health_score}%` }}
                        />
                      </div>
                      <span className="text-xs text-muted-foreground">{p.health_score}%</span>
                    </div>
                  </td>
                  <td className="py-2 text-muted-foreground">{p.task_count}</td>
                  <td className="py-2 text-muted-foreground hidden sm:table-cell max-w-48 truncate">
                    {p.top_issue || '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
