import { CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import { AgentAvatar } from '@/components/ui/AgentAvatar';
import { Button } from '@/components/ui/button';
import { formatRelativeTime } from '@/lib/format';

interface ReviewVerdictCardProps {
  agentName: string;
  agentAvatarUrl?: string;
  verdict: 'approve' | 'reject' | 'needs_changes';
  confidence?: number;
  findingsCount?: number;
  summary?: string;
  createdAt: string;
  onAccept?: () => void;
  onReject?: () => void;
}

const VERDICT_CONFIG = {
  approve: {
    icon: CheckCircle,
    label: 'Approved',
    color: 'text-emerald-600 dark:text-emerald-400',
    bg: 'bg-emerald-500/10',
  },
  reject: {
    icon: XCircle,
    label: 'Rejected',
    color: 'text-red-600 dark:text-red-400',
    bg: 'bg-red-500/10',
  },
  needs_changes: {
    icon: AlertCircle,
    label: 'Changes Requested',
    color: 'text-amber-600 dark:text-amber-400',
    bg: 'bg-amber-500/10',
  },
};

export function ReviewVerdictCard({
  agentName,
  agentAvatarUrl,
  verdict,
  confidence,
  findingsCount,
  summary,
  createdAt,
  onAccept,
  onReject,
}: ReviewVerdictCardProps) {
  const config = VERDICT_CONFIG[verdict];
  const Icon = config.icon;

  return (
    <div className="rounded-lg border border-border bg-card p-3">
      <div className="flex items-center gap-3">
        <AgentAvatar name={agentName} avatarUrl={agentAvatarUrl} status="working" size="sm" />
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium">{agentName}</span>
            <span className="text-xs text-muted-foreground">reviewed</span>
          </div>
          <p className="text-xs text-muted-foreground">{formatRelativeTime(createdAt)}</p>
        </div>
        <div className={`flex items-center gap-1.5 rounded-md px-2 py-1 ${config.bg}`}>
          <Icon className={`h-3.5 w-3.5 ${config.color}`} />
          <span className={`text-xs font-medium ${config.color}`}>{config.label}</span>
        </div>
      </div>
      {confidence !== undefined && (
        <div className="mt-2 flex items-center gap-2 text-xs text-muted-foreground">
          <span>Confidence:</span>
          <div className="h-1.5 w-16 rounded-full bg-muted">
            <div
              className={`h-full rounded-full ${verdict === 'approve' ? 'bg-emerald-500' : verdict === 'reject' ? 'bg-red-500' : 'bg-amber-500'}`}
              style={{ width: `${Math.min(confidence > 1 ? confidence : confidence * 100, 100)}%` }}
            />
          </div>
          <span>{confidence > 1 ? confidence : Math.round(confidence * 100)}%</span>
        </div>
      )}
      {findingsCount !== undefined && findingsCount > 0 && (
        <p className="mt-1 text-xs text-muted-foreground">{findingsCount} finding{findingsCount === 1 ? '' : 's'}</p>
      )}
      {summary && (
        <p className="mt-2 text-sm text-muted-foreground line-clamp-2">{summary}</p>
      )}
      {(onAccept || onReject) && (
        <div className="mt-3 flex items-center gap-2">
          {onAccept && (
            <Button size="sm" variant="outline" onClick={onAccept} className="h-7 text-xs">
              <CheckCircle className="mr-1 h-3 w-3" />
              Accept
            </Button>
          )}
          {onReject && (
            <Button size="sm" variant="outline" onClick={onReject} className="h-7 text-xs text-destructive hover:text-destructive">
              <XCircle className="mr-1 h-3 w-3" />
              Reject
            </Button>
          )}
        </div>
      )}
    </div>
  );
}
