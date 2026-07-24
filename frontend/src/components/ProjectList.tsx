import { useProjects } from '@/hooks/use-projects';
import { ProjectTable } from '@/components/ProjectTable';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorState } from '@/components/ui/ErrorState';
import { Skeleton } from '@/components/ui/skeleton';
import { FolderKanban } from 'lucide-react';

export function ProjectList() {
  const { data: projects, isLoading, error, refetch } = useProjects();

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-8 w-[200px]" />
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent>
          <ErrorState
            message={error.message || 'Failed to load projects'}
            onRetry={refetch}
          />
        </CardContent>
      </Card>
    );
  }

  if (!projects || projects.length === 0) {
    return (
      <Card>
        <CardContent>
          <EmptyState
            icon={FolderKanban}
            title="No projects yet"
            description="Create your first project to get started."
            action={{ label: 'New Project', onClick: () => {} }}
          />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-2xl font-bold">Projects</CardTitle>
        <Button size="sm">New Project</Button>
      </CardHeader>
      <CardContent>
        <ProjectTable projects={projects} />
      </CardContent>
    </Card>
  );
}