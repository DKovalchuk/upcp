import { useTask, useUpdateTask, useDeleteTask } from '@/hooks/use-tasks';
import { useAcceptanceCriteria, useDoDItems, useCreateAcceptanceCriterion, useCreateDoDItem } from '@/hooks/use-quality';
import { useSubtasks, useCreateSubtask } from '@/hooks/use-subtasks';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { PriorityDot } from '@/components/ui/PriorityDot';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { Trash2, Plus } from 'lucide-react';
import { useState } from 'react';
import { showToast } from '@/lib/toast';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';

interface TaskDetailSheetProps {
  taskId: string | null;
  onOpenChange: (open: boolean) => void;
}

export function TaskDetailSheet({ taskId, onOpenChange }: TaskDetailSheetProps) {
  const { data: task, isLoading } = useTask(taskId ?? '');
  const { data: acs } = useAcceptanceCriteria(taskId ?? '');
  const { data: dods } = useDoDItems(taskId ?? '');
  const { data: subtasks } = useSubtasks(taskId ?? '');
  const updateTask = useUpdateTask();
  const deleteTask = useDeleteTask();
  const createAC = useCreateAcceptanceCriterion();
  const createDoD = useCreateDoDItem();
  const createSubtask = useCreateSubtask();
  const [newAC, setNewAC] = useState('');
  const [newDoD, setNewDoD] = useState('');
  const [newSubtask, setNewSubtask] = useState('');

  const handleAddAC = async () => {
    if (!taskId || !newAC.trim()) return;
    try {
      await createAC.mutateAsync({ taskId, data: { description: newAC.trim() } });
      setNewAC('');
      showToast.created('Acceptance criterion');
    } catch {
      showToast.mutationError('create', 'acceptance criterion');
    }
  };

  const handleAddDoD = async () => {
    if (!taskId || !newDoD.trim()) return;
    try {
      await createDoD.mutateAsync({ taskId, data: { name: newDoD.trim() } });
      setNewDoD('');
      showToast.created('DoD item');
    } catch {
      showToast.mutationError('create', 'DoD item');
    }
  };

  const handleAddSubtask = async () => {
    if (!taskId || !newSubtask.trim()) return;
    try {
      await createSubtask.mutateAsync({ taskId, data: { title: newSubtask.trim() } });
      setNewSubtask('');
      showToast.created('Subtask');
    } catch {
      showToast.mutationError('create', 'subtask');
    }
  };
  const [activeTab, setActiveTab] = useState('details');
  const [confirmDelete, setConfirmDelete] = useState(false);

  const open = !!taskId;

  const handleStatusChange = async (newStatus: string) => {
    if (!taskId) return;
    try {
      await updateTask.mutateAsync({ id: taskId, data: { status: newStatus } });
      showToast.updated('Task');
    } catch {
      showToast.mutationError('update', 'task');
    }
  };

  const handleDelete = async () => {
    if (!taskId) return;
    try {
      await deleteTask.mutateAsync(taskId);
      showToast.deleted('Task');
      onOpenChange(false);
    } catch {
      showToast.mutationError('delete', 'task');
    }
  };

  return (
    <>
      <Sheet open={open} onOpenChange={onOpenChange}>
        <SheetContent className="w-full sm:max-w-[540px] overflow-y-auto">
          {isLoading ? (
            <div className="space-y-4 py-4">
              <Skeleton className="h-6 w-[200px]" />
              <Skeleton className="h-4 w-[300px]" />
              <Skeleton className="h-[200px] w-full" />
            </div>
          ) : task ? (
            <>
              <SheetHeader>
                <div className="flex items-center gap-2">
                  <PriorityDot priority={task.priority} />
                  <SheetTitle className="flex-1">{task.title}</SheetTitle>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-destructive"
                    onClick={() => setConfirmDelete(true)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
                <div className="flex items-center gap-2">
                  <StatusBadge status={task.status} />
                  <span className="text-xs text-muted-foreground">
                    P{task.priority}
                  </span>
                </div>
              </SheetHeader>

              <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                <div>
                  <span className="text-muted-foreground">Created</span>
                  <p>{new Date(task.created_at).toLocaleDateString()}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Updated</span>
                  <p>{new Date(task.updated_at).toLocaleDateString()}</p>
                </div>
                {task.component_id && (
                  <div>
                    <span className="text-muted-foreground">Component</span>
                    <p className="font-mono text-xs">{task.component_id}</p>
                  </div>
                )}
                {task.module_id && (
                  <div>
                    <span className="text-muted-foreground">Module</span>
                    <p className="font-mono text-xs">{task.module_id}</p>
                  </div>
                )}
              </div>

              <Tabs value={activeTab} onValueChange={setActiveTab} className="mt-6">
                <TabsList>
                  <TabsTrigger value="details">Details</TabsTrigger>
                  <TabsTrigger value="ac">
                    AC ({acs?.length ?? 0})
                  </TabsTrigger>
                  <TabsTrigger value="dod">
                    DoD ({dods?.length ?? 0})
                  </TabsTrigger>
                  <TabsTrigger value="subtasks">
                    Subtasks ({subtasks?.length ?? 0})
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="details" className="mt-4 space-y-4">
                  {task.description ? (
                    <p className="text-sm">{task.description}</p>
                  ) : (
                    <p className="text-sm text-muted-foreground italic">
                      No description provided.
                    </p>
                  )}

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Status</label>
                    <select
                      value={task.status}
                      onChange={(e) => handleStatusChange(e.target.value)}
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                    >
                      <option value="backlog">Backlog</option>
                      <option value="in-progress">In Progress</option>
                      <option value="review">Review</option>
                      <option value="done">Done</option>
                    </select>
                  </div>
                </TabsContent>

                <TabsContent value="ac" className="mt-4 space-y-3">
                  <ListSection
                    items={acs ?? []}
                    renderItem={(ac) => (
                      <span className="text-sm">{ac.description}</span>
                    )}
                    emptyText="No acceptance criteria yet."
                  />
                  <div className="flex gap-2">
                    <Input
                      placeholder="Add acceptance criterion..."
                      value={newAC}
                      onChange={(e) => setNewAC(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleAddAC()}
                    />
                    <Button size="sm" onClick={handleAddAC} disabled={!newAC.trim()}>
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                </TabsContent>

                <TabsContent value="dod" className="mt-4 space-y-3">
                  <ListSection
                    items={dods ?? []}
                    renderItem={(dod) => (
                      <span className="text-sm">{dod.name}</span>
                    )}
                    emptyText="No DoD items yet."
                  />
                  <div className="flex gap-2">
                    <Input
                      placeholder="Add DoD item..."
                      value={newDoD}
                      onChange={(e) => setNewDoD(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleAddDoD()}
                    />
                    <Button size="sm" onClick={handleAddDoD} disabled={!newDoD.trim()}>
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                </TabsContent>

                <TabsContent value="subtasks" className="mt-4 space-y-3">
                  <ListSection
                    items={subtasks ?? []}
                    renderItem={(st) => (
                      <div className="flex items-center gap-2">
                        <StatusBadge status={st.status} />
                        <span className="text-sm">{st.title}</span>
                      </div>
                    )}
                    emptyText="No subtasks yet."
                  />
                  <div className="flex gap-2">
                    <Input
                      placeholder="Add subtask..."
                      value={newSubtask}
                      onChange={(e) => setNewSubtask(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleAddSubtask()}
                    />
                    <Button size="sm" onClick={handleAddSubtask} disabled={!newSubtask.trim()}>
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                </TabsContent>
              </Tabs>
            </>
          ) : null}
        </SheetContent>
      </Sheet>

      <ConfirmDialog
        open={confirmDelete}
        onOpenChange={setConfirmDelete}
        title="Delete Task"
        description="Are you sure you want to delete this task? This action cannot be undone."
        confirmLabel="Delete"
        variant="destructive"
        onConfirm={handleDelete}
      />
    </>
  );
}

function ListSection<T extends { id?: string }>({
  items,
  renderItem,
  emptyText,
}: {
  items: T[];
  renderItem: (item: T) => React.ReactNode;
  emptyText: string;
}) {
  if (items.length === 0) {
    return (
      <div className="flex items-center gap-2 rounded-md border p-3">
        <Plus className="h-4 w-4 text-muted-foreground" />
        <span className="text-sm text-muted-foreground">{emptyText}</span>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {items.map((item) => (
        <div
          key={item.id ?? Math.random()}
          className="flex items-center gap-2 rounded-md border p-3"
        >
          {renderItem(item)}
        </div>
      ))}
    </div>
  );
}
