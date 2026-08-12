import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { TrendingUp } from 'lucide-react';
import type { VelocityData } from '@/types/analytics';

export function VelocityChart({ data }: { data: VelocityData[] }) {
  const max = Math.max(...data.map((d) => d.count), 1);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center gap-2 space-y-0 pb-2">
        <TrendingUp className="h-4 w-4" />
        <CardTitle>Velocity</CardTitle>
      </CardHeader>
      <CardContent>
        {data.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-4">No data</p>
        ) : (
          <div className="flex items-end gap-1 h-32">
            {data.map((d) => (
              <div key={d.week} className="flex-1 flex flex-col items-center gap-0.5">
                <div
                  className="w-full rounded-t bg-primary"
                  style={{ height: `${(d.count / max) * 100}%`, minHeight: d.count > 0 ? '4px' : '0' }}
                  title={`${d.count} tasks`}
                />
                <span className="text-[8px] text-muted-foreground truncate w-full text-center">
                  {d.week.split('-')[1]}
                </span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
