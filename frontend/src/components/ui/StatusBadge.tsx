import { Badge } from '@/components/ui/badge';
import { STATUS_COLORS } from '@/lib/constants';

interface StatusBadgeProps {
  status: string;
  showDot?: boolean;
  size?: 'sm' | 'default';
}

const STATUS_LABELS: Record<string, string> = {
  active: 'Active',
  backlog: 'Backlog',
  'in-progress': 'In Progress',
  in_progress: 'In Progress',
  blocked: 'Blocked',
  done: 'Done',
  cancelled: 'Cancelled',
  paused: 'Paused',
  archived: 'Archived',
  ready: 'Ready',
  needs_clarification: 'Needs Clarification',
  ready_for_review: 'Ready for Review',
  changes_requested: 'Changes Requested',
};

export function StatusBadge({ status, showDot = true, size = 'default' }: StatusBadgeProps) {
  const colors = STATUS_COLORS[status] || STATUS_COLORS.backlog;
  const label = STATUS_LABELS[status] || status;

  return (
    <Badge
      variant="outline"
      className={`${colors.bg} ${colors.text} border-transparent gap-1.5 ${size === 'sm' ? 'h-4 px-1.5 text-[10px]' : ''}`}
    >
      {showDot && (
        <span className={`inline-block h-1.5 w-1.5 rounded-full ${colors.dot}`} />
      )}
      {label}
    </Badge>
  );
}
