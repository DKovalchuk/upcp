import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ActorBadge } from '@/components/ui/ActorBadge';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { EmptyState } from '@/components/ui/EmptyState';
import { formatRelativeTime } from '@/lib/format';
import { useDashboardStats } from '@/hooks/use-dashboard';
import { useSSEConnected } from '@/hooks/use-sse-connected';
import { Link } from '@tanstack/react-router';
import { Activity } from 'lucide-react';
import type { AuditEventSummary } from '@/types/api';

/**
 * Map an AuditEventSummary from the API into the display shape used by the feed.
 */
function mapEvent(event: AuditEventSummary) {
  const payload = event.payload as Record<string, unknown> | null;
  const actorName =
    (typeof payload?.actor_name === 'string' && payload.actor_name) ||
    event.actor_id ||
    event.actor_type;

  const entityName =
    (typeof payload?.entity_name === 'string' && payload.entity_name) ||
    event.entity_id;

  const status =
    (typeof payload?.status === 'string' && payload.status) ||
    (typeof payload?.new_status === 'string' && payload.new_status) ||
    undefined;

  // Build a human-readable action from the event_type
  const action = event.event_type
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());

  return {
    id: event.id,
    actorType: (['agent', 'human', 'system'].includes(event.actor_type)
      ? event.actor_type
      : 'system') as 'agent' | 'human' | 'system',
    actorName: String(actorName),
    action,
    entityType: event.entity_type,
    entityName: String(entityName),
    entityHref: `/projects/${event.entity_id}`,
    timestamp: event.timestamp,
    status,
  };
}

export function LiveActivityFeed() {
  const { data: stats, isLoading } = useDashboardStats();
  const sseConnected = useSSEConnected();
  const rawEvents = stats?.recent_activity ?? [];
  const events = rawEvents.map(mapEvent);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="h-4 w-4" />
          Recent Activity
          {sseConnected && (
            <span className="ml-auto flex items-center gap-1.5 text-xs font-normal text-muted-foreground">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
              Live
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {!isLoading && events.length === 0 ? (
          <EmptyState
            icon={Activity}
            title="No recent activity"
            description="Activity from agents and team members will appear here."
          />
        ) : (
          <div className="space-y-3 animate-stagger">
            {events.map((event) => (
              <Link
                key={event.id}
                to={event.entityHref}
                className="flex items-start gap-3 rounded-lg p-2 transition-colors hover:bg-muted/50 group"
              >
                <div className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${
                  event.actorType === 'agent' ? 'bg-violet-500' :
                  event.actorType === 'human' ? 'bg-primary' :
                  'bg-muted-foreground'
                }`} />
                <div className="min-w-0 flex-1">
                  <p className="text-sm">
                    <ActorBadge actorType={event.actorType} actorName={event.actorName} />
                    <span className="text-muted-foreground mx-1">{event.action}</span>
                    <span className="font-medium group-hover:text-primary transition-colors">{event.entityName}</span>
                  </p>
                  <div className="mt-1 flex items-center gap-2">
                    <span className="text-xs text-muted-foreground">
                      {formatRelativeTime(event.timestamp)}
                    </span>
                    {event.status && <StatusBadge status={event.status} size="sm" showDot={false} />}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
