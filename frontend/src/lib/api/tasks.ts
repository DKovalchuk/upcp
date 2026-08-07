import type {
  Task,
  TaskCreate,
  TaskUpdate,
  TaskClaim,
  Heartbeat,
  ClarificationRequest,
  AgentMe,
  AgentEvent,
} from '@/types/task';
import type { Subtask, SubtaskCreate, SubtaskUpdate } from '@/types/subtask';
import type { PaginatedResponse } from '@/types/api';
import { apiRequest, paginationParams } from './client';

// ── Tasks ──

export async function fetchTasks(
  featureId: string,
  pagination?: { offset?: number; limit?: number }
): Promise<PaginatedResponse<Task>> {
  return apiRequest<PaginatedResponse<Task>>(
    `/api/v1/features/${featureId}/tasks${paginationParams(pagination)}`
  );
}

export async function fetchProjectTasks(
  projectId: string,
  filters?: { status?: string; feature_id?: string; assignee_type?: string },
  pagination?: { offset?: number; limit?: number }
): Promise<PaginatedResponse<Task>> {
  const params = new URLSearchParams();
  if (filters?.status) params.set('status', filters.status);
  if (filters?.feature_id) params.set('feature_id', filters.feature_id);
  if (filters?.assignee_type) params.set('assignee_type', filters.assignee_type);
  const qs = params.toString();
  const pag = paginationParams(pagination);
  const sep = qs && pag ? '&' : pag ? '' : qs ? '?' : '';
  return apiRequest<PaginatedResponse<Task>>(
    `/api/v1/projects/${projectId}/tasks${sep}${qs}${pag}`
  );
}

export async function fetchTask(id: string): Promise<Task> {
  return apiRequest<Task>(`/api/v1/tasks/${id}`);
}

export async function createTask(featureId: string, data: TaskCreate): Promise<Task> {
  return apiRequest<Task>(`/api/v1/features/${featureId}/tasks`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateTask(id: string, data: TaskUpdate): Promise<Task> {
  return apiRequest<Task>(`/api/v1/tasks/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function deleteTask(id: string): Promise<void> {
  return apiRequest<void>(`/api/v1/tasks/${id}`, {
    method: 'DELETE',
  });
}

export async function completeTask(id: string): Promise<{ id: string; status: string }> {
  return apiRequest<{ id: string; status: string }>(`/api/v1/tasks/${id}/complete`, {
    method: 'POST',
  });
}

// ── Subtasks ──

export async function fetchSubtasks(taskId: string): Promise<Subtask[]> {
  const data = await apiRequest<PaginatedResponse<Subtask>>(
    `/api/v1/tasks/${taskId}/subtasks`
  );
  return data.items ?? [];
}

export async function fetchSubtask(id: string): Promise<Subtask> {
  return apiRequest<Subtask>(`/api/v1/subtasks/${id}`);
}

export async function createSubtask(taskId: string, data: SubtaskCreate): Promise<Subtask> {
  return apiRequest<Subtask>(`/api/v1/tasks/${taskId}/subtasks`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateSubtask(id: string, data: SubtaskUpdate): Promise<Subtask> {
  return apiRequest<Subtask>(`/api/v1/subtasks/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function deleteSubtask(id: string): Promise<void> {
  return apiRequest<void>(`/api/v1/subtasks/${id}`, {
    method: 'DELETE',
  });
}

// ── Agent Workflow (write) ──

export async function claimTask(
  taskId: string,
  contextSnapshot?: string
): Promise<TaskClaim> {
  return apiRequest<TaskClaim>(`/api/v1/tasks/${taskId}/claim`, {
    method: 'POST',
    body: JSON.stringify({ context_snapshot: contextSnapshot }),
  });
}

export async function releaseTask(taskId: string): Promise<{ ok: boolean }> {
  return apiRequest<{ ok: boolean }>(`/api/v1/tasks/${taskId}/release`, {
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
  return apiRequest<{ ok: boolean }>(`/api/v1/tasks/${taskId}/heartbeat`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateProgress(
  taskId: string,
  progressPercent: number
): Promise<{ ok: boolean }> {
  return apiRequest<{ ok: boolean }>(`/api/v1/tasks/${taskId}/progress`, {
    method: 'POST',
    body: JSON.stringify({ progress_percent: progressPercent }),
  });
}

// ── Task Workflow (read) ──

export async function fetchTaskClaims(
  taskId: string
): Promise<{ items: TaskClaim[] }> {
  return apiRequest<{ items: TaskClaim[] }>(`/api/v1/tasks/${taskId}/claims`);
}

export async function fetchTaskHeartbeats(
  taskId: string
): Promise<{ items: Heartbeat[] }> {
  return apiRequest<{ items: Heartbeat[] }>(`/api/v1/tasks/${taskId}/heartbeats`);
}

export async function fetchTaskClarifications(
  taskId: string
): Promise<{ items: ClarificationRequest[] }> {
  return apiRequest<{ items: ClarificationRequest[] }>(
    `/api/v1/tasks/${taskId}/clarifications`
  );
}

// ── Agent Self-Service ──

export async function getAgentMe(): Promise<AgentMe> {
  return apiRequest<AgentMe>('/api/v1/agent/me');
}

export async function getAgentInbox(
  since?: string
): Promise<{ events: AgentEvent[] }> {
  const params = since ? `?since=${encodeURIComponent(since)}` : '';
  return apiRequest<{ events: AgentEvent[] }>(`/api/v1/agent/inbox${params}`);
}

export async function getAgentPlaybook(): Promise<{ content: string }> {
  return apiRequest<{ content: string }>('/api/v1/agent/playbook');
}
