import type { Project, ProjectCreate, ProjectUpdate } from '@/types/project';
import type { Component, ComponentCreate, ComponentUpdate } from '@/types/component';
import type { Module, ModuleCreate, ModuleUpdate } from '@/types/module';
import type { Feature, FeatureCreate, FeatureUpdate } from '@/types/feature';
import type { Task, TaskCreate, TaskUpdate } from '@/types/task';
import type { Subtask, SubtaskCreate, SubtaskUpdate } from '@/types/subtask';
import type {
  AcceptanceCriterion,
  AcceptanceCriterionCreate,
  AcceptanceCriterionUpdate,
  DoDItem,
  DoDItemCreate,
  DoDItemUpdate,
} from '@/types/quality';
import type { Report, ReportCreate } from '@/types/report';
import type { AuditEvent, AuditEventCreate } from '@/types/audit';
import type { HealthResponse, PaginatedResponse } from '@/types/api';

const API_BASE = '/api/v1';

async function apiRequest<T>(
  url: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
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
export async function fetchProjects(): Promise<Project[]> {
  const data = await apiRequest<PaginatedResponse<Project>>(`${API_BASE}/projects`);
  return data.items ?? [];
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
export async function fetchFeatures(projectId: string): Promise<Feature[]> {
  const data = await apiRequest<PaginatedResponse<Feature>>(`${API_BASE}/projects/${projectId}/features`);
  return data.items ?? [];
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
export async function fetchTasks(featureId: string): Promise<Task[]> {
  const data = await apiRequest<PaginatedResponse<Task>>(`${API_BASE}/features/${featureId}/tasks`);
  return data.items ?? [];
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
export async function fetchReports(projectId: string): Promise<Report[]> {
  const data = await apiRequest<PaginatedResponse<Report>>(`${API_BASE}/projects/${projectId}/reports`);
  return data.items ?? [];
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
export async function fetchAuditEvents(filters?: Record<string, string>): Promise<AuditEvent[]> {
  const params = new URLSearchParams(filters);
  const url = params.toString() ? `${API_BASE}/audit-events?${params}` : `${API_BASE}/audit-events`;
  return apiRequest<AuditEvent[]>(url);
}

export async function createAuditEvent(data: AuditEventCreate): Promise<AuditEvent> {
  return apiRequest<AuditEvent>(`${API_BASE}/audit-events`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// Health
export async function fetchHealth(): Promise<HealthResponse> {
  return apiRequest<HealthResponse>(`${API_BASE}/health`);
}