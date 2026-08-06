import { useState, useMemo } from 'react';
import { useProjectId } from '@/hooks/use-project-id';
import { useFeatures } from '@/hooks/use-features';
import { useTasks } from '@/hooks/use-tasks';
import { useCreateFeature, useDeleteFeature } from '@/hooks/use-features';
import { useCreateTask } from '@/hooks/use-tasks';
import { useUrlPagination } from '@/hooks/use-url-pagination';
import { EntityFormDialog } from '@/components/forms/EntityFormDialog';
import { featureFields, taskFields } from '@/components/forms/entity-fields';
import { TaskDetailSheet } from './TaskDetailSheet';
import { BoardView } from './BoardView';
import { SavedViewsDropdown } from './SavedViewsDropdown';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { PriorityDot } from '@/components/ui/PriorityDot';
import { Button } from '@/components/ui/button';
import { SearchInput } from '@/components/ui/SearchInput';
import { EmptyState } from '@/components/ui/EmptyState';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { PageSkeleton } from '@/components/ui/PageSkeleton';
import { DataTablePagination } from '@/components/ui/DataTablePagination';
import {
  Plus,
  GitBranch,
  ChevronDown,
  ChevronRight,
  Trash2,
  LayoutGrid,
  List,
} from 'lucide-react';
import { showToast } from '@/lib/toast';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import type { Task } from '@/types/task';

export function DeliveryPage() {
  const projectId = useProjectId();
  const { offset, limit, setOffset, setPageSize } = useUrlPagination(20);
  const { data, isLoading } = useFeatures(projectId, { offset, limit });
  const features = data?.items ?? [];
  const total = data?.total ?? 0;
  const createFeature = useCreateFeature();
  const deleteFeature = useDeleteFeature();

  const [showCreateFeature, setShowCreateFeature] = useState(false);
  const [expandedFeature, setExpandedFeature] = useState<string | null>(null);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [viewMode, setViewMode] = useState<'list' | 'board'>('list');
  const [confirmDelete, setConfirmDelete] = useState<{
    id: string;
    name: string;
  } | null>(null);

  if (isLoading) {
    return <PageSkeleton hasCards={false} rows={8} />;
  }

  const handleCreateFeature = async (data: Record<string, string>) => {
    await createFeature.mutateAsync({
      projectId,
      data: {
        name: data.name,
        slug: data.slug || undefined,
        description: data.description || undefined,
        status: data.status || 'backlog',
      },
    });
    showToast.created('Feature');
  };

  const handleDeleteFeature = async () => {
    if (!confirmDelete) return;
    try {
      await deleteFeature.mutateAsync(confirmDelete.id);
      showToast.deleted('Feature');
    } catch {
      showToast.mutationError('delete', 'feature');
    }
    setConfirmDelete(null);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Delivery</h2>
        <div className="flex items-center gap-2">
          <div className="flex items-center rounded-md border">
            <Button
              variant={viewMode === 'list' ? 'secondary' : 'ghost'}
              size="icon"
              className="h-8 w-8 rounded-r-none"
              onClick={() => setViewMode('list')}
              title="List view"
            >
              <List className="h-4 w-4" />
            </Button>
            <Button
              variant={viewMode === 'board' ? 'secondary' : 'ghost'}
              size="icon"
              className="h-8 w-8 rounded-l-none"
              onClick={() => setViewMode('board')}
              title="Board view"
            >
              <LayoutGrid className="h-4 w-4" />
            </Button>
          </div>
          <Button size="sm" onClick={() => setShowCreateFeature(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Feature
          </Button>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className="w-[300px]">
          <SearchInput
            placeholder="Filter tasks..."
            onSearch={setSearch}
          />
        </div>
        <SavedViewsDropdown
          currentFilters={{ search }}
          onApplyView={(filters) => {
            if (filters.search) setSearch(filters.search);
          }}
        />
      </div>

      {!features?.length ? (
        <EmptyState
          icon={GitBranch}
          title="No features yet"
          description="Features represent deliverable units of work in your project."
          action={{
            label: 'Create Feature',
            onClick: () => setShowCreateFeature(true),
          }}
        />
      ) : viewMode === 'board' ? (
        <BoardView
          features={features}
          search={search}
          onSelectTask={setSelectedTaskId}
        />
      ) : (
        <div className="space-y-3">
          {features.map((feature) => (
            <FeatureSection
              key={feature.id}
              feature={feature}
              isExpanded={expandedFeature === feature.id}
              onToggle={() =>
                setExpandedFeature(
                  expandedFeature === feature.id ? null : feature.id
                )
              }
              search={search}
              onSelectTask={setSelectedTaskId}
              onDelete={() =>
                setConfirmDelete({ id: feature.id, name: feature.name })
              }
            />
          ))}
          {total > limit && (
            <DataTablePagination
              offset={offset}
              limit={limit}
              total={total}
              onPageChange={setOffset}
              onPageSizeChange={setPageSize}
            />
          )}
        </div>
      )}

      <EntityFormDialog
        open={showCreateFeature}
        onOpenChange={setShowCreateFeature}
        title="Create Feature"
        fields={featureFields}
        onSubmit={handleCreateFeature}
        submitLabel="Create Feature"
      />

      <ConfirmDialog
        open={!!confirmDelete}
        onOpenChange={() => setConfirmDelete(null)}
        title="Delete Feature"
        description={`Are you sure you want to delete "${confirmDelete?.name}"? This cannot be undone.`}
        confirmLabel="Delete"
        variant="destructive"
        onConfirm={handleDeleteFeature}
      />

      <TaskDetailSheet
        taskId={selectedTaskId}
        projectId={projectId}
        onOpenChange={(open) => {
          if (!open) setSelectedTaskId(null);
        }}
      />
    </div>
  );
}

function FeatureSection({
  feature,
  isExpanded,
  onToggle,
  search,
  onSelectTask,
  onDelete,
}: {
  feature: {
    id: string;
    name: string;
    slug: string;
    description: string | null;
    status: string;
  };
  isExpanded: boolean;
  onToggle: () => void;
  search: string;
  onSelectTask: (taskId: string) => void;
  onDelete: () => void;
}) {
  const { data: tasksData, isLoading: tasksLoading } = useTasks(feature.id);
  const tasks = tasksData?.items ?? [];
  const taskCount = tasksData?.total ?? tasks.length;
  const createTask = useCreateTask();
  const [showCreateTask, setShowCreateTask] = useState(false);

  const featureStatus = useMemo(() => {
    if (tasks.length === 0) return feature.status;
    const statuses = tasks.map((t) => t.status);
    if (statuses.every((s) => s === 'done')) return 'done';
    if (statuses.some((s) => s === 'in-progress' || s === 'claimed' || s === 'blocked')) return 'in-progress';
    if (statuses.some((s) => s === 'review' || s === 'ready_for_review' || s === 'changes_requested')) return 'review';
    return 'backlog';
  }, [tasks, feature.status]);

  const filteredTasks = tasks.filter(
    (t) => !search || t.title.toLowerCase().includes(search.toLowerCase())
  );

  const handleCreateTask = async (data: Record<string, string>) => {
    await createTask.mutateAsync({
      featureId: feature.id,
      data: {
        title: data.title,
        description: data.description || undefined,
        status: data.status || 'backlog',
        priority: data.priority ? Number(data.priority) : 0,
      },
    });
    showToast.created('Task');
  };

  return (
    <div className="rounded-lg border">
      <div
        className="flex cursor-pointer items-center justify-between px-4 py-3 hover:bg-muted/50"
        onClick={onToggle}
      >
        <div className="flex items-center gap-3">
          {isExpanded ? (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronRight className="h-4 w-4 text-muted-foreground" />
          )}
          <div>
            <span className="font-medium">{feature.name}</span>
            <span className="ml-2 text-sm text-muted-foreground">
              ({taskCount} tasks)
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
          <StatusBadge status={featureStatus} />
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7 text-destructive"
            onClick={onDelete}
          >
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>

      {isExpanded && (
        <div className="border-t px-4 py-3">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm text-muted-foreground">Tasks</span>
            <Button
              size="sm"
              variant="outline"
              onClick={() => setShowCreateTask(true)}
            >
              <Plus className="mr-1 h-3 w-3" />
              Task
            </Button>
          </div>

          {tasksLoading ? (
            <div className="space-y-2">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-10 w-full animate-pulse rounded bg-muted" />
              ))}
            </div>
          ) : !filteredTasks?.length ? (
            <p className="text-sm text-muted-foreground py-4 text-center">
              {search ? 'No tasks match your filter.' : 'No tasks in this feature.'}
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[40px]" />
                  <TableHead>Title</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Updated</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredTasks.map((task: Task) => (
                  <TableRow
                    key={task.id}
                    className="cursor-pointer"
                    onClick={() => onSelectTask(task.id)}
                  >
                    <TableCell>
                      <PriorityDot priority={task.priority} />
                    </TableCell>
                    <TableCell className="font-medium">{task.title}</TableCell>
                    <TableCell>
                      <StatusBadge status={task.status} />
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {new Date(task.updated_at).toLocaleDateString()}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}

          <EntityFormDialog
            open={showCreateTask}
            onOpenChange={setShowCreateTask}
            title="Create Task"
            fields={taskFields}
            onSubmit={handleCreateTask}
            submitLabel="Create Task"
          />
        </div>
      )}
    </div>
  );
}
