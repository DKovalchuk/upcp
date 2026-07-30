import { useQuery } from '@tanstack/react-query';
import { fetchDashboardStats, fetchAgentActivity } from '@/lib/api';

export function useDashboardStats() {
  return useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: fetchDashboardStats,
    refetchInterval: 60000,
  });
}

export function useAgentActivity() {
  return useQuery({
    queryKey: ['agent-activity'],
    queryFn: fetchAgentActivity,
    refetchInterval: 30000,
  });
}
