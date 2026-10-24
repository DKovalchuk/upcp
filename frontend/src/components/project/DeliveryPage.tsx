import { useState, useMemo } from 'react';
import { useProjectId } from '@/hooks/use-project-id';
import { useFeatures } from '@/hooks/use-features';
import { useTasks } from '@/hooks/use-tasks';
import { useFilters } from '@/hooks/use-filters';
import { useCreateFeature, useDeleteFeature } from '@/hooks/use-features';
import { useCreateTask, useBulkUpdateTasks } from '@/hooks/use-tasks';
import { useUrlPagination } from '@/hooks/use-url-pagination';
import { useLazyMount } from '@/hooks/use-lazy-mount';
import { EntityFormDialog } from '@/components/forms/EntityFormDialog';
import { featureFields, taskFields } from '@/components/forms/entity-fields';
import { TaskDetailSheet } from './TaskDetailSheet';
import { LazyBoardView } from './LazyBoardView';
import { FilterBar } from '@/components/ui/FilterBar';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Button } from '@/components/ui/button';
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
  CheckSquare,
  Square,
  MinusSquare,
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
  const { filters } = useFilters();
  const featureFilters = { status: filters.status, search: filters.search };
  const { data, isLoading } = useFeatures(projectId, { offset, limit }, featureFilters);
  const features = data?.items ?? [];
  const total = data?.total ?? 0;
  const createFeature = useCreateFeature();
  const deleteFeature = useDeleteFeature();

  const [showCreateFeature, setShowCreateFeature] = useState(false);
  const [expandedFeature, setExpandedFeature] = useState<string | null>(null);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'list' | 'board'>('list');
  const [confirmDelete, setConfirmDelete] = useState<{
    id: string;
    name: string;
  } | null>(null);
  const [selectedTaskIds, setSelectedTaskIds] = useState<Set<string>>(new Set());
  const [showBulkStatus, setShowBulkStatus] = useState(false);
  const bulkUpdate = useBulkUpdateTasks();

  const taskDetailSheet = useLazyMount(!!selectedTaskId, (open) => {
    if (!open) setSelectedTaskId(null);
  });

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
              className="min-h-[44px] min-w-[44px] rounded-r-none"
              onClick={() => setViewMode('list')}
              aria-label="List view"
            >
              <List className="h-4 w-4" />
            </Button>
            <Button
              variant={viewMode === 'board' ? 'secondary' : 'ghost'}
              size="icon"
              className="min-h-[44px] min-w-[44px] rounded-l-none"
              onClick={() => setViewMode('board')}
              aria-label="Board view"
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
        <FilterBar
          showSearch
          showStatus
          searchPlaceholder="Filter features..."
          statusOptions={[
            { value: 'backlog', label: 'Backlog' },
            { value: 'in_progress', label: 'In Progress' },
            { value: 'review', label: 'Review' },
            { value: 'done', label: 'Done' },
          ]}
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
        <LazyBoardView
          projectId={projectId}
          features={features}
          search={filters.search ?? ''}
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
              search={filters.search ?? ''}
              onSelectTask={setSelectedTaskId}
              onDelete={() =>
                setConfirmDelete({ id: feature.id, name: feature.name })
              }
              selectedTaskIds={selectedTaskIds}
              setSelectedTaskIds={setSelectedTaskIds}
              showBulkStatus={showBulkStatus}
              setShowBulkStatus={setShowBulkStatus}
              bulkUpdate={bulkUpdate}
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

      {taskDetailSheet.mounted && (
        <TaskDetailSheet
          taskId={selectedTaskId}
          projectId={projectId}
          onOpenChange={(open) => {
            if (!open) setSelectedTaskId(null);
          }}
        />
      )}
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
  selectedTaskIds,
  setSelectedTaskIds,
  showBulkStatus,
  setShowBulkStatus,
  bulkUpdate,
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
  selectedTaskIds: Set<string>;
  setSelectedTaskIds: React.Dispatch<React.SetStateAction<Set<string>>>;
  showBulkStatus: boolean;
  setShowBulkStatus: React.Dispatch<React.SetStateAction<boolean>>;
  bulkUpdate: { mutateAsync: (args: { taskIds: string[]; updates: { status?: string } }) => Promise<unknown>; isPending: boolean };
}) {
  const { data: tasksData, isLoading: tasksLoading } = useTasks(feature.id);
  const tasks = useMemo(() => tasksData?.items ?? [], [tasksData]);
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
      <div className="flex items-center justify-between px-4 py-3 hover:bg-muted/50">
        <button
          type="button"
          className="flex flex-1 cursor-pointer items-center gap-3 text-left"
          onClick={onToggle}
          aria-expanded={isExpanded}
          aria-controls={`feature-tasks-${feature.id}`}
        >
          {isExpanded ? (
            <ChevronDown className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
          ) : (
            <ChevronRight className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
          )}
          <div>
            <span className="font-medium">{feature.name}</span>
            <span className="ml-2 text-sm text-muted-foreground">
              ({taskCount} tasks)
            </span>
          </div>
        </button>
        <div className="ml-3 flex items-center gap-2">
          <StatusBadge status={featureStatus} />
          <Button
            variant="ghost"
            size="icon"
            className="min-h-[44px] min-w-[44px] text-destructive"
            onClick={onDelete}
            aria-label="Delete feature"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>

      {isExpanded && (
        <div id={`feature-tasks-${feature.id}`} className="border-t px-4 py-3">
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
            <>
              {/* Bulk actions toolbar */}
              {selectedTaskIds.size > 0 && (
                <div className="flex items-center gap-2 rounded-md border bg-muted/50 p-2 text-sm">
                  <span className="text-muted-foreground">{selectedTaskIds.size} selected</span>
                  <Button
                    size="sm"
                    variant="outline"
                    className="h-7 text-xs"
                    onClick={() => setShowBulkStatus(true)}
                  >
                    Change Status
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    className="h-7 text-xs"
                    onClick={() => setSelectedTaskIds(new Set())}
                  >
                    Clear
                  </Button>
                </div>
              )}

              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[40px]">
                      <button
                        type="button"
                        onClick={() => {
                          if (selectedTaskIds.size === filteredTasks.length) {
                            setSelectedTaskIds(new Set());
                          } else {
                            setSelectedTaskIds(new Set(filteredTasks.map((t) => t.id)));
                          }
                        }}
                        className="text-muted-foreground hover:text-foreground"
                      >
                        {selectedTaskIds.size === 0 ? (
                          <Square className="h-4 w-4" />
                        ) : selectedTaskIds.size === filteredTasks.length ? (
                          <CheckSquare className="h-4 w-4" />
                        ) : (
                          <MinusSquare className="h-4 w-4" />
                        )}
                      </button>
                    </TableHead>
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
                    >
                      <TableCell>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedTaskIds((prev) => {
                              const next = new Set(prev);
                              if (next.has(task.id)) next.delete(task.id);
                              else next.add(task.id);
                              return next;
                            });
                          }}
                          className="text-muted-foreground hover:text-foreground"
                        >
                          {selectedTaskIds.has(task.id) ? (
                            <CheckSquare className="h-4 w-4" />
                          ) : (
                            <Square className="h-4 w-4" />
                          )}
                        </button>
                      </TableCell>
                      <TableCell
                        className="font-medium"
                        onClick={() => onSelectTask(task.id)}
                      >
                        {task.title}
                      </TableCell>
                      <TableCell onClick={() => onSelectTask(task.id)}>
                        <StatusBadge status={task.status} />
                      </TableCell>
                      <TableCell
                        className="text-xs text-muted-foreground"
                        onClick={() => onSelectTask(task.id)}
                      >
                        {new Date(task.updated_at).toLocaleDateString()}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </>
          )}

          {/* Bulk status change dialog */}
          <ConfirmDialog
            open={showBulkStatus}
            onOpenChange={setShowBulkStatus}
            title="Change Task Status"
            description={`Change status of ${selectedTaskIds.size} task(s)?`}
            confirmLabel="Change Status"
            onConfirm={async () => {
              await bulkUpdate.mutateAsync({
                taskIds: Array.from(selectedTaskIds),
                updates: { status: 'ready' },
              });
              showToast.updated(`${selectedTaskIds.size} task(s)`);
              setSelectedTaskIds(new Set());
              setShowBulkStatus(false);
            }}
          />

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
