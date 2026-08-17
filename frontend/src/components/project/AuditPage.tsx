import { useState, useMemo } from 'react';
import { useAuditEvents } from '@/hooks/use-audit';
import { useProjectId } from '@/hooks/use-project-id';
import { useUrlPagination } from '@/hooks/use-url-pagination';
import { Card, CardContent } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { PageSkeleton } from '@/components/ui/PageSkeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { DataTablePagination } from '@/components/ui/DataTablePagination';
import { formatRelativeTime } from '@/lib/format';
import { ScrollText, Download } from 'lucide-react';
import { exportAuditCsv } from '@/lib/api';
import { showToast } from '@/lib/toast';
import { Button } from '@/components/ui/button';
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
  const [searchQuery, setSearchQuery] = useState('');

  const { data, isLoading, error } = useAuditEvents(
    {
      project_id: projectId,
      ...(eventType ? { event_type: eventType } : {}),
      ...(entityType ? { entity_type: entityType } : {}),
    },
    { offset, limit }
  );

  const events = useMemo(() => data?.items ?? [], [data]);
  const total = data?.total ?? 0;

  const filteredEvents = useMemo(() => {
    if (!searchQuery) return events;
    const q = searchQuery.toLowerCase();
    return events.filter(
      (e) =>
        e.entity_type.toLowerCase().includes(q) ||
        e.event_type.toLowerCase().includes(q) ||
        e.note?.toLowerCase().includes(q) ||
        e.actor_type.toLowerCase().includes(q),
    );
  }, [events, searchQuery]);

  if (isLoading) return <PageSkeleton rows={8} />;
  if (error) return <ErrorState message="Failed to load audit events" />;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <ScrollText className="h-5 w-5" />
        <h2 className="text-lg font-semibold">Audit Log</h2>
      </div>

      <div className="flex items-center gap-3">
        <Input
          type="search"
          placeholder="Search events..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="h-9 w-[200px]"
        />
        <Button
          size="sm"
          variant="outline"
          className="h-9"
          onClick={async () => {
            try {
              const csv = await exportAuditCsv(projectId);
              const blob = new Blob([csv], { type: 'text/csv' });
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = `audit-${projectId}.csv`;
              a.click();
              URL.revokeObjectURL(url);
              showToast.success('Audit exported');
            } catch {
              showToast.error('Export failed');
            }
          }}
        >
          <Download className="mr-1 h-3 w-3" />
          Export CSV
        </Button>
        <Select value={eventType} onValueChange={(v) => setEventType(v ?? '')}>
          <SelectTrigger className="h-9 w-[160px]">
            <SelectValue placeholder="All event types" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="created">Created</SelectItem>
            <SelectItem value="updated">Updated</SelectItem>
            <SelectItem value="deleted">Deleted</SelectItem>
          </SelectContent>
        </Select>
        <Select value={entityType} onValueChange={(v) => setEntityType(v ?? '')}>
          <SelectTrigger className="h-9 w-[160px]">
            <SelectValue placeholder="All entity types" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="project">Project</SelectItem>
            <SelectItem value="component">Component</SelectItem>
            <SelectItem value="module">Module</SelectItem>
            <SelectItem value="feature">Feature</SelectItem>
            <SelectItem value="task">Task</SelectItem>
            <SelectItem value="subtask">Subtask</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {!filteredEvents.length ? (
        <Card>
          <CardContent className="py-8 text-center text-muted-foreground">
            {searchQuery ? 'No events match your search.' : 'No audit events found.'}
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="relative space-y-0">
            <div className="absolute left-[15px] top-0 bottom-0 w-px bg-border" />
            {filteredEvents.map((event: AuditEvent) => (
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
