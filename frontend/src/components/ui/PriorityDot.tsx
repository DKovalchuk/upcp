import { PRIORITY_COLORS, PRIORITY_LABELS } from '@/lib/constants';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';

interface PriorityDotProps {
  priority: number;
}

function getClosestPriority(priority: number): number {
  if (priority <= 0) return 0;
  if (priority <= 1) return 1;
  if (priority <= 2) return 2;
  return 3;
}

export function PriorityDot({ priority }: PriorityDotProps) {
  const mapped = getClosestPriority(priority);
  const color = PRIORITY_COLORS[mapped] ?? PRIORITY_COLORS[3];
  const label = PRIORITY_LABELS[mapped] ?? `P${priority}`;

  return (
    <Tooltip>
      <TooltipTrigger>
        <div className={`h-2.5 w-2.5 rounded-full ${color}`} />
      </TooltipTrigger>
      <TooltipContent>
        <p>{label}</p>
      </TooltipContent>
    </Tooltip>
  );
}
