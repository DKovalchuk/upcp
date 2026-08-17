import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { BarChart3 } from 'lucide-react';
import type { TrendData } from '@/types/analytics';

export function TrendChart({ data }: { data: TrendData[] }) {
  const max = Math.max(...data.map((d) => Math.max(d.completed, d.created)), 1);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center gap-2 space-y-0 pb-2">
        <BarChart3 className="h-4 w-4" />
        <CardTitle>Task Trends</CardTitle>
      </CardHeader>
      <CardContent>
        {data.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-4">No data</p>
        ) : (
          <div className="flex items-end gap-1 h-32">
            {data.map((d) => (
              <div key={d.week} className="flex-1 flex flex-col items-center gap-0.5">
                <div className="flex gap-0.5 items-end" style={{ height: '100px' }}>
                  <div
                    className="w-2 rounded-t bg-emerald-500"
                    style={{ height: `${(d.completed / max) * 100}%` }}
                    title={`Completed: ${d.completed}`}
                  />
                  <div
                    className="w-2 rounded-t bg-blue-400"
                    style={{ height: `${(d.created / max) * 100}%` }}
                    title={`Created: ${d.created}`}
                  />
                </div>
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
