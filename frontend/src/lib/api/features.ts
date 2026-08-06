import type { Feature, FeatureCreate, FeatureUpdate } from '@/types/feature';
import type { PaginatedResponse } from '@/types/api';
import { apiRequest, paginationParams } from './client';

export async function fetchFeatures(
  projectId: string,
  pagination?: { offset?: number; limit?: number }
): Promise<PaginatedResponse<Feature>> {
  return apiRequest<PaginatedResponse<Feature>>(
    `/api/v1/projects/${projectId}/features${paginationParams(pagination)}`
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
