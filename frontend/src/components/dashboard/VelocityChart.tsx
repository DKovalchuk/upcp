import { useNavigate } from '@tanstack/react-router';
import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface VelocityDataPoint {
  week: string;
  count: number;
}

export function VelocityChart({
  data,
  isLoading,
}: {
  data?: VelocityDataPoint[];
  isLoading?: boolean;
}) {
  const navigate = useNavigate();

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
            Velocity (8 weeks)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex h-48 items-center justify-center">
            <div className="h-4 w-32 animate-pulse rounded bg-muted" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!data || data.length === 0 || data.every((d) => d.count === 0)) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
            Velocity (8 weeks)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex h-48 items-center justify-center text-sm text-muted-foreground">
            No completed tasks yet
          </div>
        </CardContent>
      </Card>
    );
  }

  const handleClick = (chartData: any) => {
    if (chartData?.activePayload?.[0]) {
      const week = chartData.activePayload[0].payload.week;
      navigate({ to: `/delivery?status=done&week=${week}` });
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
          Velocity (8 weeks)
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={data}
              onClick={handleClick}
              style={{ cursor: 'pointer' }}
              margin={{ top: 5, right: 10, left: -20, bottom: 0 }}
            >
              <defs>
                <linearGradient id="velocityGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                dataKey="week"
                tickFormatter={(v: string) => v.split('-')[1] ?? v}
                className="text-xs"
                tick={{ fontSize: 11 }}
              />
              <YAxis allowDecimals={false} className="text-xs" tick={{ fontSize: 11 }} />
              <Tooltip
                formatter={(value: number) => [`${value} tasks`, 'Completed']}
                labelFormatter={(label: string) => `Week ${label}`}
                contentStyle={{
                  borderRadius: '8px',
                  border: '1px solid hsl(var(--border))',
                  backgroundColor: 'hsl(var(--card))',
                  fontSize: '12px',
                }}
              />
              <Area
                type="monotone"
                dataKey="count"
                stroke="#3b82f6"
                strokeWidth={2}
                fill="url(#velocityGradient)"
                dot={{ r: 4, fill: '#3b82f6', strokeWidth: 0 }}
                activeDot={{ r: 6, fill: '#3b82f6' }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
