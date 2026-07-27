import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { EmptyState } from '@/components/ui/EmptyState';
import { Bot } from 'lucide-react';

export function AgentActivitySummary() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <div className="relative">
            <Bot className="h-4 w-4" />
            <span className="absolute -top-0.5 -right-0.5 h-2 w-2 rounded-full bg-emerald-500 animate-heartbeat-pulse" />
          </div>
          Active Agents
        </CardTitle>
      </CardHeader>
      <CardContent>
        <EmptyState
          icon={Bot}
          title="No active agents"
          description="Agent activity will appear here when tasks are running."
        />
      </CardContent>
    </Card>
  );
}
