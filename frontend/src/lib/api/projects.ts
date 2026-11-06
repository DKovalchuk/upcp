import type { Project, ProjectCreate, ProjectUpdate } from '@/types/project';
import type { PaginatedResponse } from '@/types/api';
import { apiRequest, paginationParams } from './client';

export async function fetchProjects(
  pagination?: { offset?: number; limit?: number },
  filters?: { status?: string; search?: string; sort_by?: string; sort_dir?: string },
): Promise<PaginatedResponse<Project>> {
  const params = new URLSearchParams(paginationParams(pagination));
  if (filters?.status) params.set('status', filters.status);
  if (filters?.search) params.set('search', filters.search);
  if (filters?.sort_by) params.set('sort_by', filters.sort_by);
  if (filters?.sort_dir) params.set('sort_dir', filters.sort_dir);
  return apiRequest<PaginatedResponse<Project>>(
    `/api/v1/projects?${params}`,
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
