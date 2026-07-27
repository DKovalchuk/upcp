import type { Project, ProjectCreate, ProjectUpdate } from '@/types/project';
import type { Component, ComponentCreate, ComponentUpdate } from '@/types/component';
import type { Module, ModuleCreate, ModuleUpdate } from '@/types/module';
import type { Feature, FeatureCreate, FeatureUpdate } from '@/types/feature';
import type { Task, TaskCreate, TaskUpdate, TaskClaim, AgentMe, AgentEvent } from '@/types/task';
import type { Subtask, SubtaskCreate, SubtaskUpdate } from '@/types/subtask';
import type {
  AcceptanceCriterion,
  AcceptanceCriterionCreate,
  AcceptanceCriterionUpdate,
  DoDItem,
  DoDItemCreate,
  DoDItemUpdate,
  Evidence,
  EvidenceCreate,
  ReviewRound,
} from '@/types/quality';
import type { Report, ReportCreate } from '@/types/report';
import type { AuditEvent, AuditEventCreate } from '@/types/audit';
import type {
  AttentionDashboard,
  Notification,
  PortfolioOverview,
  ProjectHealth,
} from '@/types/dashboard';
import type { HealthResponse, PaginatedResponse, DashboardStatsResponse, QualityStatsResponse } from '@/types/api';
import type { GitProvider, GitProviderCreate, GitBranch, GitCommit, GitLink } from '@/types/git';

import { safeStorage } from '@/lib/storage';

const API_BASE = '/api/v1';

function getToken(): string | null {
  return safeStorage.getItem('upcp_access_token');
}

function paginationParams(params?: { offset?: number; limit?: number }): string {
  if (!params) return '';
  const parts: string[] = [];
  if (params.offset !== undefined) parts.push(`offset=${params.offset}`);
  if (params.limit !== undefined) parts.push(`limit=${params.limit}`);
  return parts.length ? `?${parts.join('&')}` : '';
}

async function apiRequest<T>(
  url: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...options.headers as Record<string, string>,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    if (response.status === 401 && !window.location.pathname.startsWith('/login')) {
      safeStorage.removeItem('upcp_access_token');
      safeStorage.removeItem('upcp_refresh_token');
      window.location.href = '/login';
      throw new Error('Unauthorized');
    }
    const error = await response.json().catch(() => ({
      error: response.statusText,
      detail: 'Unknown error',
    }));
    throw new Error(error.detail || error.error || response.statusText);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

// Projects
export async function fetchProjects(
  pagination?: { offset?: number; limit?: number }
): Promise<PaginatedResponse<Project>> {
  return apiRequest<PaginatedResponse<Project>>(
    `${API_BASE}/projects${paginationParams(pagination)}`
  );
}

export async function fetchProject(id: string): Promise<Project> {
  return apiRequest<Project>(`${API_BASE}/projects/${id}`);
}

export async function createProject(data: ProjectCreate): Promise<Project> {
  return apiRequest<Project>(`${API_BASE}/projects`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateProject(id: string, data: ProjectUpdate): Promise<Project> {
  return apiRequest<Project>(`${API_BASE}/projects/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function deleteProject(id: string): Promise<void> {
  return apiRequest<void>(`${API_BASE}/projects/${id}`, {
    method: 'DELETE',
  });
}

// Components
export async function fetchComponents(projectId: string): Promise<Component[]> {
  const data = await apiRequest<PaginatedResponse<Component>>(`${API_BASE}/projects/${projectId}/components`);
  return data.items ?? [];
}

export async function fetchComponent(id: string): Promise<Component> {
  return apiRequest<Component>(`${API_BASE}/components/${id}`);
}

export async function createComponent(projectId: string, data: ComponentCreate): Promise<Component> {
  return apiRequest<Component>(`${API_BASE}/projects/${projectId}/components`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateComponent(id: string, data: ComponentUpdate): Promise<Component> {
  return apiRequest<Component>(`${API_BASE}/components/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function deleteComponent(id: string): Promise<void> {
  return apiRequest<void>(`${API_BASE}/components/${id}`, {
    method: 'DELETE',
  });
}

// Modules
export async function fetchModules(componentId: string): Promise<Module[]> {
  const data = await apiRequest<PaginatedResponse<Module>>(`${API_BASE}/components/${componentId}/modules`);
  return data.items ?? [];
}

export async function fetchModule(id: string): Promise<Module> {
  return apiRequest<Module>(`${API_BASE}/modules/${id}`);
}

export async function createModule(componentId: string, data: ModuleCreate): Promise<Module> {
  return apiRequest<Module>(`${API_BASE}/components/${componentId}/modules`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateModule(id: string, data: ModuleUpdate): Promise<Module> {
  return apiRequest<Module>(`${API_BASE}/modules/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function deleteModule(id: string): Promise<void> {
  return apiRequest<void>(`${API_BASE}/modules/${id}`, {
    method: 'DELETE',
  });
}

// Features
export async function fetchFeatures(
  projectId: string,
  pagination?: { offset?: number; limit?: number }
): Promise<PaginatedResponse<Feature>> {
  return apiRequest<PaginatedResponse<Feature>>(
    `${API_BASE}/projects/${projectId}/features${paginationParams(pagination)}`
  );
}

export async function fetchFeature(id: string): Promise<Feature> {
  return apiRequest<Feature>(`${API_BASE}/features/${id}`);
}

export async function createFeature(projectId: string, data: FeatureCreate): Promise<Feature> {
  return apiRequest<Feature>(`${API_BASE}/projects/${projectId}/features`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateFeature(id: string, data: FeatureUpdate): Promise<Feature> {
  return apiRequest<Feature>(`${API_BASE}/features/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function deleteFeature(id: string): Promise<void> {
  return apiRequest<void>(`${API_BASE}/features/${id}`, {
    method: 'DELETE',
  });
}

// Tasks
export async function fetchTasks(
  featureId: string,
  pagination?: { offset?: number; limit?: number }
): Promise<PaginatedResponse<Task>> {
  return apiRequest<PaginatedResponse<Task>>(
    `${API_BASE}/features/${featureId}/tasks${paginationParams(pagination)}`
  );
}

export async function fetchTask(id: string): Promise<Task> {
  return apiRequest<Task>(`${API_BASE}/tasks/${id}`);
}

export async function createTask(featureId: string, data: TaskCreate): Promise<Task> {
  return apiRequest<Task>(`${API_BASE}/features/${featureId}/tasks`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateTask(id: string, data: TaskUpdate): Promise<Task> {
  return apiRequest<Task>(`${API_BASE}/tasks/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function deleteTask(id: string): Promise<void> {
  return apiRequest<void>(`${API_BASE}/tasks/${id}`, {
    method: 'DELETE',
  });
}

export async function completeTask(id: string): Promise<{ id: string; status: string }> {
  return apiRequest<{ id: string; status: string }>(`${API_BASE}/tasks/${id}/complete`, {
    method: 'POST',
  });
}

// Subtasks
export async function fetchSubtasks(taskId: string): Promise<Subtask[]> {
  const data = await apiRequest<PaginatedResponse<Subtask>>(`${API_BASE}/tasks/${taskId}/subtasks`);
  return data.items ?? [];
}

export async function fetchSubtask(id: string): Promise<Subtask> {
  return apiRequest<Subtask>(`${API_BASE}/subtasks/${id}`);
}

export async function createSubtask(taskId: string, data: SubtaskCreate): Promise<Subtask> {
  return apiRequest<Subtask>(`${API_BASE}/tasks/${taskId}/subtasks`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateSubtask(id: string, data: SubtaskUpdate): Promise<Subtask> {
  return apiRequest<Subtask>(`${API_BASE}/subtasks/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function deleteSubtask(id: string): Promise<void> {
  return apiRequest<void>(`${API_BASE}/subtasks/${id}`, {
    method: 'DELETE',
  });
}

// Acceptance Criteria
export async function fetchAcceptanceCriteria(taskId: string): Promise<AcceptanceCriterion[]> {
  return apiRequest<AcceptanceCriterion[]>(`${API_BASE}/tasks/${taskId}/acceptance-criteria`);
}

export async function fetchAcceptanceCriterion(id: string): Promise<AcceptanceCriterion> {
  return apiRequest<AcceptanceCriterion>(`${API_BASE}/acceptance-criteria/${id}`);
}

export async function createAcceptanceCriterion(
  taskId: string,
  data: AcceptanceCriterionCreate
): Promise<AcceptanceCriterion> {
  return apiRequest<AcceptanceCriterion>(`${API_BASE}/tasks/${taskId}/acceptance-criteria`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateAcceptanceCriterion(
  id: string,
  data: AcceptanceCriterionUpdate
): Promise<AcceptanceCriterion> {
  return apiRequest<AcceptanceCriterion>(`${API_BASE}/acceptance-criteria/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function deleteAcceptanceCriterion(id: string): Promise<void> {
  return apiRequest<void>(`${API_BASE}/acceptance-criteria/${id}`, {
    method: 'DELETE',
  });
}

// DoD Items
export async function fetchDoDItems(taskId: string): Promise<DoDItem[]> {
  return apiRequest<DoDItem[]>(`${API_BASE}/tasks/${taskId}/dod-items`);
}

export async function fetchDoDItem(id: string): Promise<DoDItem> {
  return apiRequest<DoDItem>(`${API_BASE}/dod-items/${id}`);
}

export async function createDoDItem(taskId: string, data: DoDItemCreate): Promise<DoDItem> {
  return apiRequest<DoDItem>(`${API_BASE}/tasks/${taskId}/dod-items`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateDoDItem(id: string, data: DoDItemUpdate): Promise<DoDItem> {
  return apiRequest<DoDItem>(`${API_BASE}/dod-items/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function deleteDoDItem(id: string): Promise<void> {
  return apiRequest<void>(`${API_BASE}/dod-items/${id}`, {
    method: 'DELETE',
  });
}

// Reports
export async function fetchReports(
  projectId: string,
  pagination?: { offset?: number; limit?: number }
): Promise<PaginatedResponse<Report>> {
  return apiRequest<PaginatedResponse<Report>>(
    `${API_BASE}/projects/${projectId}/reports${paginationParams(pagination)}`
  );
}

export async function fetchReport(id: string): Promise<Report> {
  return apiRequest<Report>(`${API_BASE}/reports/${id}`);
}

export async function createReport(projectId: string, data: ReportCreate): Promise<Report> {
  return apiRequest<Report>(`${API_BASE}/projects/${projectId}/reports`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// Audit Events
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
    ? `${API_BASE}/projects/${projectId}/audit-events?${qs}`
    : `${API_BASE}/projects/${projectId}/audit-events`;
  return apiRequest<PaginatedResponse<AuditEvent>>(url);
}

export async function createAuditEvent(data: AuditEventCreate): Promise<AuditEvent> {
  return apiRequest<AuditEvent>(`${API_BASE}/audit-events`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// Dashboard
export async function fetchDashboardStats(): Promise<DashboardStatsResponse> {
  return apiRequest<DashboardStatsResponse>(`${API_BASE}/dashboard/stats`);
}

// Quality Stats
export async function fetchQualityStats(
  projectId: string
): Promise<QualityStatsResponse> {
  return apiRequest<QualityStatsResponse>(
    `${API_BASE}/projects/${projectId}/quality/stats`
  );
}

// Health
export async function fetchHealth(): Promise<HealthResponse> {
  return apiRequest<HealthResponse>(`${API_BASE}/health`);
}

// Search
export interface SearchResult {
  entity_type: string;
  id: string;
  title: string;
  subtitle: string;
  url: string;
}

export async function searchGlobal(
  query: string,
  limit = 20
): Promise<SearchResult[]> {
  return apiRequest<SearchResult[]>(
    `${API_BASE}/search?q=${encodeURIComponent(query)}&limit=${limit}`
  );
}

// Git Providers
export async function fetchGitProviders(
  projectId: string
): Promise<GitProvider[]> {
  return apiRequest<GitProvider[]>(
    `${API_BASE}/projects/${projectId}/git-providers`
  );
}

export async function createGitProvider(
  projectId: string,
  data: GitProviderCreate
): Promise<GitProvider> {
  return apiRequest<GitProvider>(
    `${API_BASE}/projects/${projectId}/git-providers`,
    { method: 'POST', body: JSON.stringify(data) }
  );
}

export async function deleteGitProvider(id: string): Promise<void> {
  return apiRequest<void>(`${API_BASE}/git-providers/${id}`, {
    method: 'DELETE',
  });
}

// Git Branches
export async function fetchGitBranches(
  providerId: string
): Promise<GitBranch[]> {
  return apiRequest<GitBranch[]>(
    `${API_BASE}/git-providers/${providerId}/branches`
  );
}

// Git Commits
export async function fetchGitCommits(
  providerId: string,
  limit = 20
): Promise<GitCommit[]> {
  return apiRequest<GitCommit[]>(
    `${API_BASE}/git-providers/${providerId}/commits?limit=${limit}`
  );
}

// Git Links
export async function fetchGitLinks(
  entityType: string,
  entityId: string
): Promise<GitLink[]> {
  return apiRequest<GitLink[]>(
    `${API_BASE}/git-links?entity_type=${entityType}&entity_id=${entityId}`
  );
}

export async function createGitLink(
  data: Omit<GitLink, 'id'>
): Promise<GitLink> {
  return apiRequest<GitLink>(`${API_BASE}/git-links`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function deleteGitLink(id: string): Promise<void> {
  return apiRequest<void>(`${API_BASE}/git-links/${id}`, {
    method: 'DELETE',
  });
}

// ── Agent Workflow ──

export async function claimTask(
  taskId: string,
  contextSnapshot?: string
): Promise<TaskClaim> {
  return apiRequest<TaskClaim>(`${API_BASE}/tasks/${taskId}/claim`, {
    method: 'POST',
    body: JSON.stringify({ context_snapshot: contextSnapshot }),
  });
}

export async function releaseTask(taskId: string): Promise<{ ok: boolean }> {
  return apiRequest<{ ok: boolean }>(`${API_BASE}/tasks/${taskId}/release`, {
    method: 'POST',
  });
}

export async function sendHeartbeat(
  taskId: string,
  data: {
    progress_percent: number;
    current_step: string;
    next_step: string;
    blockers?: string;
    eta?: string;
  }
): Promise<{ ok: boolean }> {
  return apiRequest<{ ok: boolean }>(`${API_BASE}/tasks/${taskId}/heartbeat`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateProgress(
  taskId: string,
  progressPercent: number
): Promise<{ ok: boolean }> {
  return apiRequest<{ ok: boolean }>(`${API_BASE}/tasks/${taskId}/progress`, {
    method: 'POST',
    body: JSON.stringify({ progress_percent: progressPercent }),
  });
}

// ── Agent Self-Service ──

export async function getAgentMe(): Promise<AgentMe> {
  return apiRequest<AgentMe>(`${API_BASE}/agent/me`);
}

export async function getAgentInbox(
  since?: string
): Promise<{ events: AgentEvent[] }> {
  const params = since ? `?since=${encodeURIComponent(since)}` : '';
  return apiRequest<{ events: AgentEvent[] }>(
    `${API_BASE}/agent/inbox${params}`
  );
}

export async function getAgentPlaybook(): Promise<{ content: string }> {
  return apiRequest<{ content: string }>(`${API_BASE}/agent/playbook`);
}

// ── Evidence ──

export async function fetchEvidence(
  taskId: string
): Promise<{ items: Evidence[] }> {
  return apiRequest<{ items: Evidence[] }>(
    `${API_BASE}/tasks/${taskId}/evidence`
  );
}

export async function createEvidence(
  taskId: string,
  data: EvidenceCreate
): Promise<Evidence> {
  return apiRequest<Evidence>(`${API_BASE}/tasks/${taskId}/evidence`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function verifyEvidence(
  evidenceId: string
): Promise<Evidence> {
  return apiRequest<Evidence>(
    `${API_BASE}/evidence/${evidenceId}/agent-verify`,
    { method: 'POST' }
  );
}

export async function acceptEvidence(
  evidenceId: string
): Promise<Evidence> {
  return apiRequest<Evidence>(
    `${API_BASE}/evidence/${evidenceId}/human-accept`,
    { method: 'POST' }
  );
}

export async function rejectEvidence(
  evidenceId: string,
  reason?: string
): Promise<Evidence> {
  return apiRequest<Evidence>(`${API_BASE}/evidence/${evidenceId}/reject`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
  });
}

// ── Review Rounds ──

export async function fetchReviewRounds(
  taskId: string
): Promise<{ items: ReviewRound[] }> {
  return apiRequest<{ items: ReviewRound[] }>(
    `${API_BASE}/tasks/${taskId}/review-rounds`
  );
}

export async function createReviewRound(
  taskId: string,
  data: { reviewer_type?: string; reviewer_id?: string }
): Promise<ReviewRound> {
  return apiRequest<ReviewRound>(
    `${API_BASE}/tasks/${taskId}/review-rounds`,
    { method: 'POST', body: JSON.stringify(data) }
  );
}

export async function submitReviewVerdict(
  roundId: string,
  data: { verdict: string; confidence: number; summary: string }
): Promise<ReviewRound> {
  return apiRequest<ReviewRound>(
    `${API_BASE}/review-rounds/${roundId}/verdict`,
    { method: 'POST', body: JSON.stringify(data) }
  );
}

export async function submitForReview(
  taskId: string
): Promise<ReviewRound> {
  return apiRequest<ReviewRound>(
    `${API_BASE}/tasks/${taskId}/submit-review`,
    { method: 'POST' }
  );
}

// ── Attention Dashboard ──

export async function fetchAttentionDashboard(): Promise<AttentionDashboard> {
  return apiRequest<AttentionDashboard>(`${API_BASE}/dashboard/attention`);
}

export async function fetchProjectHealth(
  projectId: string
): Promise<ProjectHealth> {
  return apiRequest<ProjectHealth>(`${API_BASE}/projects/${projectId}/health`);
}

export async function fetchPortfolioOverview(): Promise<PortfolioOverview> {
  return apiRequest<PortfolioOverview>(`${API_BASE}/portfolio/overview`);
}

// ── Notifications ──

export async function fetchNotifications(
  unreadOnly = false
): Promise<{ items: Notification[] }> {
  const params = unreadOnly ? '?unread_only=true' : '';
  return apiRequest<{ items: Notification[] }>(
    `${API_BASE}/notifications${params}`
  );
}

export async function fetchUnreadCount(): Promise<{ count: number }> {
  return apiRequest<{ count: number }>(
    `${API_BASE}/notifications/unread-count`
  );
}

export async function markNotificationRead(
  notificationId: string
): Promise<{ id: string; is_read: boolean }> {
  return apiRequest<{ id: string; is_read: boolean }>(
    `${API_BASE}/notifications/${notificationId}/read`,
    { method: 'POST' }
  );
}

export async function markAllNotificationsRead(): Promise<{ count: number }> {
  return apiRequest<{ count: number }>(
    `${API_BASE}/notifications/read-all`,
    { method: 'POST' }
  );
}
