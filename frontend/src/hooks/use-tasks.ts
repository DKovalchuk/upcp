import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchTasks,
  fetchTask,
  createTask,
  updateTask,
  deleteTask,
  completeTask,
  bulkUpdateTasks,
} from '@/lib/api';
import type { TaskCreate, TaskUpdate } from '@/types/task';

export function useTasks(
  featureId: string,
  pagination?: { offset?: number; limit?: number }
) {
  return useQuery({
    queryKey: ['tasks', featureId, pagination],
    queryFn: () => fetchTasks(featureId, pagination),
    enabled: !!featureId,
  });
}

export function useTask(id: string) {
  return useQuery({
    queryKey: ['tasks', id],
    queryFn: () => fetchTask(id),
    enabled: !!id,
  });
}

export function useCreateTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      featureId,
      data,
    }: {
      featureId: string;
      data: TaskCreate;
    }) => createTask(featureId, data),
    onSuccess: (_, { featureId }) => {
      queryClient.invalidateQueries({ queryKey: ['tasks', featureId] });
    },
  });
}

export function useUpdateTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: TaskUpdate }) =>
      updateTask(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      queryClient.invalidateQueries({ queryKey: ['tasks', id] });
    },
  });
}

export function useDeleteTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => deleteTask(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });
}

export function useCompleteTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => completeTask(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      queryClient.invalidateQueries({ queryKey: ['tasks', id] });
    },
  });
}

export function useBulkUpdateTasks() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      taskIds,
      updates,
    }: {
      taskIds: string[];
      updates: { status?: string; priority?: number; assignee_type?: string; assignee_id?: string };
    }) => bulkUpdateTasks(taskIds, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });
}
