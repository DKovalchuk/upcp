import type { TrendData, VelocityData, HealthHistoryData, AgentPerformance } from '@/types/analytics';
import { apiRequest } from './client';

export async function fetchProjectTrends(
  projectId: string,
  weeks = 8
): Promise<{ items: TrendData[] }> {
  return apiRequest(`/api/v1/analytics/project/${projectId}/trends?weeks=${weeks}`);
}

export async function fetchProjectVelocity(
  projectId: string,
  weeks = 8
): Promise<{ items: VelocityData[] }> {
  return apiRequest(`/api/v1/analytics/project/${projectId}/velocity?weeks=${weeks}`);
}

export async function fetchHealthHistory(
  projectId: string,
  days = 30
): Promise<{ items: HealthHistoryData[] }> {
  return apiRequest(`/api/v1/analytics/project/${projectId}/health-history?days=${days}`);
}

export async function fetchAgentPerformance(
  agentId: string
): Promise<{ items: AgentPerformance[] }> {
  return apiRequest(`/api/v1/analytics/agent/${agentId}/performance`);
}

export async function fetchAgentsOverview(): Promise<{ items: AgentPerformance[] }> {
  return apiRequest('/api/v1/analytics/agents/overview');
}

export async function fetchGlobalVelocity(
  weeks = 8,
  projectId?: string,
): Promise<{ items: { week: string; count: number }[] }> {
  const params = new URLSearchParams({ weeks: String(weeks) });
  if (projectId) params.set('project_id', projectId);
  return apiRequest(`/api/v1/analytics/velocity?${params}`);
}

export async function fetchNotificationChannels(): Promise<{ items: Array<{
  id: string;
  channel_type: string;
  name: string;
  config: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}> }> {
  return apiRequest('/api/v1/notification-channels');
}

export async function createNotificationChannel(data: {
  channel_type: string;
  name: string;
  config: Record<string, unknown>;
}): Promise<{ id: string }> {
  return apiRequest('/api/v1/notification-channels', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateNotificationChannel(
  id: string,
  data: { name?: string; config?: Record<string, unknown> }
): Promise<{ id: string }> {
  return apiRequest(`/api/v1/notification-channels/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function deleteNotificationChannel(id: string): Promise<void> {
  await apiRequest(`/api/v1/notification-channels/${id}`, { method: 'DELETE' });
}

export async function toggleNotificationChannel(id: string): Promise<{ is_active: boolean }> {
  return apiRequest(`/api/v1/notification-channels/${id}/toggle`, { method: 'POST' });
}

export async function testNotificationChannel(id: string): Promise<{ status: string }> {
  return apiRequest(`/api/v1/notification-channels/${id}/test`, { method: 'POST' });
}
