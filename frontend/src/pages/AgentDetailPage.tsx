// Agent Detail page — TASK-0099 Sprint 2

import { useParams } from '@tanstack/react-router';
import { useAgent } from '@/hooks/use-agents';
import { AgentProfileHeader } from '@/components/agents/AgentProfileHeader';
import { AgentClaimsTab } from '@/components/agents/AgentClaimsTab';
import { AgentActivityTab } from '@/components/agents/AgentActivityTab';
import { AgentClarificationsTab } from '@/components/agents/AgentClarificationsTab';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { PageSkeleton } from '@/components/ui/PageSkeleton';
import { ErrorState } from '@/components/ui/ErrorState';

export function AgentDetailPage() {
  const { agentId } = useParams({ from: '/agents/$agentId' });
  const { data: agent, isLoading, error } = useAgent(agentId);

  if (isLoading) {
    return <PageSkeleton hasHeader hasCards cardCount={4} />;
  }

  if (error || !agent) {
    return <ErrorState message="Agent not found" />;
  }

  return (
    <div className="space-y-6">
      <AgentProfileHeader agent={agent} />

      <Tabs defaultValue="overview">
        <TabsList className="w-full justify-start">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="claims">Claims</TabsTrigger>
          <TabsTrigger value="activity">Activity</TabsTrigger>
          <TabsTrigger value="clarifications">Clarifications</TabsTrigger>
          <TabsTrigger value="tokens">Tokens</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="mt-4">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <MetricCard label="Tasks Completed" value={agent.metrics.tasks_completed} />
            <MetricCard label="Tasks Failed" value={agent.metrics.tasks_failed} />
            <MetricCard
              label="Success Rate"
              value={agent.metrics.success_rate !== null ? `${agent.metrics.success_rate}%` : '—'}
            />
            <MetricCard
              label="Status"
              value={agent.metrics.status}
              className="capitalize"
            />
          </div>
          {agent.metrics.current_task_id && (
            <div className="mt-4 rounded-md border p-4">
              <p className="text-sm text-muted-foreground">Current Task</p>
              <p className="font-medium">{agent.metrics.current_task_title ?? agent.metrics.current_task_id}</p>
              {agent.metrics.current_progress_percent !== null && (
                <div className="mt-2 flex items-center gap-2">
                  <div className="h-2 flex-1 rounded-full bg-muted">
                    <div
                      className="h-full rounded-full bg-primary"
                      style={{ width: `${agent.metrics.current_progress_percent}%` }}
                    />
                  </div>
                  <span className="text-sm text-muted-foreground">
                    {agent.metrics.current_progress_percent}%
                  </span>
                </div>
              )}
            </div>
          )}
        </TabsContent>

        <TabsContent value="claims" className="mt-4">
          <AgentClaimsTab agentId={agentId} />
        </TabsContent>

        <TabsContent value="activity" className="mt-4">
          <AgentActivityTab agentId={agentId} />
        </TabsContent>

        <TabsContent value="clarifications" className="mt-4">
          <AgentClarificationsTab agentId={agentId} />
        </TabsContent>

        <TabsContent value="tokens" className="mt-4">
          <div className="rounded-md border">
            <div className="p-4 text-sm text-muted-foreground">
              {agent.tokens.length === 0
                ? 'No tokens generated'
                : `${agent.tokens.length} token(s) configured`}
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function MetricCard({
  label,
  value,
  className,
}: {
  label: string;
  value: string | number;
  className?: string;
}) {
  return (
    <div className="rounded-md border p-4">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className={`text-2xl font-bold ${className ?? ''}`}>{value}</p>
    </div>
  );
}
