import { useMemo } from 'react';
import { useQueries } from '@tanstack/react-query';
import { fetchTasks } from '@/lib/api';
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

const STATUS_ORDER = BOARD_COLUMNS.map((c) => c.key);

function nextStatus(current: string): string {
  const idx = STATUS_ORDER.indexOf(current as (typeof STATUS_ORDER)[number]);
  if (idx === -1) return STATUS_ORDER[0];
  return STATUS_ORDER[(idx + 1) % STATUS_ORDER.length];
}

interface BoardViewProps {
  features: Feature[];
  search: string;
  onSelectTask: (taskId: string) => void;
}

export function BoardView({ features, search, onSelectTask }: BoardViewProps) {
  const updateTask = useUpdateTask();

  const taskQueries = useQueries({
    queries: features.map((f) => ({
      queryKey: ['tasks', f.id],
      queryFn: () => fetchTasks(f.id),
      enabled: !!f.id,
    })),
  });

  const isLoading = taskQueries.some((q) => q.isLoading);

  const allTasksList = useMemo(() => {
    const result: Task[] = [];
    for (const q of taskQueries) {
      if (q.data?.items) {
        result.push(...q.data.items);
      }
    }
    return result;
  }, [taskQueries]);

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

  const handleStatusChange = async (task: Task) => {
    const newStatus = nextStatus(task.status);
    try {
      await updateTask.mutateAsync({
        id: task.id,
        data: { status: newStatus },
      });
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
          <div className="min-h-[200px] space-y-2 rounded-lg border border-dashed p-2">
            {tasksByStatus[col.key]?.length === 0 ? (
              <p className="py-8 text-center text-xs text-muted-foreground">
                No tasks
              </p>
            ) : (
              tasksByStatus[col.key]?.map((task) => (
                <div
                  key={task.id}
                  className="cursor-pointer rounded-lg border bg-card p-3 transition-colors hover:bg-muted/50"
                  onClick={() => onSelectTask(task.id)}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium leading-tight">
                        {task.title}
                      </p>
                      {featureNameMap[task.feature_id] && (
                        <p className="mt-1 text-xs text-muted-foreground">
                          {featureNameMap[task.feature_id]}
                        </p>
                      )}
                    </div>
                    <PriorityDot priority={task.priority} />
                  </div>
                  <div className="mt-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleStatusChange(task);
                      }}
                      className="inline-block"
                    >
                      <StatusBadge status={task.status} />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
