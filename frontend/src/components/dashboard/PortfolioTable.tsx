import { useState } from 'react';
import { Link, useNavigate } from '@tanstack/react-router';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Button } from '@/components/ui/button';
import type { PortfolioProject } from '@/types/dashboard';

const INITIAL_VISIBLE_PROJECTS = 5;

function healthBarColor(score: number): string {
  if (score >= 80) return 'bg-emerald-500';
  if (score >= 50) return 'bg-amber-500';
  return 'bg-red-500';
}

export function PortfolioTable({
  projects,
  isLoading,
  projectStatuses,
}: {
  projects?: PortfolioProject[];
  isLoading?: boolean;
  projectStatuses?: Record<string, string>;
}) {
  const navigate = useNavigate();
  const [showAll, setShowAll] = useState(false);

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

  const visible = showAll ? projects : projects.slice(0, INITIAL_VISIBLE_PROJECTS);

  const handleRowClick = (projectId: string, target: EventTarget & Element) => {
    // Keep the name link as the interactive element; avoid double navigation.
    if (target.closest('a')) return;
    navigate({ to: '/projects/$projectId', params: { projectId } });
  };

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
                <th className="pb-2 font-medium">Status</th>
                <th className="pb-2 font-medium hidden sm:table-cell">Top Issue</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((p) => {
                const status = projectStatuses?.[p.id];
                return (
                  <tr
                    key={p.id}
                    className="cursor-pointer border-b transition-colors last:border-0 hover:bg-muted/50"
                    onClick={(e) => handleRowClick(p.id, e.target as Element)}
                  >
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
                    <td className="py-2">
                      {status ? (
                        <StatusBadge status={status} />
                      ) : (
                        <span className="text-xs text-muted-foreground">—</span>
                      )}
                    </td>
                    <td className="py-2 hidden max-w-48 truncate text-muted-foreground sm:table-cell">
                      {p.top_issue || '—'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        {projects.length > INITIAL_VISIBLE_PROJECTS && (
          <div className="mt-3 text-center">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowAll((prev) => !prev)}
            >
              {showAll ? 'Show less' : 'Show more'}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
