import type { AuditEvent, AuditEventCreate } from '@/types/audit';
import type { PaginatedResponse } from '@/types/api';
import { apiRequest } from './client';

export async function fetchAuditEvents(
  projectId: string,
  filters?: Record<string, string>,
  pagination?: { offset?: number; limit?: number }
): Promise<PaginatedResponse<AuditEvent>> {
  const params = new URLSearchParams(filters);
  if (pagination?.offset !== undefined) params.set('offset', String(pagination.offset));
  if (pagination?.limit !== undefined) params.set('limit', String(pagination.limit));
  const qs = params.toString();
  const url = qs
    ? `/api/v1/projects/${projectId}/audit-events?${qs}`
    : `/api/v1/projects/${projectId}/audit-events`;
  return apiRequest<PaginatedResponse<AuditEvent>>(url);
}

export async function createAuditEvent(data: AuditEventCreate): Promise<AuditEvent> {
  return apiRequest<AuditEvent>('/api/v1/audit-events', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}
