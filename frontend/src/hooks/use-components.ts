import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchComponents,
  fetchComponent,
  createComponent,
  updateComponent,
  deleteComponent,
} from '@/lib/api';
import type { ComponentCreate, ComponentUpdate } from '@/types/component';

export function useComponents(projectId: string) {
  return useQuery({
    queryKey: ['components', projectId],
    queryFn: () => fetchComponents(projectId),
    enabled: !!projectId,
  });
}

export function useComponent(id: string) {
  return useQuery({
    queryKey: ['components', id],
    queryFn: () => fetchComponent(id),
    enabled: !!id,
  });
}

export function useCreateComponent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      projectId,
      data,
    }: {
      projectId: string;
      data: ComponentCreate;
    }) => createComponent(projectId, data),
    onSuccess: (_, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: ['components', projectId] });
    },
  });
}

export function useUpdateComponent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ComponentUpdate }) =>
      updateComponent(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['components'] });
      queryClient.invalidateQueries({ queryKey: ['components', id] });
    },
  });
}

export function useDeleteComponent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => deleteComponent(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['components'] });
    },
  });
}
