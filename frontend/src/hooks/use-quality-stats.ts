import { useQuery } from '@tanstack/react-query';
import { fetchQualityStats } from '@/lib/api';

export function useQualityStats(projectId: string) {
  return useQuery({
    queryKey: ['quality-stats', projectId],
    queryFn: () => fetchQualityStats(projectId),
    enabled: !!projectId,
  });
}
