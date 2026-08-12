import { useState } from 'react';
import { useProjectId } from '@/hooks/use-project-id';
import { useComponents } from '@/hooks/use-components';
import { useModules } from '@/hooks/use-modules';
import { useCreateComponent, useDeleteComponent } from '@/hooks/use-components';
import { useCreateModule, useDeleteModule } from '@/hooks/use-modules';
import { EntityFormDialog } from '@/components/forms/EntityFormDialog';
import { componentFields, moduleFields } from '@/components/forms/entity-fields';
import { Card, CardContent, CardTitle } from '@/components/ui/card';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Button } from '@/components/ui/button';
import { EmptyState } from '@/components/ui/EmptyState';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { PageSkeleton } from '@/components/ui/PageSkeleton';
import { Plus, Boxes, ChevronDown, ChevronRight, Trash2 } from 'lucide-react';
import { showToast } from '@/lib/toast';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

export function StructurePage() {
  const projectId = useProjectId();
  const { data: components, isLoading } = useComponents(projectId);
  const createComponent = useCreateComponent();
  const deleteComponent = useDeleteComponent();
  const deleteModule = useDeleteModule();

  const [showCreateComponent, setShowCreateComponent] = useState(false);
  const [expandedComponent, setExpandedComponent] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<{
    type: 'component' | 'module';
    id: string;
    name: string;
  } | null>(null);

  if (isLoading) {
    return <PageSkeleton hasCards cardCount={6} />;
  }

  const handleCreateComponent = async (data: Record<string, string>) => {
    await createComponent.mutateAsync({
      projectId,
      data: {
        name: data.name,
        slug: data.slug || undefined,
        description: data.description || undefined,
        status: data.status || 'active',
      },
    });
    showToast.created('Component');
  };

  const handleDelete = async () => {
    if (!confirmDelete) return;
    try {
      if (confirmDelete.type === 'component') {
        await deleteComponent.mutateAsync(confirmDelete.id);
        showToast.deleted('Component');
      } else {
        await deleteModule.mutateAsync(confirmDelete.id);
        showToast.deleted('Module');
      }
    } catch {
      showToast.mutationError('delete', confirmDelete.type);
    }
    setConfirmDelete(null);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Structure</h2>
        <Button size="sm" onClick={() => setShowCreateComponent(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Component
        </Button>
      </div>

      {!components?.length ? (
        <EmptyState
          icon={Boxes}
          title="No components yet"
          description="Components represent the major parts of your project."
          action={{
            label: 'Create Component',
            onClick: () => setShowCreateComponent(true),
          }}
        />
      ) : (
        <div className="space-y-3">
          {components.map((component) => (
            <ComponentCard
              key={component.id}
              component={component}
              isExpanded={expandedComponent === component.id}
              onToggle={() =>
                setExpandedComponent(
                  expandedComponent === component.id ? null : component.id
                )
              }
              onDelete={() =>
                setConfirmDelete({
                  type: 'component',
                  id: component.id,
                  name: component.name,
                })
              }
              onDeleteModule={(id, name) =>
                setConfirmDelete({ type: 'module', id, name })
              }
            />
          ))}
        </div>
      )}

      <EntityFormDialog
        open={showCreateComponent}
        onOpenChange={setShowCreateComponent}
        title="Create Component"
        fields={componentFields}
        onSubmit={handleCreateComponent}
        submitLabel="Create Component"
      />

      <ConfirmDialog
        open={!!confirmDelete}
        onOpenChange={() => setConfirmDelete(null)}
        title={`Delete ${confirmDelete?.type === 'component' ? 'Component' : 'Module'}`}
        description={`Are you sure you want to delete "${confirmDelete?.name}"? This action cannot be undone.`}
        confirmLabel="Delete"
        variant="destructive"
        onConfirm={handleDelete}
      />
    </div>
  );
}

function ComponentCard({
  component,
  isExpanded,
  onToggle,
  onDelete,
  onDeleteModule,
}: {
  component: { id: string; name: string; slug: string; description: string | null; status: string };
  isExpanded: boolean;
  onToggle: () => void;
  onDelete: () => void;
  onDeleteModule: (id: string, name: string) => void;
}) {
  const { data: modules, isLoading: modulesLoading } = useModules(
    isExpanded ? component.id : ''
  );
  const createModule = useCreateModule();
  const [showCreateModule, setShowCreateModule] = useState(false);

  const handleCreateModule = async (data: Record<string, string>) => {
    await createModule.mutateAsync({
      componentId: component.id,
      data: {
        name: data.name,
        slug: data.slug || undefined,
        description: data.description || undefined,
        status: data.status || 'active',
      },
    });
    showToast.created('Module');
  };

  return (
    <Card>
      <button
        type="button"
        className="flex w-full cursor-pointer select-none items-center justify-between py-3 text-left"
        onClick={onToggle}
        aria-expanded={isExpanded}
        aria-controls={`component-modules-${component.id}`}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {isExpanded ? (
              <ChevronDown className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
            ) : (
              <ChevronRight className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
            )}
            <div>
              <CardTitle className="text-base">{component.name}</CardTitle>
              <p className="text-xs text-muted-foreground font-mono">
                {component.slug}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
            <StatusBadge status={component.status} />
            <Button
              variant="ghost"
              size="icon"
              className="min-h-[44px] min-w-[44px] text-destructive"
              onClick={onDelete}
              aria-label="Delete component"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>
        {component.description && (
          <p className="ml-7 text-sm text-muted-foreground">
            {component.description}
          </p>
        )}
      </button>

      {isExpanded && (
        <div id={`component-modules-${component.id}`}>
        <CardContent className="pt-0">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium text-muted-foreground">
              Modules
            </span>
            <Button
              size="sm"
              variant="outline"
              onClick={() => setShowCreateModule(true)}
            >
              <Plus className="mr-1 h-3 w-3" />
              Module
            </Button>
          </div>

          {modulesLoading ? (
            <div className="space-y-2">
              {[1, 2].map((i) => (
                <div key={i} className="h-10 w-full animate-pulse rounded bg-muted" />
              ))}
            </div>
          ) : !modules?.length ? (
            <p className="text-sm text-muted-foreground py-4 text-center">
              No modules in this component.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Slug</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="w-[50px]" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {modules.map((mod) => (
                  <TableRow key={mod.id}>
                    <TableCell className="font-medium">{mod.name}</TableCell>
                    <TableCell className="font-mono text-xs">
                      {mod.slug}
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={mod.status} />
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="min-h-[44px] min-w-[44px] text-destructive"
                        onClick={() => onDeleteModule(mod.id, mod.name)}
                        aria-label="Delete module"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}

          <EntityFormDialog
            open={showCreateModule}
            onOpenChange={setShowCreateModule}
            title="Create Module"
            fields={moduleFields}
            onSubmit={handleCreateModule}
            submitLabel="Create Module"
          />
        </CardContent>
        </div>
      )}
    </Card>
  );
}
