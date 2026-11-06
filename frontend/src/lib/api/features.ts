import type { Feature, FeatureCreate, FeatureUpdate } from '@/types/feature';
import type { PaginatedResponse } from '@/types/api';
import { apiRequest, paginationParams } from './client';

export async function fetchFeatures(
  projectId: string,
  pagination?: { offset?: number; limit?: number },
  filters?: { status?: string; search?: string; sort_by?: string; sort_dir?: string },
): Promise<PaginatedResponse<Feature>> {
  const params = new URLSearchParams(paginationParams(pagination));
  if (filters?.status) params.set('status', filters.status);
  if (filters?.search) params.set('search', filters.search);
  if (filters?.sort_by) params.set('sort_by', filters.sort_by);
  if (filters?.sort_dir) params.set('sort_dir', filters.sort_dir);
  return apiRequest<PaginatedResponse<Feature>>(
    `/api/v1/projects/${projectId}/features?${params}`,
  );
}

export async function fetchFeature(id: string): Promise<Feature> {
  return apiRequest<Feature>(`/api/v1/features/${id}`);
}

export async function createFeature(projectId: string, data: FeatureCreate): Promise<Feature> {
  return apiRequest<Feature>(`/api/v1/projects/${projectId}/features`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateFeature(id: string, data: FeatureUpdate): Promise<Feature> {
  return apiRequest<Feature>(`/api/v1/features/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function deleteFeature(id: string): Promise<void> {
  return apiRequest<void>(`/api/v1/features/${id}`, {
    method: 'DELETE',
  });
}
