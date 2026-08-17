import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Users } from 'lucide-react';
import type { AgentPerformance } from '@/types/analytics';

export function AgentPerformanceCard({ data }: { data: AgentPerformance[] }) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center gap-2 space-y-0 pb-2">
        <Users className="h-4 w-4" />
        <CardTitle>Agent Performance</CardTitle>
      </CardHeader>
      <CardContent>
        {data.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-4">No agents yet</p>
        ) : (
          <div className="space-y-3">
            {data.map((a) => (
              <div key={a.agent_id} className="flex items-center justify-between text-sm">
                <div>
                  <span className="font-medium">{a.agent_id}</span>
                  <span className="ml-2 text-muted-foreground">
                    {a.total_claims} claims
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-muted-foreground">
                    {a.success_rate}%
                  </span>
                  {a.avg_hours !== null && (
                    <span className="text-xs text-muted-foreground">
                      {a.avg_hours}h avg
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
