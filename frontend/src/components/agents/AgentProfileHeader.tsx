// Agent Profile Header — TASK-0099 Sprint 2

import { AgentAvatar } from '@/components/ui/AgentAvatar';
import { AgentStatusBadge } from '@/components/ui/AgentStatusBadge';
import { formatRelativeTime } from '@/lib/format';
import type { AgentWithMetrics } from '@/types/agent';

interface AgentProfileHeaderProps {
  agent: AgentWithMetrics;
}

export function AgentProfileHeader({ agent }: AgentProfileHeaderProps) {
  return (
    <div className="flex items-start gap-4">
      <AgentAvatar name={agent.name} size="lg" />
      <div className="flex-1">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold tracking-tight">{agent.name}</h1>
          <AgentStatusBadge status={agent.metrics.status} />
        </div>
        {agent.description && (
          <p className="text-muted-foreground mt-1">{agent.description}</p>
        )}
        <p className="text-sm text-muted-foreground mt-2">
          Created {formatRelativeTime(agent.created_at)}
          {agent.metrics.last_heartbeat_at && (
            <> · Last active {formatRelativeTime(agent.metrics.last_heartbeat_at)}</>
          )}
        </p>
      </div>
    </div>
  );
}
