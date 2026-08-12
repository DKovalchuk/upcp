import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { History, GitCommit, FolderOpen, CheckCircle, AlertCircle } from 'lucide-react';
import { fetchAuditEvents } from '@/lib/api/audit';
import { formatRelativeTime } from '@/lib/format';

const EVENT_ICONS: Record<string, typeof GitCommit> = {
  task: GitCommit,
  project: FolderOpen,
  evidence: CheckCircle,
  review: AlertCircle,
};

function EventIcon({ eventType }: { eventType: string }) {
  const base = eventType.split('.')[0];
  const Icon = EVENT_ICONS[base] ?? GitCommit;
  return <Icon className="h-3.5 w-3.5 text-muted-foreground shrink-0" />;
}

export function RecentActivity({ projectId }: { projectId: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ['audit-events', projectId],
    queryFn: () => fetchAuditEvents(projectId, undefined, { offset: 0, limit: 10 }),
    enabled: !!projectId,
  });

  const events = data?.items ?? [];

  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-8 w-full animate-pulse rounded bg-muted" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center gap-2 space-y-0 pb-2">
        <History className="h-4 w-4" />
        <CardTitle>Recent Activity</CardTitle>
      </CardHeader>
      <CardContent>
        {events.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-4">
            No activity yet
          </p>
        ) : (
          <div className="space-y-3">
            {events.map((event) => (
              <div key={event.id} className="flex items-start gap-3">
                <EventIcon eventType={event.event_type} />
                <div className="min-w-0 flex-1">
                  <p className="text-sm">
                    <span className="font-medium">{event.event_type}</span>
                    {event.note && (
                      <span className="text-muted-foreground"> — {event.note}</span>
                    )}
                  </p>
                  <p className="text-[10px] text-muted-foreground">
                    {formatRelativeTime(event.timestamp)}
                    {event.actor_id && (
                      <span> by {event.actor_id}</span>
                    )}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
