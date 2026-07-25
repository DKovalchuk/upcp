import { useState } from 'react';
import { useAuditEvents } from '@/hooks/use-audit';
import { useProjectId } from '@/hooks/use-project-id';
import { useUrlPagination } from '@/hooks/use-url-pagination';
import { Card, CardContent } from '@/components/ui/card';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { PageSkeleton } from '@/components/ui/PageSkeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { DataTablePagination } from '@/components/ui/DataTablePagination';
import { formatRelativeTime } from '@/lib/format';
import { ScrollText } from 'lucide-react';
import type { AuditEvent } from '@/types/audit';

const EVENT_COLORS: Record<string, string> = {
  created: 'bg-emerald-500',
  updated: 'bg-blue-500',
  deleted: 'bg-red-500',
  completed: 'bg-violet-500',
};

export function AuditPage() {
  const projectId = useProjectId();

  const { offset, limit, setOffset, setPageSize } = useUrlPagination(20);
  const [eventType, setEventType] = useState('');
  const [entityType, setEntityType] = useState('');

  const { data, isLoading, error } = useAuditEvents(
    {
      project_id: projectId,
      ...(eventType ? { event_type: eventType } : {}),
      ...(entityType ? { entity_type: entityType } : {}),
    },
    { offset, limit }
  );

  if (isLoading) return <PageSkeleton rows={8} />;
  if (error) return <ErrorState message="Failed to load audit events" />;

  const events = data?.items ?? [];
  const total = data?.total ?? 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <ScrollText className="h-5 w-5" />
        <h2 className="text-lg font-semibold">Audit Log</h2>
      </div>

      <div className="flex items-center gap-3">
        <select
          value={eventType}
          onChange={(e) => setEventType(e.target.value)}
          className="h-9 rounded-md border border-input bg-background px-3 text-sm"
        >
          <option value="">All event types</option>
          <option value="created">Created</option>
          <option value="updated">Updated</option>
          <option value="deleted">Deleted</option>
        </select>
        <select
          value={entityType}
          onChange={(e) => setEntityType(e.target.value)}
          className="h-9 rounded-md border border-input bg-background px-3 text-sm"
        >
          <option value="">All entity types</option>
          <option value="project">Project</option>
          <option value="component">Component</option>
          <option value="module">Module</option>
          <option value="feature">Feature</option>
          <option value="task">Task</option>
          <option value="subtask">Subtask</option>
        </select>
      </div>

      {!events.length ? (
        <Card>
          <CardContent className="py-8 text-center text-muted-foreground">
            No audit events found.
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="relative space-y-0">
            <div className="absolute left-[15px] top-0 bottom-0 w-px bg-border" />
            {events.map((event: AuditEvent) => (
              <div key={event.id} className="relative flex gap-4 py-3">
                <div className={`relative z-10 mt-1 h-3 w-3 shrink-0 rounded-full ${EVENT_COLORS[event.event_type] ?? 'bg-slate-400'}`} />
                <Card className="flex-1">
                  <CardContent className="p-3">
                    <div className="flex items-center gap-2 flex-wrap">
                      <StatusBadge status={event.event_type} />
                      <span className="text-sm font-medium">{event.entity_type}</span>
                      <span className="text-xs text-muted-foreground font-mono">{event.entity_id.slice(0, 8)}</span>
                      <span className="text-xs text-muted-foreground ml-auto">{formatRelativeTime(event.timestamp)}</span>
                    </div>
                    <div className="mt-1 text-xs text-muted-foreground">
                      by {event.actor_type} ({event.actor_id.slice(0, 8)})
                    </div>
                    {event.note && (
                      <p className="mt-1 text-sm">{event.note}</p>
                    )}
                  </CardContent>
                </Card>
              </div>
            ))}
          </div>
          {total > limit && (
            <DataTablePagination
              offset={offset}
              limit={limit}
              total={total}
              onPageChange={setOffset}
              onPageSizeChange={setPageSize}
            />
          )}
        </>
      )}
    </div>
  );
}
