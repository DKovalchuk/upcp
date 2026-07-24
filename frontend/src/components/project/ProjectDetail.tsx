import { useMemo } from 'react';
import { useLocation } from '@tanstack/react-router';
import { useProject } from '@/hooks/use-projects';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { PageSkeleton } from '@/components/ui/PageSkeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { Button } from '@/components/ui/button';
import { Pencil, Trash2 } from 'lucide-react';
import { StructurePage } from './StructurePage';
import { DeliveryPage } from './DeliveryPage';
import { QualityPage } from './QualityPage';
import { AuditPage } from './AuditPage';
import { ReportsPage } from './ReportsPage';
import { GitIntegrationPage } from './GitIntegrationPage';

const TAB_ROUTES: Record<string, string> = {
  structure: 'structure',
  delivery: 'delivery',
  quality: 'quality',
  audit: 'audit',
  git: 'git',
  settings: 'settings',
};

export function ProjectDetail() {
  const location = useLocation();
  const projectId = useMemo(() => {
    const match = location.pathname.match(/^\/projects\/([^/]+)/);
    return match?.[1] ?? '';
  }, [location.pathname]);
  const { data: project, isLoading, error } = useProject(projectId);

  const activeTab = useMemo(() => {
    const segment = location.pathname.split('/').pop();
    if (segment && TAB_ROUTES[segment]) return segment;
    return 'overview';
  }, [location.pathname]);

  if (isLoading) {
    return <PageSkeleton hasHeader hasCards cardCount={4} />;
  }

  if (error || !project) {
    return (
      <ErrorState
        message={error?.message || 'Project not found'}
      />
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{project.name}</h1>
          {project.description && (
            <p className="mt-1 text-muted-foreground">
              {project.description}
            </p>
          )}
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge status={project.status} />
          <Button variant="outline" size="icon" className="h-8 w-8">
            <Pencil className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="icon" className="h-8 w-8 text-destructive">
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <Tabs value={activeTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="structure">Structure</TabsTrigger>
          <TabsTrigger value="delivery">Delivery</TabsTrigger>
          <TabsTrigger value="quality">Quality</TabsTrigger>
          <TabsTrigger value="audit">Audit</TabsTrigger>
          <TabsTrigger value="git">Git</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="mt-6">
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
        </TabsContent>

        <TabsContent value="structure" className="mt-6">
          <StructurePage />
        </TabsContent>

        <TabsContent value="delivery" className="mt-6">
          <DeliveryPage />
        </TabsContent>

        <TabsContent value="quality" className="mt-6">
          <QualityPage />
        </TabsContent>

        <TabsContent value="audit" className="mt-6">
          <AuditPage />
        </TabsContent>

        <TabsContent value="git" className="mt-6">
          <GitIntegrationPage />
        </TabsContent>

        <TabsContent value="settings" className="mt-6">
          <ReportsPage />
        </TabsContent>
      </Tabs>
    </div>
  );
}
