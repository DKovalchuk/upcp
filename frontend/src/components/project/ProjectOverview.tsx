import { HealthScoreCard } from './HealthScoreCard';
import { TaskDistributionChart } from './TaskDistributionChart';
import { VelocitySparkline } from './VelocitySparkline';
import { RecentActivity } from './RecentActivity';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { StatusBadge } from '@/components/ui/StatusBadge';

export function ProjectOverview({
  project,
}: {
  project: {
    name: string;
    slug: string;
    description: string | null;
    status: string;
    created_at: string;
    updated_at: string;
  };
}) {
  const projectId = project.slug || '';

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Project Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Name</p>
              <p>{project.name}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Slug</p>
              <p className="font-mono text-sm">{project.slug}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Status</p>
              <StatusBadge status={project.status} />
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Created</p>
              <p>{new Date(project.created_at).toLocaleDateString()}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Updated</p>
              <p>{new Date(project.updated_at).toLocaleDateString()}</p>
            </div>
            {project.description && (
              <div className="col-span-2">
                <p className="text-sm font-medium text-muted-foreground">Description</p>
                <p>{project.description}</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <HealthScoreCard projectId={projectId} />
        <TaskDistributionChart projectId={projectId} />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <VelocitySparkline projectId={projectId} />
        <RecentActivity projectId={projectId} />
      </div>
    </div>
  );
}
