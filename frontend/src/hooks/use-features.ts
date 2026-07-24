import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchFeatures,
  fetchFeature,
  createFeature,
  updateFeature,
  deleteFeature,
} from '@/lib/api';
import type { FeatureCreate, FeatureUpdate } from '@/types/feature';

export function useFeatures(projectId: string) {
  return useQuery({
    queryKey: ['features', projectId],
    queryFn: () => fetchFeatures(projectId),
    enabled: !!projectId,
  });
}

export function useFeature(id: string) {
  return useQuery({
    queryKey: ['features', id],
    queryFn: () => fetchFeature(id),
    enabled: !!id,
  });
}

export function useCreateFeature() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      projectId,
      data,
    }: {
      projectId: string;
      data: FeatureCreate;
    }) => createFeature(projectId, data),
    onSuccess: (_, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: ['features', projectId] });
    },
  });
}

export function useUpdateFeature() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: FeatureUpdate }) =>
      updateFeature(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['features'] });
      queryClient.invalidateQueries({ queryKey: ['features', id] });
    },
  });
}

export function useDeleteFeature() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => deleteFeature(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['features'] });
    },
  });
}
