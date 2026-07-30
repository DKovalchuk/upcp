import { useState, useMemo } from 'react';
import { useProjects, useCreateProject } from '@/hooks/use-projects';
import { useUrlPagination } from '@/hooks/use-url-pagination';
import { ProjectTable } from '@/components/ProjectTable';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorState } from '@/components/ui/ErrorState';
import { Skeleton } from '@/components/ui/skeleton';
import { DataTablePagination } from '@/components/ui/DataTablePagination';
import { EntityFormDialog } from '@/components/forms/EntityFormDialog';
import { projectFields } from '@/components/forms/entity-fields';
import { showToast } from '@/lib/toast';
import { FolderKanban } from 'lucide-react';

export function ProjectList() {
  const { offset, limit, setOffset, setPageSize } = useUrlPagination(20);
  const { data, isLoading, error, refetch } = useProjects({ offset, limit });
  const createProject = useCreateProject();
  const [showCreate, setShowCreate] = useState(false);

  const projects = data?.items ?? [];
  const total = data?.total ?? 0;

  // Create dialog omits status field (defaults to "active" on server)
  const projectFieldsForCreate = useMemo(
    () => projectFields.filter((f) => f.name !== 'status'),
    []
  );

  const handleCreate = async (formData: Record<string, string>) => {
    await createProject.mutateAsync({
      name: formData.name,
      slug: formData.slug || undefined,
      description: formData.description || undefined,
    });
    showToast.created('Project');
  };

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

  if (!projects.length) {
    return (
      <>
        <Card>
          <CardContent>
            <EmptyState
              icon={FolderKanban}
              title="No projects yet"
              description="Create your first project to get started."
              action={{ label: 'New Project', onClick: () => setShowCreate(true) }}
            />
          </CardContent>
        </Card>
        <EntityFormDialog
          open={showCreate}
          onOpenChange={setShowCreate}
          title="New Project"
          fields={projectFieldsForCreate}
          onSubmit={handleCreate}
          submitLabel="Create"
        />
      </>
    );
  }

  return (
    <>
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-2xl font-bold">Projects</CardTitle>
          <Button size="sm" onClick={() => setShowCreate(true)}>New Project</Button>
        </CardHeader>
        <CardContent className="space-y-4">
          <ProjectTable projects={projects} />
          {total > limit && (
            <DataTablePagination
              offset={offset}
              limit={limit}
              total={total}
              onPageChange={setOffset}
              onPageSizeChange={setPageSize}
            />
          )}
        </CardContent>
      </Card>
      <EntityFormDialog
        open={showCreate}
        onOpenChange={setShowCreate}
        title="New Project"
        fields={projectFieldsForCreate}
        onSubmit={handleCreate}
        submitLabel="Create"
      />
    </>
  );
}
