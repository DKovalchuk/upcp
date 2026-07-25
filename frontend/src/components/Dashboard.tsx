import { Link } from '@tanstack/react-router';
import { useDashboardStats } from '@/hooks/use-dashboard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { PageSkeleton } from '@/components/ui/PageSkeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { EmptyState } from '@/components/ui/EmptyState';
import { formatRelativeTime } from '@/lib/format';
import {
  FolderKanban,
  Activity,
  GitBranch,
  ShieldCheck,
} from 'lucide-react';

function StatCard({
  label,
  value,
  icon: Icon,
  color,
}: {
  label: string;
  value: number | string;
  icon: React.ElementType;
  color: string;
}) {
  return (
    <Card>
      <CardContent className="flex items-center gap-4 p-4">
        <div
          className={`flex h-10 w-10 items-center justify-center rounded-lg ${color}`}
        >
          <Icon className="h-5 w-5" />
        </div>
        <div>
          <p className="text-2xl font-bold">{value}</p>
          <p className="text-sm text-muted-foreground">{label}</p>
        </div>
      </CardContent>
    </Card>
  );
}

export function Dashboard() {
  const { data: stats, isLoading, error } = useDashboardStats();

  if (isLoading) {
    return <PageSkeleton hasCards cardCount={4} rows={5} />;
  }

  if (error) {
    return <ErrorState message="Failed to load dashboard data" />;
  }

  if (stats && stats.project_count === 0) {
    return (
      <EmptyState
        icon={FolderKanban}
        title="No projects yet"
        description="Create your first project to get started with UPCP."
        action={{ label: 'New Project', onClick: () => {} }}
      />
    );
  }

  const tc = stats?.task_counts_by_status;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Projects"
          value={stats?.project_count ?? 0}
          icon={FolderKanban}
          color="bg-primary/10 text-primary"
        />
        <StatCard
          label="Tasks In Progress"
          value={tc?.in_progress ?? 0}
          icon={GitBranch}
          color="bg-blue-500/10 text-blue-600"
        />
        <StatCard
          label="Tasks Done"
          value={tc?.done ?? 0}
          icon={ShieldCheck}
          color="bg-emerald-500/10 text-emerald-600"
        />
        <StatCard
          label="Recent Activity"
          value={stats?.recent_activity?.length ?? 0}
          icon={Activity}
          color="bg-amber-500/10 text-amber-600"
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Recent Projects</CardTitle>
            </CardHeader>
            <CardContent>
              {!stats?.recent_projects?.length ? (
                <p className="text-sm text-muted-foreground">
                  No recent projects.
                </p>
              ) : (
                <div className="space-y-3">
                  {stats.recent_projects.map((project) => (
                    <Link
                      key={project.id}
                      to="/projects/$projectId"
                      params={{ projectId: project.id }}
                      className="flex items-center justify-between rounded-lg border p-3 transition-colors hover:bg-muted/50"
                    >
                      <div className="min-w-0 flex-1">
                        <p className="truncate font-medium">{project.name}</p>
                        {project.description && (
                          <p className="truncate text-sm text-muted-foreground">
                            {project.description}
                          </p>
                        )}
                      </div>
                      <div className="ml-4 flex items-center gap-3">
                        <StatusBadge status={project.status} />
                        <span className="whitespace-nowrap text-xs text-muted-foreground">
                          {formatRelativeTime(project.updated_at)}
                        </span>
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div>
          <Card>
            <CardHeader>
              <CardTitle>Activity Feed</CardTitle>
            </CardHeader>
            <CardContent>
              {!stats?.recent_activity?.length ? (
                <p className="text-sm text-muted-foreground">
                  No recent activity.
                </p>
              ) : (
                <div className="space-y-4">
                  {stats.recent_activity.map((event) => (
                    <div
                      key={event.id}
                      className="flex items-start gap-3"
                    >
                      <div className="mt-1 h-2 w-2 shrink-0 rounded-full bg-primary" />
                      <div className="min-w-0 flex-1">
                        <p className="text-sm">
                          <span className="font-medium">
                            {event.event_type}
                          </span>{' '}
                          <span className="text-muted-foreground">
                            {event.entity_type}
                          </span>
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {formatRelativeTime(event.timestamp)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
