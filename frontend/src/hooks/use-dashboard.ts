import { useQuery } from '@tanstack/react-query';
import { fetchDashboardStats, fetchAgentActivity, fetchPortfolioOverview } from '@/lib/api';

export function useDashboardStats(projectId?: string) {
  return useQuery({
    queryKey: ['dashboard-stats', projectId],
    queryFn: () => fetchDashboardStats(projectId),
    refetchInterval: 60_000,
    staleTime: 60_000,
  });
}

export function useAgentActivity() {
  return useQuery({
    queryKey: ['agent-activity'],
    queryFn: fetchAgentActivity,
    refetchInterval: 30_000,
    staleTime: 30_000,
  });
}

export function usePortfolioOverview() {
  return useQuery({
    queryKey: ['portfolio-overview'],
    queryFn: fetchPortfolioOverview,
    staleTime: 60_000,
  });
}
