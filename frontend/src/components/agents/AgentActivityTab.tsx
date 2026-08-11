// Agent Activity Tab — TASK-0099 Sprint 2

import { useAgentActivity } from '@/hooks/use-agents';
import { EmptyState } from '@/components/ui/EmptyState';
import { formatRelativeTime } from '@/lib/format';
import { Activity } from 'lucide-react';

interface AgentActivityTabProps {
  agentId: string;
}

export function AgentActivityTab({ agentId }: AgentActivityTabProps) {
  const { data, isLoading } = useAgentActivity(agentId);
  const events = data?.items ?? [];

  if (isLoading) {
    return <div className="text-sm text-muted-foreground">Loading...</div>;
  }

  if (events.length === 0) {
    return (
      <EmptyState
        icon={Activity}
        title="No activity"
        description="No events recorded for this agent"
      />
    );
  }

  return (
    <div className="space-y-3">
      {events.map((event) => (
        <div
          key={event.id}
          className="flex items-start gap-3 rounded-md border p-3"
        >
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium">{event.event_type}</p>
            <p className="text-sm text-muted-foreground">{event.message}</p>
          </div>
          <span className="text-xs text-muted-foreground whitespace-nowrap">
            {event.created_at ? formatRelativeTime(event.created_at) : '—'}
          </span>
        </div>
      ))}
    </div>
  );
}
