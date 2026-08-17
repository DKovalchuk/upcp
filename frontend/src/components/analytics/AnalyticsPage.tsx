import { useState } from 'react';
import { useProjectId } from '@/hooks/use-project-id';
import { useProjectTrends, useProjectVelocity, useAgentsOverview } from '@/hooks/use-analytics';
import { TrendChart } from './TrendChart';
import { VelocityChart } from './VelocityChart';
import { AgentPerformanceCard } from './AgentPerformanceCard';
import { PageSkeleton } from '@/components/ui/PageSkeleton';
import { BarChart3 } from 'lucide-react';

export function AnalyticsPage() {
  const projectId = useProjectId();
  const [weeks] = useState(8);

  const { data: trendsData, isLoading: trendsLoading } = useProjectTrends(projectId, weeks);
  const { data: velocityData, isLoading: velocityLoading } = useProjectVelocity(projectId, weeks);
  const { data: agentsData, isLoading: agentsLoading } = useAgentsOverview();

  if (trendsLoading || velocityLoading || agentsLoading) {
    return <PageSkeleton hasCards cardCount={3} />;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <BarChart3 className="h-5 w-5" />
        <h2 className="text-lg font-semibold">Analytics</h2>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <TrendChart data={trendsData?.items ?? []} />
        <VelocityChart data={velocityData?.items ?? []} />
      </div>

      <AgentPerformanceCard data={agentsData?.items ?? []} />
    </div>
  );
}
