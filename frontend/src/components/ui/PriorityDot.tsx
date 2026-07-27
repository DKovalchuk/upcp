import { PRIORITY_COLORS, PRIORITY_LABELS } from '@/lib/constants';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';

interface PriorityDotProps {
  priority: number;
  showLabel?: boolean;
  size?: 'sm' | 'default';
}

function getClosestPriority(priority: number): number {
  if (priority <= 0) return 0;
  if (priority <= 1) return 1;
  if (priority <= 2) return 2;
  return 3;
}

export function PriorityDot({ priority, showLabel = false, size = 'default' }: PriorityDotProps) {
  const mapped = getClosestPriority(priority);
  const colors = PRIORITY_COLORS[mapped] ?? PRIORITY_COLORS[3];
  const label = PRIORITY_LABELS[mapped] ?? `P${priority}`;
  const dotSize = size === 'sm' ? 'h-2 w-2' : 'h-2.5 w-2.5';

  return (
    <Tooltip>
      <TooltipTrigger render={<span className="inline-flex items-center gap-1.5" />}>
        <span
          role="img"
          aria-label={`Priority: ${label}`}
          className={`inline-block ${dotSize} rounded-full ${colors.dot}`}
          tabIndex={0}
        />
        {showLabel && (
          <span className={`text-xs ${colors.text}`}>{label}</span>
        )}
      </TooltipTrigger>
      <TooltipContent>
        <p>{label}</p>
      </TooltipContent>
    </Tooltip>
  );
}
