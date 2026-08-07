import { useMemo, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  closestCenter,
  type DragStartEvent,
  type DragEndEvent,
} from '@dnd-kit/core';
import { useDroppable } from '@dnd-kit/core';
import { useDraggable } from '@dnd-kit/core';
import { fetchProjectTasks } from '@/lib/api';
import { useUpdateTask } from '@/hooks/use-tasks';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { PriorityDot } from '@/components/ui/PriorityDot';
import { Skeleton } from '@/components/ui/skeleton';
import { showToast } from '@/lib/toast';
import type { Task } from '@/types/task';
import type { Feature } from '@/types/feature';

const BOARD_COLUMNS = [
  { key: 'backlog', label: 'Backlog' },
  { key: 'in-progress', label: 'In Progress' },
  { key: 'review', label: 'Review' },
  { key: 'done', label: 'Done' },
] as const;

interface BoardViewProps {
  projectId: string;
  features: Feature[];
  search: string;
  onSelectTask: (taskId: string) => void;
}

function DraggableTaskCard({
  task,
  featureName,
  onSelectTask,
}: {
  task: Task;
  featureName?: string;
  onSelectTask: (id: string) => void;
}) {
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
    id: task.id,
    data: { task },
  });

  return (
    <div
      ref={setNodeRef}
      data-draggable
      {...listeners}
      {...attributes}
      className={`cursor-grab rounded-lg border bg-card p-3 transition-colors hover:bg-muted/50 ${
        isDragging ? 'opacity-50' : ''
      }`}
      onClick={() => {
        if (!isDragging) onSelectTask(task.id);
      }}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium leading-tight">{task.title}</p>
          {featureName && (
            <p className="mt-1 text-xs text-muted-foreground">{featureName}</p>
          )}
        </div>
        <PriorityDot priority={task.priority} />
      </div>
      <div className="mt-2">
        <StatusBadge status={task.status} />
      </div>
    </div>
  );
}

function DroppableColumn({
  columnKey,
  children,
}: {
  columnKey: string;
  children: React.ReactNode;
}) {
  const { setNodeRef, isOver } = useDroppable({ id: columnKey });

  return (
    <div
      ref={setNodeRef}
      data-droppable
      className={`min-h-[200px] space-y-2 rounded-lg border border-dashed p-2 transition-colors ${
        isOver ? 'border-primary bg-primary/5' : ''
      }`}
    >
      {children}
    </div>
  );
}

export function BoardView({ projectId, features, search, onSelectTask }: BoardViewProps) {
  const updateTask = useUpdateTask();
  const queryClient = useQueryClient();
  const [activeTask, setActiveTask] = useState<Task | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } })
  );

  const { data, isLoading } = useQuery({
    queryKey: ['project-tasks', projectId],
    queryFn: () => fetchProjectTasks(projectId),
    enabled: !!projectId,
  });

  const allTasksList = useMemo(() => data?.items ?? [], [data]);

  const filteredTasks = useMemo(() => {
    if (!search) return allTasksList;
    const q = search.toLowerCase();
    return allTasksList.filter(
      (t) =>
        t.title.toLowerCase().includes(q) ||
        t.description?.toLowerCase().includes(q)
    );
  }, [allTasksList, search]);

  const tasksByStatus = useMemo(() => {
    const map: Record<string, Task[]> = {};
    for (const col of BOARD_COLUMNS) {
      map[col.key] = [];
    }
    for (const task of filteredTasks) {
      const status = task.status || 'backlog';
      if (map[status]) {
        map[status].push(task);
      } else {
        map.backlog.push(task);
      }
    }
    return map;
  }, [filteredTasks]);

  const featureNameMap = useMemo(() => {
    const map: Record<string, string> = {};
    for (const f of features) {
      map[f.id] = f.name;
    }
    return map;
  }, [features]);

  const handleDragStart = (event: DragStartEvent) => {
    const task = event.active.data.current?.task as Task | undefined;
    if (task) setActiveTask(task);
  };

  const handleDragEnd = async (event: DragEndEvent) => {
    setActiveTask(null);
    const { active, over } = event;
    if (!over) return;

    const task = active.data.current?.task as Task | undefined;
    const newStatus = over.id as string;
    if (!task || task.status === newStatus) return;

    try {
      await updateTask.mutateAsync({
        id: task.id,
        data: { status: newStatus },
      });
      queryClient.invalidateQueries({ queryKey: ['project-tasks', projectId] });
      showToast.updated('Task');
    } catch {
      showToast.mutationError('update', 'task');
    }
  };

  if (isLoading && allTasksList.length === 0) {
    return (
      <div className="grid grid-cols-4 gap-4">
        {BOARD_COLUMNS.map((col) => (
          <div key={col.key} className="space-y-2">
            <Skeleton className="h-8 w-full" />
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-20 w-full rounded-lg" />
            ))}
          </div>
        ))}
      </div>
    );
  }

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {BOARD_COLUMNS.map((col) => (
          <div key={col.key} className="space-y-2">
            <div className="flex items-center gap-2 px-1">
              <h3 className="text-sm font-medium text-muted-foreground">
                {col.label}
              </h3>
              <span className="text-xs text-muted-foreground">
                ({tasksByStatus[col.key]?.length ?? 0})
              </span>
            </div>
            <DroppableColumn columnKey={col.key}>
              {tasksByStatus[col.key]?.length === 0 ? (
                <p className="py-8 text-center text-xs text-muted-foreground">
                  No tasks
                </p>
              ) : (
                tasksByStatus[col.key]?.map((task) => (
                  <DraggableTaskCard
                    key={task.id}
                    task={task}
                    featureName={featureNameMap[task.feature_id]}
                    onSelectTask={onSelectTask}
                  />
                ))
              )}
            </DroppableColumn>
          </div>
        ))}
      </div>

      <DragOverlay>
        {activeTask && (
          <div className="rounded-lg border bg-card p-3 shadow-lg opacity-90">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium leading-tight">
                  {activeTask.title}
                </p>
                {featureNameMap[activeTask.feature_id] && (
                  <p className="mt-1 text-xs text-muted-foreground">
                    {featureNameMap[activeTask.feature_id]}
                  </p>
                )}
              </div>
              <PriorityDot priority={activeTask.priority} />
            </div>
            <div className="mt-2">
              <StatusBadge status={activeTask.status} />
            </div>
          </div>
        )}
      </DragOverlay>
    </DndContext>
  );
}
