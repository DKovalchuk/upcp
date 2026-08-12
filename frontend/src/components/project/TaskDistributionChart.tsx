import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { PieChart } from 'lucide-react';
import { fetchProjectTasks } from '@/lib/api';

const STATUS_CONFIG = {
  done: { label: 'Done', color: '#10b981' },
  'in-progress': { label: 'In Progress', color: '#3b82f6' },
  claimed: { label: 'Claimed', color: '#8b5cf6' },
  review: { label: 'Review', color: '#f59e0b' },
  backlog: { label: 'Backlog', color: '#6b7280' },
  blocked: { label: 'Blocked', color: '#ef4444' },
} as const;

function DonutSegment({
  cx,
  cy,
  radius,
  startAngle,
  endAngle,
  color,
}: {
  cx: number;
  cy: number;
  radius: number;
  startAngle: number;
  endAngle: number;
  color: string;
}) {
  if (endAngle - startAngle >= 359.99) {
    return (
      <circle
        cx={cx}
        cy={cy}
        r={radius}
        fill="none"
        stroke={color}
        strokeWidth="24"
      />
    );
  }

  const startRad = ((startAngle - 90) * Math.PI) / 180;
  const endRad = ((endAngle - 90) * Math.PI) / 180;
  const x1 = cx + radius * Math.cos(startRad);
  const y1 = cy + radius * Math.sin(startRad);
  const x2 = cx + radius * Math.cos(endRad);
  const y2 = cy + radius * Math.sin(endRad);
  const largeArc = endAngle - startAngle > 180 ? 1 : 0;

  return (
    <path
      d={`M ${x1} ${y1} A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2}`}
      fill="none"
      stroke={color}
      strokeWidth="24"
    />
  );
}

export function TaskDistributionChart({ projectId }: { projectId: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ['project-tasks', projectId],
    queryFn: () => fetchProjectTasks(projectId),
    enabled: !!projectId,
  });

  const tasks = data?.items ?? [];

  const distribution = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const task of tasks) {
      const status = task.status || 'backlog';
      counts[status] = (counts[status] || 0) + 1;
    }
    return Object.entries(counts)
      .map(([status, count]) => ({
        status,
        count,
        label: STATUS_CONFIG[status as keyof typeof STATUS_CONFIG]?.label ?? status,
        color: STATUS_CONFIG[status as keyof typeof STATUS_CONFIG]?.color ?? '#6b7280',
      }))
      .sort((a, b) => b.count - a.count);
  }, [tasks]);

  const total = tasks.length;

  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="h-[120px] w-full animate-pulse rounded bg-muted" />
        </CardContent>
      </Card>
    );
  }

  if (total === 0) {
    return (
      <Card>
        <CardHeader className="flex flex-row items-center gap-2 space-y-0 pb-2">
          <PieChart className="h-4 w-4" />
          <CardTitle>Task Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground text-center py-4">No tasks yet</p>
        </CardContent>
      </Card>
    );
  }

  let currentAngle = 0;
  const segments = distribution.map((d) => {
    const angle = (d.count / total) * 360;
    const start = currentAngle;
    currentAngle += angle;
    return { ...d, startAngle: start, endAngle: currentAngle };
  });

  return (
    <Card>
      <CardHeader className="flex flex-row items-center gap-2 space-y-0 pb-2">
        <PieChart className="h-4 w-4" />
        <CardTitle>Task Distribution</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-6">
          <div className="relative">
            <svg width="100" height="100">
              {segments.map((seg) => (
                <DonutSegment
                  key={seg.status}
                  cx={50}
                  cy={50}
                  radius={38}
                  startAngle={seg.startAngle}
                  endAngle={seg.endAngle}
                  color={seg.color}
                />
              ))}
            </svg>
            <span className="absolute inset-0 flex items-center justify-center text-lg font-bold">
              {total}
            </span>
          </div>
          <div className="space-y-1.5 flex-1">
            {segments.map((seg) => (
              <div key={seg.status} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <span
                    className="h-2.5 w-2.5 rounded-full"
                    style={{ backgroundColor: seg.color }}
                  />
                  <span className="text-muted-foreground">{seg.label}</span>
                </div>
                <span className="font-medium">{seg.count}</span>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
