import { useAcceptanceCriteria, useDoDItems, useDeleteAcceptanceCriterion, useDeleteDoDItem } from '@/hooks/use-quality';
import { useSubtasks, useDeleteSubtask } from '@/hooks/use-subtasks';
import {
  useTaskClaims,
  useTaskHeartbeats,
} from '@/hooks/use-task-execution';
import { useTaskDetail } from '@/hooks/use-task-detail';
import { useUpdateTask } from '@/hooks/use-tasks';
import { useGitLinks } from '@/hooks/use-git-links';
import { useComponents } from '@/hooks/use-components';
import { useModules } from '@/hooks/use-modules';
import { useState, useCallback } from 'react';
import { showToast } from '@/lib/toast';
import { ClarificationsTab } from './ClarificationsTab';
import { EvidenceTab } from './EvidenceTab';
import { ReviewsTab } from './ReviewsTab';
import { CommentsTab } from './CommentsTab';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { PriorityDot } from '@/components/ui/PriorityDot';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { AgentAvatar } from '@/components/ui/AgentAvatar';
import { AgentStatusBadge } from '@/components/ui/AgentStatusBadge';
import {
  Trash2,
  Plus,
  Bot,
  Clock,
  GitBranch,
  Pencil,
  Save,
  X,
} from 'lucide-react';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';

interface TaskDetailSheetProps {
  taskId: string | null;
  projectId?: string;
  onOpenChange: (open: boolean) => void;
}

export function TaskDetailSheet({ taskId, projectId, onOpenChange }: TaskDetailSheetProps) {
  const detail = useTaskDetail(taskId);
  const { data: acs } = useAcceptanceCriteria(taskId ?? '');
  const { data: dods } = useDoDItems(taskId ?? '');
  const { data: subtasks } = useSubtasks(taskId ?? '');
  const deleteAC = useDeleteAcceptanceCriterion();
  const deleteDoD = useDeleteDoDItem();
  const deleteSubtask = useDeleteSubtask();
  const { data: claims, isLoading: isLoadingClaims } = useTaskClaims(taskId ?? '');
  const { data: heartbeats, isLoading: isLoadingHeartbeats } = useTaskHeartbeats(taskId ?? '');
  const { data: gitLinks } = useGitLinks('task', taskId ?? '');

  // UUID resolution
  const { data: components } = useComponents(projectId ?? '');
  const componentMap = new Map((components ?? []).map((c) => [c.id, c.name]));
  const { data: modules } = useModules(detail.task?.component_id ?? '');
  const moduleMap = new Map((modules ?? []).map((m) => [m.id, m.name]));

  const open = !!taskId;
  const updateTask = useUpdateTask();

  // Edit mode state
  const [editing, setEditing] = useState(false);
  const [editTitle, setEditTitle] = useState('');
  const [editDesc, setEditDesc] = useState('');
  const [editPriority, setEditPriority] = useState(0);

  const startEdit = useCallback(() => {
    if (!detail.task) return;
    setEditTitle(detail.task.title);
    setEditDesc(detail.task.description ?? '');
    setEditPriority(detail.task.priority);
    setEditing(true);
  }, [detail.task]);

  const cancelEdit = useCallback(() => setEditing(false), []);

  const saveEdit = useCallback(async () => {
    if (!taskId) return;
    try {
      await updateTask.mutateAsync({
        id: taskId,
        data: { title: editTitle, description: editDesc, priority: editPriority },
      });
      showToast.updated('Task');
      setEditing(false);
    } catch {
      showToast.mutationError('update', 'task');
    }
  }, [taskId, editTitle, editDesc, editPriority, updateTask]);

  const { task, isLoading, isReleasing, newAC, setNewAC, newDoD, setNewDoD, newSubtask, setNewSubtask, activeTab, setActiveTab, confirmDelete, setConfirmDelete, handleAddAC, handleAddDoD, handleAddSubtask, handleStatusChange, handleDelete, handleReleaseClaim } = detail;

  return (
    <>
      <Sheet open={open} onOpenChange={onOpenChange}>
        <SheetContent className="w-full sm:max-w-[600px] overflow-y-auto">
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
                  {!editing && (
                    <Button variant="ghost" size="icon" className="min-h-[44px] min-w-[44px]" onClick={startEdit} aria-label="Edit task">
                      <Pencil className="h-4 w-4" />
                    </Button>
                  )}
                  <Button
                    variant="ghost"
                    size="icon"
                    className="min-h-[44px] min-w-[44px] text-destructive"
                    onClick={() => setConfirmDelete(true)}
                    aria-label="Delete task"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
                <div className="flex items-center gap-2">
                  <StatusBadge status={task.status} />
                  <span className="text-xs text-muted-foreground font-mono">
                    P{task.priority}
                  </span>
                </div>
              </SheetHeader>

              {/* ── Quick Info ── */}
              <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                <div>
                  <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Created</span>
                  <p className="mt-0.5">{new Date(task.created_at).toLocaleDateString()}</p>
                </div>
                <div>
                  <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Updated</span>
                  <p className="mt-0.5">{new Date(task.updated_at).toLocaleDateString()}</p>
                </div>
                {task.component_id && (
                  <div>
                    <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Component</span>
                    <p className="mt-0.5 text-xs">{componentMap.get(task.component_id) ?? task.component_id}</p>
                  </div>
                )}
                {task.module_id && (
                  <div>
                    <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Module</span>
                    <p className="mt-0.5 text-xs">{moduleMap.get(task.module_id) ?? task.module_id}</p>
                  </div>
                )}
              </div>

              {/* ── Tabs ── */}
              <Tabs value={activeTab} onValueChange={setActiveTab} className="mt-6">
                <TabsList className="w-full justify-start">
                  <TabsTrigger value="details">Details</TabsTrigger>
                  <TabsTrigger value="execution">
                    <Bot className="mr-1 h-3 w-3" />
                    Execution
                  </TabsTrigger>
                  <TabsTrigger value="clarifications">
                    Clarifications
                  </TabsTrigger>
                  <TabsTrigger value="evidence">
                    Evidence
                  </TabsTrigger>
                  <TabsTrigger value="reviews">
                    Reviews
                  </TabsTrigger>
                  <TabsTrigger value="comments">
                    Comments
                  </TabsTrigger>
                  <TabsTrigger value="quality">
                    Quality
                  </TabsTrigger>
                </TabsList>

                {/* ── Details Tab ── */}
                <TabsContent value="details" className="mt-4 space-y-4">
                  {editing ? (
                    <>
                      <div className="space-y-2">
                        <label className="text-xs font-medium text-muted-foreground">Title</label>
                        <Input value={editTitle} onChange={(e) => setEditTitle(e.target.value)} />
                      </div>
                      <div className="space-y-2">
                        <label className="text-xs font-medium text-muted-foreground">Description</label>
                        <textarea
                          value={editDesc}
                          onChange={(e) => setEditDesc(e.target.value)}
                          className="flex min-h-[80px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                          placeholder="Task description..."
                        />
                      </div>
                      <div className="space-y-2">
                        <label className="text-xs font-medium text-muted-foreground">Priority (0-10)</label>
                        <Input type="number" min={0} max={10} value={editPriority} onChange={(e) => setEditPriority(Number(e.target.value))} />
                      </div>
                      <div className="flex gap-2">
                        <Button size="sm" onClick={saveEdit} disabled={updateTask.isPending}>
                          <Save className="mr-1 h-3 w-3" /> Save
                        </Button>
                        <Button size="sm" variant="outline" onClick={cancelEdit}>
                          <X className="mr-1 h-3 w-3" /> Cancel
                        </Button>
                      </div>
                    </>
                  ) : (
                    <>
                      {task.description ? (
                        <p className="text-sm leading-relaxed">{task.description}</p>
                      ) : (
                        <p className="text-sm text-muted-foreground italic">No description provided.</p>
                      )}
                      <div className="space-y-2">
                        <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Status</label>
                        <Select value={task.status} onValueChange={(v) => v && handleStatusChange(v)}>
                          <SelectTrigger className="h-9"><SelectValue /></SelectTrigger>
                          <SelectContent>
                            <SelectItem value="backlog">Backlog</SelectItem>
                            <SelectItem value="in-progress">In Progress</SelectItem>
                            <SelectItem value="review">Review</SelectItem>
                            <SelectItem value="done">Done</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </>
                  )}
                </TabsContent>

                {/* ── Execution Tab (claims + heartbeats only) ── */}
                <TabsContent value="execution" className="mt-4 space-y-4">
                  {/* Agent Claims */}
                  {isLoadingClaims ? (
                    <div className="rounded-lg border border-border p-4">
                      <Skeleton className="h-16 w-full" />
                    </div>
                  ) : claims?.items && claims.items.length > 0 ? (
                    <div className="rounded-lg border border-border p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <AgentAvatar name={claims.items[0].agent_id} status={claims.items[0].state === 'claimed' ? 'working' : 'idle'} showPulse={claims.items[0].state === 'claimed'} size="lg" />
                          <div>
                            <p className="text-sm font-medium">{claims.items[0].agent_id}</p>
                            <AgentStatusBadge status={claims.items[0].state === 'claimed' ? 'working' : 'idle'} showPulse={claims.items[0].state === 'claimed'} />
                          </div>
                        </div>
                        {claims.items[0].state === 'claimed' && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={handleReleaseClaim}
                            disabled={isReleasing}
                          >
                            Release claim
                          </Button>
                        )}
                      </div>
                      <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
                        <div>
                          <span className="text-xs text-muted-foreground">Claimed</span>
                          <p className="mt-0.5 flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {claims.items[0].claimed_at ? new Date(claims.items[0].claimed_at).toLocaleString() : 'N/A'}
                          </p>
                        </div>
                        <div>
                          <span className="text-xs text-muted-foreground">State</span>
                          <p className="mt-0.5">{claims.items[0].state}</p>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="rounded-lg border border-dashed border-border p-4">
                      <p className="text-sm text-muted-foreground text-center">No agent claims yet.</p>
                    </div>
                  )}

                  {/* Heartbeats */}
                  {isLoadingHeartbeats ? (
                    <div className="space-y-2">
                      <Skeleton className="h-20 w-full" />
                    </div>
                  ) : heartbeats?.items && heartbeats.items.length > 0 ? (
                    <div className="space-y-2">
                      <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-1.5">
                        <Clock className="h-3 w-3" />
                        Heartbeats
                      </h4>
                      {heartbeats.items.slice(0, 5).map((heartbeat) => (
                        <div key={heartbeat.id} className="rounded-lg border border-border p-3">
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-muted-foreground">{heartbeat.current_step}</span>
                            <span className="text-xs text-muted-foreground">{heartbeat.progress_percent}%</span>
                          </div>
                          <div className="mt-2 h-1.5 w-full rounded-full bg-muted">
                            <div
                              className="h-full rounded-full bg-primary"
                              style={{ width: `${Math.min(heartbeat.progress_percent, 100)}%` }}
                            />
                          </div>
                          {heartbeat.next_step && (
                            <p className="mt-1 text-xs text-muted-foreground">Next: {heartbeat.next_step}</p>
                          )}
                          {heartbeat.blockers && (
                            <p className="mt-1 text-xs text-destructive">Blocker: {heartbeat.blockers}</p>
                          )}
                          {heartbeat.eta && (
                            <p className="mt-1 text-xs text-muted-foreground">ETA: {new Date(heartbeat.eta).toLocaleString()}</p>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : null}

                  {/* Git */}
                  <div>
                    <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-1.5">
                      <GitBranch className="h-3 w-3" />
                      Git
                    </h4>
                    {gitLinks && gitLinks.length > 0 ? (
                      <div className="space-y-1">
                        {gitLinks.map((link) => (
                          <div key={link.id} className="flex items-center gap-2 rounded border px-2 py-1.5 text-xs">
                            <GitBranch className="h-3 w-3 text-muted-foreground" />
                            <span className="font-mono">{link.git_type}: {link.git_id.slice(0, 12)}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="rounded-lg border border-dashed border-border p-3">
                        <p className="text-sm text-muted-foreground text-center">No linked commits.</p>
                      </div>
                    )}
                  </div>
                </TabsContent>

                {/* ── Clarifications Tab ── */}
                <TabsContent value="clarifications" className="mt-4">
                  <ClarificationsTab taskId={taskId ?? ''} taskName={task?.title ?? 'Task'} />
                </TabsContent>

                {/* ── Evidence Tab ── */}
                <TabsContent value="evidence" className="mt-4">
                  <EvidenceTab taskId={taskId ?? ''} />
                </TabsContent>

                {/* ── Reviews Tab ── */}
                <TabsContent value="reviews" className="mt-4">
                  <ReviewsTab taskId={taskId ?? ''} taskStatus={task.status} />
                </TabsContent>

                {/* ── Comments Tab ── */}
                <TabsContent value="comments" className="mt-4">
                  <CommentsTab taskId={taskId ?? ''} />
                </TabsContent>

                {/* ── Quality Tab (AC + DoD + Subtasks) ── */}
                <TabsContent value="quality" className="mt-4 space-y-6">
                  <div>
                    <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
                      Acceptance Criteria ({acs?.length ?? 0})
                    </h4>
                    <ListSection
                      items={acs ?? []}
                      renderItem={(ac) => (
                        <div className="flex items-center justify-between">
                          <span className="text-sm">{ac.description}</span>
                          <Button variant="ghost" size="icon" className="h-6 w-6 text-destructive" onClick={() => deleteAC.mutate(ac.id)}>
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </div>
                      )}
                      emptyText="No acceptance criteria yet."
                    />
                    <div className="flex gap-2 mt-2">
                      <Input
                        placeholder="Add acceptance criterion..."
                        value={newAC}
                        onChange={(e) => setNewAC(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleAddAC()}
                        className="h-9"
                      />
                      <Button size="sm" onClick={handleAddAC} disabled={!newAC.trim()}>
                        <Plus className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>

                  <div>
                    <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
                      Definition of Done ({dods?.length ?? 0})
                    </h4>
                    <ListSection
                      items={dods ?? []}
                      renderItem={(dod) => (
                        <div className="flex items-center justify-between">
                          <span className="text-sm">{dod.name}</span>
                          <Button variant="ghost" size="icon" className="h-6 w-6 text-destructive" onClick={() => deleteDoD.mutate(dod.id)}>
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </div>
                      )}
                      emptyText="No DoD items yet."
                    />
                    <div className="flex gap-2 mt-2">
                      <Input
                        placeholder="Add DoD item..."
                        value={newDoD}
                        onChange={(e) => setNewDoD(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleAddDoD()}
                        className="h-9"
                      />
                      <Button size="sm" onClick={handleAddDoD} disabled={!newDoD.trim()}>
                        <Plus className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>

                  <div>
                    <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
                      Subtasks ({subtasks?.length ?? 0})
                    </h4>
                    <ListSection
                      items={subtasks ?? []}
                      renderItem={(st) => (
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <StatusBadge status={st.status} size="sm" />
                            <span className="text-sm">{st.title}</span>
                          </div>
                          <Button variant="ghost" size="icon" className="h-6 w-6 text-destructive" onClick={() => deleteSubtask.mutate(st.id)}>
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </div>
                      )}
                      emptyText="No subtasks yet."
                    />
                    <div className="flex gap-2 mt-2">
                      <Input
                        placeholder="Add subtask..."
                        value={newSubtask}
                        onChange={(e) => setNewSubtask(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && handleAddSubtask()}
                        className="h-9"
                      />
                      <Button size="sm" onClick={handleAddSubtask} disabled={!newSubtask.trim()}>
                        <Plus className="h-4 w-4" />
                      </Button>
                    </div>
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
        onConfirm={async () => {
          await handleDelete();
          onOpenChange(false);
        }}
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
      <div className="flex items-center gap-2 rounded-lg border border-dashed border-border p-4">
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
          className="flex items-center gap-2 rounded-lg border border-border p-3 transition-colors hover:bg-muted/30"
        >
          {renderItem(item)}
        </div>
      ))}
    </div>
  );
}
