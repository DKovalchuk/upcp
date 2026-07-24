import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchAuditEvents, createAuditEvent } from '@/lib/api';
import type { AuditEventCreate } from '@/types/audit';

interface AuditFilters {
  project_id: string;
  event_type?: string;
  entity_type?: string;
  date_from?: string;
  date_to?: string;
}

export function useAuditEvents(
  filters?: AuditFilters,
  pagination?: { offset?: number; limit?: number }
) {
  const params: Record<string, string> = {};
  if (filters?.event_type) params.event_type = filters.event_type;
  if (filters?.entity_type) params.entity_type = filters.entity_type;
  if (filters?.date_from) params.date_from = filters.date_from;
  if (filters?.date_to) params.date_to = filters.date_to;

  const projectId = filters?.project_id ?? '';

  return useQuery({
    queryKey: ['audit-events', projectId, params, pagination],
    queryFn: () => fetchAuditEvents(projectId, params, pagination),
    enabled: !!projectId,
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
