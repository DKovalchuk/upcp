import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchTaskClaims,
  fetchTaskHeartbeats,
  fetchTaskClarifications,
  fetchEvidence,
  fetchReviewRounds,
  releaseTask,
} from '@/lib/api';

export function useTaskClaims(taskId: string) {
  return useQuery({
    queryKey: ['tasks', taskId, 'claims'],
    queryFn: () => fetchTaskClaims(taskId),
    enabled: !!taskId,
    staleTime: 0,
  });
}

export function useTaskHeartbeats(taskId: string) {
  return useQuery({
    queryKey: ['tasks', taskId, 'heartbeats'],
    queryFn: () => fetchTaskHeartbeats(taskId),
    enabled: !!taskId,
    staleTime: 0,
  });
}

export function useTaskClarifications(taskId: string) {
  return useQuery({
    queryKey: ['tasks', taskId, 'clarifications'],
    queryFn: () => fetchTaskClarifications(taskId),
    enabled: !!taskId,
    staleTime: 0,
  });
}

export function useTaskEvidence(taskId: string) {
  return useQuery({
    queryKey: ['tasks', taskId, 'evidence'],
    queryFn: () => fetchEvidence(taskId),
    enabled: !!taskId,
  });
}

export function useTaskReviewRounds(taskId: string) {
  return useQuery({
    queryKey: ['tasks', taskId, 'review-rounds'],
    queryFn: () => fetchReviewRounds(taskId),
    enabled: !!taskId,
  });
}

export function useReleaseTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (taskId: string) => releaseTask(taskId),
    onSuccess: (_, taskId) => {
      queryClient.invalidateQueries({ queryKey: ['tasks', taskId, 'claims'] });
      queryClient.invalidateQueries({ queryKey: ['tasks', taskId, 'heartbeats'] });
    },
  });
}
