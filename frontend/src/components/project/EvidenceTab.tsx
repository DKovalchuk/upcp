// Dedicated Evidence Tab — TASK-0099 Sprint 3

import { useTaskEvidence } from '@/hooks/use-task-execution';
import { EmptyState } from '@/components/ui/EmptyState';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { formatRelativeTime } from '@/lib/format';
import { ExternalLink, FileText } from 'lucide-react';

interface EvidenceTabProps {
  taskId: string;
}

const EVIDENCE_TYPE_ICONS: Record<string, typeof FileText> = {
  test_output: FileText,
  screenshot: FileText,
  log: FileText,
  url: ExternalLink,
  file: FileText,
  metric: FileText,
  custom: FileText,
};

export function EvidenceTab({ taskId }: EvidenceTabProps) {
  const { data: evidence, isLoading } = useTaskEvidence(taskId);
  const items = evidence ?? [];

  if (isLoading) {
    return <div className="text-sm text-muted-foreground">Loading...</div>;
  }

  if (items.length === 0) {
    return (
      <EmptyState
        icon={FileText}
        title="No evidence"
        description="No evidence has been attached to this task yet"
      />
    );
  }

  return (
    <div className="space-y-3">
      {items.map((e) => {
        const Icon = EVIDENCE_TYPE_ICONS[e.type] ?? FileText;
        return (
          <div key={e.id} className="rounded-md border p-3">
            <div className="flex items-start gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-muted">
                <Icon className="h-4 w-4 text-muted-foreground" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h4 className="text-sm font-medium">{e.title}</h4>
                  <StatusBadge status={e.verification_state} />
                </div>
                {e.description && (
                  <p className="mt-1 text-sm text-muted-foreground line-clamp-2">
                    {e.description}
                  </p>
                )}
                {e.url && (
                  <a
                    href={e.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-1 inline-flex items-center gap-1 text-xs text-blue-600 hover:underline dark:text-blue-400"
                  >
                    <ExternalLink className="h-3 w-3" />
                    {e.url.length > 50 ? e.url.slice(0, 50) + '...' : e.url}
                  </a>
                )}
                {e.content_snippet && (
                  <pre className="mt-2 max-h-24 overflow-auto rounded bg-muted p-2 text-xs">
                    {e.content_snippet}
                  </pre>
                )}
                <p className="mt-1 text-xs text-muted-foreground">
                  {formatRelativeTime(e.created_at)}
                  {e.created_by_id && <span> by {e.created_by_id}</span>}
                </p>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
