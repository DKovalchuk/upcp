import { Badge } from '@/components/ui/badge';
import { STATUS_COLORS } from '@/lib/constants';

interface StatusBadgeProps {
  status: string;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const colors = STATUS_COLORS[status] || STATUS_COLORS.backlog;

  return (
    <Badge
      variant="outline"
      className={`${colors.bg} ${colors.text} border-transparent`}
    >
      {status}
    </Badge>
  );
}
