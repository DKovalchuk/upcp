import { useAcceptanceCriteria, useDoDItems } from '@/hooks/use-quality';
import { useSubtasks } from '@/hooks/use-subtasks';
import {
  useTaskClaims,
  useTaskHeartbeats,
  useTaskClarifications,
  useTaskEvidence,
  useTaskReviewRounds,
} from '@/hooks/use-task-execution';
import { useTaskDetail } from '@/hooks/use-task-detail';
import { useComponents } from '@/hooks/use-components';
import { useModules } from '@/hooks/use-modules';
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
import { ClarificationBanner } from '@/components/ui/ClarificationBanner';
import { ReviewVerdictCard } from '@/components/ui/ReviewVerdictCard';
import {
  Trash2,
  Plus,
  Bot,
  Clock,
  FileText,
  MessageCircle,
  CheckCircle,
  GitBranch,
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
  const { data: claims, isLoading: isLoadingClaims } = useTaskClaims(taskId ?? '');
  const { data: heartbeats, isLoading: isLoadingHeartbeats } = useTaskHeartbeats(taskId ?? '');
  const { data: clarifications, isLoading: isLoadingClarifications } = useTaskClarifications(taskId ?? '');
  const { data: evidence, isLoading: isLoadingEvidence } = useTaskEvidence(taskId ?? '');
  const { data: reviewRounds, isLoading: isLoadingReviewRounds } = useTaskReviewRounds(taskId ?? '');

  // UUID resolution
  const { data: components } = useComponents(projectId ?? '');
  const componentMap = new Map((components ?? []).map((c) => [c.id, c.name]));
  const { data: modules } = useModules(detail.task?.component_id ?? '');
  const moduleMap = new Map((modules ?? []).map((m) => [m.id, m.name]));

  const open = !!taskId;

  const { task, isLoading, isReleasing, newAC, setNewAC, newDoD, setNewDoD, newSubtask, setNewSubtask, activeTab, setActiveTab, confirmDelete, setConfirmDelete, handleAddAC, handleAddDoD, handleAddSubtask, handleStatusChange, handleDelete, handleReleaseClaim, handleSubmitVerdict } = detail;

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

                {/* ── Details Tab ── */}
                <TabsContent value="details" className="mt-4 space-y-4">
                  {task.description ? (
                    <p className="text-sm leading-relaxed">{task.description}</p>
                  ) : (
                    <p className="text-sm text-muted-foreground italic">
                      No description provided.
                    </p>
                  )}

                  <div className="space-y-2">
                    <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Status</label>
                    <Select value={task.status} onValueChange={(v) => v && handleStatusChange(v)}>
                      <SelectTrigger className="h-9">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="backlog">Backlog</SelectItem>
                        <SelectItem value="in-progress">In Progress</SelectItem>
                        <SelectItem value="review">Review</SelectItem>
                        <SelectItem value="done">Done</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </TabsContent>

                {/* ── Execution Tab ── */}
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

                  {/* Clarifications */}
                  <div>
                    <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-1.5">
                      <MessageCircle className="h-3 w-3" />
                      Clarifications
                    </h4>
                    {isLoadingClarifications ? (
                      <Skeleton className="h-20 w-full" />
                    ) : clarifications?.items && clarifications.items.length > 0 ? (
                      <div className="space-y-2">
                        {clarifications.items.map((clarification) => (
                          <ClarificationBanner
                            key={clarification.id}
                            taskName={task?.title ?? 'Task'}
                            question={clarification.question}
                            askedBy={clarification.author_id}
                            askedAt={clarification.created_at}
                            isBlocking={clarification.blocking}
                          />
                        ))}
                      </div>
                    ) : (
                      <div className="rounded-lg border border-dashed border-border p-4">
                        <p className="text-sm text-muted-foreground text-center">No clarifications requested.</p>
                      </div>
                    )}
                  </div>

                  {/* Evidence */}
                  <div>
                    <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-1.5">
                      <FileText className="h-3 w-3" />
                      Evidence
                    </h4>
                    {isLoadingEvidence ? (
                      <Skeleton className="h-20 w-full" />
                    ) : evidence?.items && evidence.items.length > 0 ? (
                      <div className="space-y-2">
                        {evidence.items.map((item) => (
                          <div key={item.id} className="rounded-lg border border-border p-3">
                            <p className="text-sm font-medium">{item.title}</p>
                            <p className="mt-1 text-xs text-muted-foreground">{item.type}</p>
                            {item.description && (
                              <p className="mt-1 text-sm text-muted-foreground">{item.description}</p>
                            )}
                            <div className="mt-2 flex items-center gap-2 text-xs text-muted-foreground">
                              <span>Created: {new Date(item.created_at).toLocaleString()}</span>
                              <span>Verification: {item.verification_state}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="rounded-lg border border-dashed border-border p-4">
                        <p className="text-sm text-muted-foreground text-center">No evidence attached yet.</p>
                      </div>
                    )}
                  </div>

                  {/* Reviews */}
                  <div>
                    <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-1.5">
                      <CheckCircle className="h-3 w-3" />
                      Reviews
                    </h4>
                    {isLoadingReviewRounds ? (
                      <Skeleton className="h-20 w-full" />
                    ) : reviewRounds?.items && reviewRounds.items.length > 0 ? (
                      <div className="space-y-2">
                        {reviewRounds.items.map((round) => (
                          <ReviewVerdictCard
                            key={round.id}
                            agentName={round.reviewer_id ?? 'Unknown reviewer'}
                            verdict={(round.verdict as 'approve' | 'reject' | 'needs_changes') ?? 'approve'}
                            confidence={round.confidence ?? 0}
                            findingsCount={0}
                            summary={round.summary ?? undefined}
                            createdAt={round.created_at}
                            onAccept={
                              round.verdict !== 'approve'
                                ? () => handleSubmitVerdict(round.id, 'approve', round.confidence ?? 80, 'Accepted by human reviewer')
                                : undefined
                            }
                            onReject={
                              round.verdict !== 'reject'
                                ? () => handleSubmitVerdict(round.id, 'reject', round.confidence ?? 50, 'Rejected by human reviewer')
                                : undefined
                            }
                          />
                        ))}
                      </div>
                    ) : (
                      <div className="rounded-lg border border-dashed border-border p-4">
                        <p className="text-sm text-muted-foreground text-center">No reviews yet.</p>
                      </div>
                    )}
                  </div>

                  {/* Git */}
                  <div>
                    <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-1.5">
                      <GitBranch className="h-3 w-3" />
                      Git
                    </h4>
                    <div className="rounded-lg border border-border p-3">
                      <p className="text-sm text-muted-foreground">No linked commits.</p>
                    </div>
                  </div>
                </TabsContent>

                {/* ── Acceptance Criteria Tab ── */}
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
                      className="h-9"
                    />
                    <Button size="sm" onClick={handleAddAC} disabled={!newAC.trim()}>
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                </TabsContent>

                {/* ── DoD Tab ── */}
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
                      className="h-9"
                    />
                    <Button size="sm" onClick={handleAddDoD} disabled={!newDoD.trim()}>
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                </TabsContent>

                {/* ── Subtasks Tab ── */}
                <TabsContent value="subtasks" className="mt-4 space-y-3">
                  <ListSection
                    items={subtasks ?? []}
                    renderItem={(st) => (
                      <div className="flex items-center gap-2">
                        <StatusBadge status={st.status} size="sm" />
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
                      className="h-9"
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
