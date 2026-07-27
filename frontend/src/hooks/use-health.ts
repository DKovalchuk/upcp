import { useQuery } from '@tanstack/react-query';
import { fetchHealth } from '@/lib/api';

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: fetchHealth,
    refetchInterval: 30000, // Refetch every 30 seconds
  });
}
