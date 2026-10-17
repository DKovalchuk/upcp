import { useNavigate } from '@tanstack/react-router';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface StatusCount {
  backlog?: number;
  in_progress?: number;
  review?: number;
  done?: number;
  blocked?: number;
}

const STATUS_COLORS: Record<string, string> = {
  backlog: '#94a3b8',
  in_progress: '#3b82f6',
  review: '#f59e0b',
  done: '#10b981',
  blocked: '#ef4444',
};

const STATUS_LABELS: Record<string, string> = {
  backlog: 'Backlog',
  in_progress: 'In Progress',
  review: 'Review',
  done: 'Done',
  blocked: 'Blocked',
};

interface ChartDatum {
  name: string;
  value: number;
  status: string;
}

export function TaskDistributionDonut({ counts, deliveryBase }: { counts?: StatusCount; deliveryBase?: string }) {
  const navigate = useNavigate();

  const data: ChartDatum[] = Object.entries(counts ?? {})
    .filter(([, v]) => (v ?? 0) > 0)
    .map(([k, v]) => ({
      name: STATUS_LABELS[k] ?? k,
      value: v ?? 0,
      status: k,
    }));

  const total = data.reduce((sum, d) => sum + d.value, 0);

  if (total === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
            Task Distribution
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex h-48 items-center justify-center text-sm text-muted-foreground">
            No tasks yet
          </div>
        </CardContent>
      </Card>
    );
  }

  const handleClick = (status?: string) => {
    const base = deliveryBase ?? '/projects';
    if (deliveryBase && status) {
      navigate({ to: base, search: { status } });
    } else {
      navigate({ to: base });
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
          Task Distribution
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-4">
          <div className="relative h-40 w-40 shrink-0">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data}
                  cx="50%"
                  cy="50%"
                  innerRadius={45}
                  outerRadius={70}
                  paddingAngle={2}
                  dataKey="value"
                  onClick={(datum: unknown) => {
                    const d = datum as { status?: string; payload?: { status?: string } } | null;
                    handleClick(d?.status ?? d?.payload?.status);
                  }}
                  style={{ cursor: 'pointer' }}
                >
                  {data.map((d) => (
                    <Cell
                      key={d.status}
                      fill={STATUS_COLORS[d.status] ?? '#6b7280'}
                      stroke="transparent"
                      aria-label={`${d.name}: ${d.value} tasks, click to filter`}
                    />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value: number, name: string) => [
                    `${value} tasks`,
                    name,
                  ]}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-2xl font-bold">{total}</span>
              <span className="text-[10px] text-muted-foreground">tasks</span>
            </div>
          </div>
          <div className="flex flex-col gap-1.5 text-sm">
            {data.map((d) => (
              <button
                key={d.status}
                onClick={() => handleClick(d.status)}
                className="flex items-center gap-2 rounded px-1 py-0.5 text-left transition-colors hover:bg-muted/50"
              >
                <span
                  className="h-2.5 w-2.5 rounded-full shrink-0"
                  style={{ backgroundColor: STATUS_COLORS[d.status] }}
                />
                <span className="text-muted-foreground">{d.name}</span>
                <span className="ml-auto font-medium">{d.value}</span>
              </button>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
