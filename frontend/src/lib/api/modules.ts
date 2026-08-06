import type { Module, ModuleCreate, ModuleUpdate } from '@/types/module';
import type { PaginatedResponse } from '@/types/api';
import { apiRequest } from './client';

export async function fetchModules(componentId: string): Promise<Module[]> {
  const data = await apiRequest<PaginatedResponse<Module>>(
    `/api/v1/components/${componentId}/modules`
  );
  return data.items ?? [];
}

export async function fetchModule(id: string): Promise<Module> {
  return apiRequest<Module>(`/api/v1/modules/${id}`);
}

export async function createModule(componentId: string, data: ModuleCreate): Promise<Module> {
  return apiRequest<Module>(`/api/v1/components/${componentId}/modules`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateModule(id: string, data: ModuleUpdate): Promise<Module> {
  return apiRequest<Module>(`/api/v1/modules/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function deleteModule(id: string): Promise<void> {
  return apiRequest<void>(`/api/v1/modules/${id}`, {
    method: 'DELETE',
  });
}
