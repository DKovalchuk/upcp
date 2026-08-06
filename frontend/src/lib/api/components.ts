import type { Component, ComponentCreate, ComponentUpdate } from '@/types/component';
import type { PaginatedResponse } from '@/types/api';
import { apiRequest } from './client';

export async function fetchComponents(projectId: string): Promise<Component[]> {
  const data = await apiRequest<PaginatedResponse<Component>>(
    `/api/v1/projects/${projectId}/components`
  );
  return data.items ?? [];
}

export async function fetchComponent(id: string): Promise<Component> {
  return apiRequest<Component>(`/api/v1/components/${id}`);
}

export async function createComponent(projectId: string, data: ComponentCreate): Promise<Component> {
  return apiRequest<Component>(`/api/v1/projects/${projectId}/components`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateComponent(id: string, data: ComponentUpdate): Promise<Component> {
  return apiRequest<Component>(`/api/v1/components/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function deleteComponent(id: string): Promise<void> {
  return apiRequest<void>(`/api/v1/components/${id}`, {
    method: 'DELETE',
  });
}
