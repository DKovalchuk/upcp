// Agent Clarifications Tab — TASK-0099 Sprint 2

import { useAgentClarifications } from '@/hooks/use-agents';
import { EmptyState } from '@/components/ui/EmptyState';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { formatRelativeTime } from '@/lib/format';
import { MessageCircle } from 'lucide-react';

interface AgentClarificationsTabProps {
  agentId: string;
}

export function AgentClarificationsTab({ agentId }: AgentClarificationsTabProps) {
  const { data, isLoading } = useAgentClarifications(agentId);
  const clarifications = data?.items ?? [];

  if (isLoading) {
    return <div className="text-sm text-muted-foreground">Loading...</div>;
  }

  if (clarifications.length === 0) {
    return (
      <EmptyState
        icon={MessageCircle}
        title="No clarifications"
        description="This agent has not created any clarification requests"
      />
    );
  }

  return (
    <div className="space-y-3">
      {clarifications.map((cr) => (
        <div
          key={cr.id}
          className="flex items-start gap-3 rounded-md border p-3"
        >
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <StatusBadge status={cr.state} />
              {cr.blocking && (
                <span className="text-xs font-medium text-orange-600 dark:text-orange-400">
                  Blocking
                </span>
              )}
            </div>
            <p className="text-sm mt-1">{cr.question}</p>
          </div>
          <span className="text-xs text-muted-foreground whitespace-nowrap">
            {cr.created_at ? formatRelativeTime(cr.created_at) : '—'}
          </span>
        </div>
      ))}
    </div>
  );
}
