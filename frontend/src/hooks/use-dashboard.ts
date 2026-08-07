import { useQuery } from '@tanstack/react-query';
import { fetchDashboardStats, fetchAgentActivity } from '@/lib/api';

export function useDashboardStats() {
  return useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: fetchDashboardStats,
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
