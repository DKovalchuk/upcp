import { Badge } from '@/components/ui/badge';
import { AGENT_STATUS_COLORS } from '@/lib/constants';

interface AgentStatusBadgeProps {
  status: 'working' | 'idle' | 'blocked' | 'offline' | 'stale';
  showPulse?: boolean;
}

const STATUS_LABELS: Record<string, string> = {
  working: 'Working',
  idle: 'Idle',
  blocked: 'Blocked',
  offline: 'Offline',
  stale: 'Stale',
};

export function AgentStatusBadge({ status, showPulse = false }: AgentStatusBadgeProps) {
  const colors = AGENT_STATUS_COLORS[status];
  const label = STATUS_LABELS[status];

  return (
    <Badge
      variant="outline"
      className={`${colors.bg} ${colors.text} border-transparent gap-1.5`}
    >
      <span className={`inline-block h-1.5 w-1.5 rounded-full ${colors.dot} ${showPulse ? 'animate-heartbeat-pulse' : ''}`} />
      {label}
    </Badge>
  );
}
