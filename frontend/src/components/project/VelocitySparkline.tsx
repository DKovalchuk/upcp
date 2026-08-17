import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { TrendingUp } from 'lucide-react';
import { fetchProjectTasks } from '@/lib/api';

export function VelocitySparkline({ projectId }: { projectId: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ['project-tasks', projectId],
    queryFn: () => fetchProjectTasks(projectId),
    enabled: !!projectId,
  });

  const weeklyData = useMemo(() => {
    const tasks = data?.items ?? [];
    const now = new Date();
    const weeks: { label: string; count: number }[] = [];

    for (let i = 7; i >= 0; i--) {
      const weekStart = new Date(now);
      weekStart.setDate(now.getDate() - (i * 7 + now.getDay()));
      weekStart.setHours(0, 0, 0, 0);
      const weekEnd = new Date(weekStart);
      weekEnd.setDate(weekStart.getDate() + 7);

      const count = tasks.filter((t) => {
        if (t.status !== 'done' || !t.updated_at) return false;
        const d = new Date(t.updated_at);
        return d >= weekStart && d < weekEnd;
      }).length;

      const label = weekStart.toLocaleDateString('en', { month: 'short', day: 'numeric' });
      weeks.push({ label, count });
    }

    return weeks;
  }, [data]);

  const max = Math.max(...weeklyData.map((w) => w.count), 1);

  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="h-[100px] w-full animate-pulse rounded bg-muted" />
        </CardContent>
      </Card>
    );
  }

  const chartWidth = 280;
  const chartHeight = 80;
  const barWidth = chartWidth / weeklyData.length - 4;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center gap-2 space-y-0 pb-2">
        <TrendingUp className="h-4 w-4" />
        <CardTitle>Velocity (8 weeks)</CardTitle>
      </CardHeader>
      <CardContent>
        <svg
          width="100%"
          viewBox={`0 0 ${chartWidth} ${chartHeight + 20}`}
          className="overflow-visible"
        >
          {weeklyData.map((week, i) => {
            const barHeight = (week.count / max) * chartHeight;
            const x = i * (chartWidth / weeklyData.length) + 2;
            const y = chartHeight - barHeight;
            return (
              <g key={week.label}>
                <rect
                  x={x}
                  y={y}
                  width={barWidth}
                  height={barHeight}
                  rx={2}
                  className="fill-primary/80"
                />
                {i % 2 === 0 && (
                  <text
                    x={x + barWidth / 2}
                    y={chartHeight + 14}
                    textAnchor="middle"
                    className="fill-muted-foreground text-[8px]"
                  >
                    {week.label}
                  </text>
                )}
              </g>
            );
          })}
        </svg>
      </CardContent>
    </Card>
  );
}
