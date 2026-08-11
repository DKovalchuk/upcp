// Dedicated Evidence Tab — TASK-0099 Sprint 4

import { useState } from 'react';
import { useTaskEvidence } from '@/hooks/use-task-execution';
import { useCreateEvidence, useAcceptEvidence, useRejectEvidence } from '@/hooks/use-quality';
import { EmptyState } from '@/components/ui/EmptyState';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { formatRelativeTime } from '@/lib/format';
import { showToast } from '@/lib/toast';
import { ExternalLink, FileText, Plus, CheckCircle, XCircle } from 'lucide-react';

interface EvidenceTabProps {
  taskId: string;
}

const EVIDENCE_TYPES = [
  { value: 'test_output', label: 'Test Output' },
  { value: 'screenshot', label: 'Screenshot' },
  { value: 'log', label: 'Log' },
  { value: 'url', label: 'URL' },
  { value: 'file', label: 'File' },
  { value: 'metric', label: 'Metric' },
  { value: 'custom', label: 'Custom' },
];

export function EvidenceTab({ taskId }: EvidenceTabProps) {
  const { data: evidence, isLoading } = useTaskEvidence(taskId);
  const createEvidence = useCreateEvidence(taskId);
  const acceptEvidence = useAcceptEvidence(taskId);
  const rejectEvidence = useRejectEvidence(taskId);

  const [showAttach, setShowAttach] = useState(false);
  const [title, setTitle] = useState('');
  const [type, setType] = useState('test_output');
  const [description, setDescription] = useState('');
  const [url, setUrl] = useState('');

  const items = evidence?.items ?? [];

  const handleAttach = async () => {
    if (!title.trim()) return;
    await createEvidence.mutateAsync({
      title: title.trim(),
      type,
      description: description.trim() || undefined,
      url: url.trim() || undefined,
    });
    showToast.created('Evidence');
    setShowAttach(false);
    setTitle('');
    setDescription('');
    setUrl('');
  };

  if (isLoading) {
    return <div className="text-sm text-muted-foreground">Loading...</div>;
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium">Evidence ({items.length})</h4>
        <Button size="sm" variant="outline" onClick={() => setShowAttach(!showAttach)}>
          <Plus className="mr-1 h-3 w-3" />
          Attach
        </Button>
      </div>

      {showAttach && (
        <div className="rounded-md border p-3 space-y-2">
          <Input placeholder="Evidence title" value={title} onChange={(e) => setTitle(e.target.value)} className="h-8 text-sm" />
          <Select value={type} onValueChange={(v) => setType(v ?? 'test_output')}>
            <SelectTrigger className="h-8"><SelectValue /></SelectTrigger>
            <SelectContent>
              {EVIDENCE_TYPES.map((t) => (
                <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Input placeholder="Description (optional)" value={description} onChange={(e) => setDescription(e.target.value)} className="h-8 text-sm" />
          <Input placeholder="URL (optional)" value={url} onChange={(e) => setUrl(e.target.value)} className="h-8 text-sm" />
          <div className="flex gap-2">
            <Button size="sm" onClick={handleAttach} disabled={!title.trim() || createEvidence.isPending}>
              {createEvidence.isPending ? 'Attaching...' : 'Attach'}
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setShowAttach(false)}>Cancel</Button>
          </div>
        </div>
      )}

      {items.length === 0 && !showAttach ? (
        <EmptyState icon={FileText} title="No evidence" description="No evidence has been attached to this task yet" />
      ) : (
        items.map((e) => (
          <div key={e.id} className="rounded-md border p-3">
            <div className="flex items-start gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-muted">
                <FileText className="h-4 w-4 text-muted-foreground" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h4 className="text-sm font-medium">{e.title}</h4>
                  <StatusBadge status={e.verification_state} />
                </div>
                {e.description && <p className="mt-1 text-sm text-muted-foreground line-clamp-2">{e.description}</p>}
                {e.url && (
                  <a href={e.url} target="_blank" rel="noopener noreferrer" className="mt-1 inline-flex items-center gap-1 text-xs text-blue-600 hover:underline dark:text-blue-400">
                    <ExternalLink className="h-3 w-3" />
                    {e.url.length > 50 ? e.url.slice(0, 50) + '...' : e.url}
                  </a>
                )}
                {e.content_snippet && <pre className="mt-2 max-h-24 overflow-auto rounded bg-muted p-2 text-xs">{e.content_snippet}</pre>}
                <p className="mt-1 text-xs text-muted-foreground">
                  {formatRelativeTime(e.created_at)}
                  {e.created_by_id && <span> by {e.created_by_id}</span>}
                </p>
              </div>
              {e.verification_state === 'unverified' && (
                <div className="flex gap-1">
                  <Button size="sm" variant="outline" className="h-7 text-xs"
                    onClick={() => acceptEvidence.mutate(e.id, { onSuccess: () => showToast.updated('Evidence') })}
                    disabled={acceptEvidence.isPending}>
                    <CheckCircle className="mr-1 h-3 w-3" /> Accept
                  </Button>
                  <Button size="sm" variant="outline" className="h-7 text-xs text-destructive hover:text-destructive"
                    onClick={() => rejectEvidence.mutate({ evidenceId: e.id }, { onSuccess: () => showToast.updated('Evidence') })}
                    disabled={rejectEvidence.isPending}>
                    <XCircle className="mr-1 h-3 w-3" /> Reject
                  </Button>
                </div>
              )}
            </div>
          </div>
        ))
      )}
    </div>
  );
}
