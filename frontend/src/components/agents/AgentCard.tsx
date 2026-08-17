// Agent Card component — TASK-0099 Sprint 2

import { AgentAvatar } from '@/components/ui/AgentAvatar';
import { AgentStatusBadge } from '@/components/ui/AgentStatusBadge';
import { Card, CardContent } from '@/components/ui/card';
import type { AgentProfile } from '@/types/agent';

interface AgentCardProps {
  agent: AgentProfile;
  onSelect: () => void;
}

export function AgentCard({ agent, onSelect }: AgentCardProps) {
  return (
    <Card
      className="cursor-pointer transition-colors hover:ring-1 hover:ring-ring/20"
      onClick={onSelect}
    >
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          <AgentAvatar name={agent.name} size="lg" />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="font-medium truncate">{agent.name}</h3>
              <AgentStatusBadge status={agent.is_active ? 'idle' : 'offline'} />
            </div>
            {agent.description && (
              <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                {agent.description}
              </p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
