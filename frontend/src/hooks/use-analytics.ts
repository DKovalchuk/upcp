import { useQuery } from '@tanstack/react-query';
import {
  fetchProjectTrends,
  fetchProjectVelocity,
  fetchHealthHistory,
  fetchAgentsOverview,
  fetchGlobalVelocity,
  fetchNotificationChannels,
} from '@/lib/api/analytics';

export function useProjectTrends(projectId: string, weeks = 8) {
  return useQuery({
    queryKey: ['analytics', 'trends', projectId, weeks],
    queryFn: () => fetchProjectTrends(projectId, weeks),
    enabled: !!projectId,
  });
}

export function useProjectVelocity(projectId: string, weeks = 8) {
  return useQuery({
    queryKey: ['analytics', 'velocity', projectId, weeks],
    queryFn: () => fetchProjectVelocity(projectId, weeks),
    enabled: !!projectId,
  });
}

export function useHealthHistory(projectId: string, days = 30) {
  return useQuery({
    queryKey: ['analytics', 'health', projectId, days],
    queryFn: () => fetchHealthHistory(projectId, days),
    enabled: !!projectId,
  });
}

export function useAgentsOverview() {
  return useQuery({
    queryKey: ['analytics', 'agents-overview'],
    queryFn: fetchAgentsOverview,
  });
}

export function useGlobalVelocity(weeks = 8, projectId?: string) {
  return useQuery({
    queryKey: ['analytics', 'global-velocity', weeks, projectId],
    queryFn: () => fetchGlobalVelocity(weeks, projectId),
    staleTime: 30_000,
  });
}

export function useNotificationChannels() {
  return useQuery({
    queryKey: ['notification-channels'],
    queryFn: fetchNotificationChannels,
  });
}
