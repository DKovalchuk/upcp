import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchAuditEvents, createAuditEvent } from '@/lib/api';
import type { AuditEventCreate } from '@/types/audit';

export function useAuditEvents(filters?: Record<string, string>) {
  return useQuery({
    queryKey: ['audit-events', filters],
    queryFn: () => fetchAuditEvents(filters),
  });
}

export function useCreateAuditEvent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: AuditEventCreate) => createAuditEvent(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['audit-events'] });
    },
  });
}
