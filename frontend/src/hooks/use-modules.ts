import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchModules,
  fetchModule,
  createModule,
  updateModule,
  deleteModule,
} from '@/lib/api';
import type { ModuleCreate, ModuleUpdate } from '@/types/module';

export function useModules(componentId: string) {
  return useQuery({
    queryKey: ['modules', componentId],
    queryFn: () => fetchModules(componentId),
    enabled: !!componentId,
  });
}

export function useModule(id: string) {
  return useQuery({
    queryKey: ['modules', id],
    queryFn: () => fetchModule(id),
    enabled: !!id,
  });
}

export function useCreateModule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      componentId,
      data,
    }: {
      componentId: string;
      data: ModuleCreate;
    }) => createModule(componentId, data),
    onSuccess: (_, { componentId }) => {
      queryClient.invalidateQueries({ queryKey: ['modules', componentId] });
    },
  });
}

export function useUpdateModule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ModuleUpdate }) =>
      updateModule(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['modules'] });
      queryClient.invalidateQueries({ queryKey: ['modules', id] });
    },
  });
}

export function useDeleteModule() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => deleteModule(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['modules'] });
    },
  });
}
