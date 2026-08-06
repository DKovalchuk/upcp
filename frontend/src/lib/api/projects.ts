import type { Project, ProjectCreate, ProjectUpdate } from '@/types/project';
import type { PaginatedResponse } from '@/types/api';
import { apiRequest, paginationParams } from './client';

export async function fetchProjects(
  pagination?: { offset?: number; limit?: number }
): Promise<PaginatedResponse<Project>> {
  return apiRequest<PaginatedResponse<Project>>(
    `/api/v1/projects${paginationParams(pagination)}`
  );
}

export async function fetchProject(id: string): Promise<Project> {
  return apiRequest<Project>(`/api/v1/projects/${id}`);
}

export async function createProject(data: ProjectCreate): Promise<Project> {
  return apiRequest<Project>('/api/v1/projects', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateProject(id: string, data: ProjectUpdate): Promise<Project> {
  return apiRequest<Project>(`/api/v1/projects/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function deleteProject(id: string): Promise<void> {
  return apiRequest<void>(`/api/v1/projects/${id}`, {
    method: 'DELETE',
  });
}
