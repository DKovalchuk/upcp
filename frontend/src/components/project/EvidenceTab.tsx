// Dedicated Evidence Tab — TASK-0099 Sprint 4 + TASK-0116 file uploads

import { useState, useCallback, useRef } from 'react';
import { useTaskEvidence } from '@/hooks/use-task-execution';
import { useCreateEvidence, useAcceptEvidence, useRejectEvidence, useUploadEvidenceFile } from '@/hooks/use-quality';
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
import { ExternalLink, FileText, Plus, CheckCircle, XCircle, Upload, File, Image, X } from 'lucide-react';

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

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const ALLOWED_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.pdf', '.txt', '.md', '.csv', '.py', '.ts', '.js', '.json', '.xml', '.svg'];

function isAllowedFile(file: File): boolean {
  const ext = '.' + file.name.split('.').pop()?.toLowerCase();
  return ALLOWED_EXTENSIONS.includes(ext);
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getFileIcon(fileName: string) {
  const ext = fileName.split('.').pop()?.toLowerCase();
  if (['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'].includes(ext ?? '')) return Image;
  return File;
}

export function EvidenceTab({ taskId }: EvidenceTabProps) {
  const { data: evidence, isLoading } = useTaskEvidence(taskId);
  const createEvidence = useCreateEvidence(taskId);
  const uploadFile = useUploadEvidenceFile(taskId);
  const acceptEvidence = useAcceptEvidence(taskId);
  const rejectEvidence = useRejectEvidence(taskId);

  const [showAttach, setShowAttach] = useState(false);
  const [title, setTitle] = useState('');
  const [type, setType] = useState('test_output');
  const [description, setDescription] = useState('');
  const [url, setUrl] = useState('');
  const [dragOver, setDragOver] = useState(false);
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

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

  const handleFileSelect = useCallback((file: File) => {
    if (!isAllowedFile(file)) {
      showToast.error('File type not allowed');
      return;
    }
    if (file.size > MAX_FILE_SIZE) {
      showToast.error(`File too large (max ${formatFileSize(MAX_FILE_SIZE)})`);
      return;
    }
    setPendingFile(file);
    setTitle(file.name);
    setType('file');
  }, []);

  const handleUpload = async () => {
    if (!pendingFile || !title.trim()) return;
    await uploadFile.mutateAsync({ file: pendingFile, title: title.trim() });
    showToast.created('Evidence file');
    setPendingFile(null);
    setTitle('');
    setShowAttach(false);
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFileSelect(file);
  }, [handleFileSelect]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback(() => setDragOver(false), []);

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

      {/* Drop zone */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`rounded-md border-2 border-dashed p-4 text-center transition-colors ${
          dragOver
            ? 'border-primary bg-primary/5'
            : 'border-muted-foreground/25 hover:border-muted-foreground/50'
        }`}
      >
        <Upload className="mx-auto h-6 w-6 text-muted-foreground" />
        <p className="mt-1 text-xs text-muted-foreground">
          Drag & drop a file here or{' '}
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="text-primary hover:underline"
          >
            browse
          </button>
        </p>
        <p className="mt-0.5 text-xs text-muted-foreground/60">
          Max {formatFileSize(MAX_FILE_SIZE)} — {ALLOWED_EXTENSIONS.join(', ')}
        </p>
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept={ALLOWED_EXTENSIONS.join(',')}
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFileSelect(file);
            e.target.value = '';
          }}
        />
      </div>

      {/* Pending file preview */}
      {pendingFile && (
        <div className="flex items-center gap-2 rounded-md border p-2">
          {(() => { const Icon = getFileIcon(pendingFile.name); return <Icon className="h-4 w-4 text-muted-foreground" />; })()}
          <span className="flex-1 truncate text-sm">{pendingFile.name}</span>
          <span className="text-xs text-muted-foreground">{formatFileSize(pendingFile.size)}</span>
          <Button
            size="sm"
            variant="ghost"
            className="h-6 w-6 p-0"
            onClick={() => { setPendingFile(null); setTitle(''); }}
          >
            <X className="h-3 w-3" />
          </Button>
          <Button
            size="sm"
            onClick={handleUpload}
            disabled={!title.trim() || uploadFile.isPending}
          >
            {uploadFile.isPending ? 'Uploading...' : 'Upload'}
          </Button>
        </div>
      )}

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

      {items.length === 0 && !showAttach && !pendingFile ? (
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
                  {e.file_name && (
                    <span className="text-xs text-muted-foreground">
                      ({e.file_name}{e.file_size ? ` — ${formatFileSize(e.file_size)}` : ''})
                    </span>
                  )}
                </div>
                {e.description && <p className="mt-1 text-sm text-muted-foreground line-clamp-2">{e.description}</p>}
                {e.url && (
                  <a href={e.url} target="_blank" rel="noopener noreferrer" className="mt-1 inline-flex items-center gap-1 text-xs text-blue-600 hover:underline dark:text-blue-400">
                    <ExternalLink className="h-3 w-3" />
                    {e.url.length > 50 ? e.url.slice(0, 50) + '...' : e.url}
                  </a>
                )}
                {e.file_name && (
                  <a
                    href={`/api/v1/evidence/${e.id}/download`}
                    className="mt-1 inline-flex items-center gap-1 text-xs text-blue-600 hover:underline dark:text-blue-400"
                    download
                  >
                    <File className="h-3 w-3" />
                    Download {e.file_name}
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
