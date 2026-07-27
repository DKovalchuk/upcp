import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchSubtasks,
  fetchSubtask,
  createSubtask,
  updateSubtask,
  deleteSubtask,
} from '@/lib/api';
import type { SubtaskCreate, SubtaskUpdate } from '@/types/subtask';

export function useSubtasks(taskId: string) {
  return useQuery({
    queryKey: ['subtasks', taskId],
    queryFn: () => fetchSubtasks(taskId),
    enabled: !!taskId,
  });
}

export function useSubtask(id: string) {
  return useQuery({
    queryKey: ['subtasks', id],
    queryFn: () => fetchSubtask(id),
    enabled: !!id,
  });
}

export function useCreateSubtask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      taskId,
      data,
    }: {
      taskId: string;
      data: SubtaskCreate;
    }) => createSubtask(taskId, data),
    onSuccess: (_, { taskId }) => {
      queryClient.invalidateQueries({ queryKey: ['subtasks', taskId] });
    },
  });
}

export function useUpdateSubtask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: SubtaskUpdate }) =>
      updateSubtask(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['subtasks'] });
      queryClient.invalidateQueries({ queryKey: ['subtasks', id] });
    },
  });
}

export function useDeleteSubtask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => deleteSubtask(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subtasks'] });
    },
  });
}
