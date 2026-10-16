import type {
  AgentActivityItem,
  AttentionDashboard,
  Notification,
  PortfolioOverview,
  ProjectHealth,
} from '@/types/dashboard';
import type { DashboardStatsResponse } from '@/types/api';
import { apiRequest } from './client';

// ── Dashboard Stats ──

export async function fetchDashboardStats(projectId?: string): Promise<DashboardStatsResponse> {
  const params = projectId ? `?project_id=${projectId}` : '';
  return apiRequest<DashboardStatsResponse>(`/api/v1/dashboard/stats${params}`);
}

// ── Attention Dashboard ──

export async function fetchAttentionDashboard(projectId?: string): Promise<AttentionDashboard> {
  const params = projectId ? `?project_id=${encodeURIComponent(projectId)}` : '';
  return apiRequest<AttentionDashboard>(`/api/v1/dashboard/attention${params}`);
}

export async function fetchAgentActivity(): Promise<{ items: AgentActivityItem[] }> {
  return apiRequest<{ items: AgentActivityItem[] }>('/api/v1/dashboard/agent-activity');
}

export async function fetchProjectHealth(
  projectId: string
): Promise<ProjectHealth> {
  return apiRequest<ProjectHealth>(`/api/v1/projects/${projectId}/health`);
}

export async function fetchPortfolioOverview(): Promise<PortfolioOverview> {
  return apiRequest<PortfolioOverview>('/api/v1/portfolio/overview');
}

// ── Notifications ──

export async function fetchNotifications(
  unreadOnly = false
): Promise<{ items: Notification[] }> {
  const params = unreadOnly ? '?unread_only=true' : '';
  return apiRequest<{ items: Notification[] }>(`/api/v1/notifications${params}`);
}

export async function fetchUnreadCount(): Promise<{ count: number }> {
  return apiRequest<{ count: number }>('/api/v1/notifications/unread-count');
}

export async function markNotificationRead(
  notificationId: string
): Promise<{ id: string; is_read: boolean }> {
  return apiRequest<{ id: string; is_read: boolean }>(
    `/api/v1/notifications/${notificationId}/read`,
    { method: 'POST' }
  );
}

export async function markAllNotificationsRead(): Promise<{ count: number }> {
  return apiRequest<{ count: number }>('/api/v1/notifications/read-all', {
    method: 'POST',
  });
}
