import { PRIORITY_COLORS, PRIORITY_LABELS } from '@/lib/constants';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';

interface PriorityDotProps {
  priority: string;
}

export function PriorityDot({ priority }: PriorityDotProps) {
  const color = PRIORITY_COLORS[priority] || PRIORITY_COLORS.P3;
  const label = PRIORITY_LABELS[priority] || priority;

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
