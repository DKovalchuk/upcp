import { Link } from '@tanstack/react-router';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { EmptyState } from '@/components/ui/EmptyState';
import { Skeleton } from '@/components/ui/skeleton';
import { AgentAvatar } from '@/components/ui/AgentAvatar';
import { AgentStatusBadge } from '@/components/ui/AgentStatusBadge';
import { useAgentActivity } from '@/hooks/use-dashboard';
import { formatRelativeTime } from '@/lib/format';
import { Bot } from 'lucide-react';

// B19.7 (TASK-0154): progress outside [0..100] would overflow the bar
// and display impossible percentages.
const clampPercent = (value: number): number =>
  Math.min(100, Math.max(0, value));

export function AgentActivitySummary() {
  const { data, isLoading } = useAgentActivity();

  const items = data?.items ?? [];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <div className="relative">
            <Bot className="h-4 w-4" />
            <span className="absolute -top-0.5 -right-0.5 h-2 w-2 rounded-full bg-emerald-500 animate-heartbeat-pulse" />
          </div>
          Active Agents
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        {isLoading ? (
          <div className="p-4 space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-center gap-3">
                <Skeleton className="h-10 w-10 rounded-full" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-4 w-1/3" />
                  <Skeleton className="h-3 w-2/3" />
                </div>
                <Skeleton className="h-4 w-16" />
              </div>
            ))}
          </div>
        ) : items.length === 0 ? (
          <div className="p-4">
            <EmptyState
              icon={Bot}
              title="No active agents"
              description="Agent activity will appear here when tasks are running."
            />
          </div>
        ) : (
          <div className="divide-y divide-border">
            {items.map((item) => (
              <Link
                key={item.agent_id}
                to="/agents/$agentId"
                params={{ agentId: item.agent_id }}
                className="flex items-center gap-3 p-4 hover:bg-muted/50 transition-colors"
              >
                <AgentAvatar
                  name={item.agent_name}
                  status={item.is_stale ? 'stale' : 'working'}
                  size="default"
                  showPulse={!item.is_stale}
                />
                <div className="flex-1 min-w-0 space-y-1">
                  <div className="flex items-center justify-between">
                    <h4 className="font-medium text-sm truncate">
                      {item.agent_name}
                    </h4>
                    {item.is_stale && (
                      <AgentStatusBadge status="stale" showPulse />
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground truncate">
                    {item.task_title}
                  </p>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${
                          item.is_stale ? 'bg-orange-500' : 'bg-emerald-500'
                        }`}
                        style={{ width: `${clampPercent(item.progress_percent)}%` }}
                      />
                    </div>
                    <span className="tabular-nums w-8 text-right">
                      {clampPercent(item.progress_percent)}%
                    </span>
                  </div>
                </div>
                <div className="text-xs text-muted-foreground tabular-nums whitespace-nowrap">
                  {item.last_heartbeat_at
                    ? formatRelativeTime(item.last_heartbeat_at)
                    : 'No heartbeat'}
                </div>
              </Link>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
