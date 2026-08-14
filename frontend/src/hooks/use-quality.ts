import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchAcceptanceCriteria,
  fetchAcceptanceCriterion,
  createAcceptanceCriterion,
  updateAcceptanceCriterion,
  deleteAcceptanceCriterion,
  fetchDoDItems,
  fetchDoDItem,
  createDoDItem,
  updateDoDItem,
  uploadEvidenceFile,
  deleteDoDItem,
  submitReviewVerdict,
  createEvidence,
  acceptEvidence,
  rejectEvidence,
  createReviewRound,
} from '@/lib/api';
import type {
  AcceptanceCriterionCreate,
  AcceptanceCriterionUpdate,
  DoDItemCreate,
  DoDItemUpdate,
} from '@/types/quality';

// Acceptance Criteria
export function useAcceptanceCriteria(taskId: string) {
  return useQuery({
    queryKey: ['acceptance-criteria', taskId],
    queryFn: () => fetchAcceptanceCriteria(taskId),
    enabled: !!taskId,
  });
}

export function useAcceptanceCriterion(id: string) {
  return useQuery({
    queryKey: ['acceptance-criteria', id],
    queryFn: () => fetchAcceptanceCriterion(id),
    enabled: !!id,
  });
}

export function useCreateAcceptanceCriterion() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      taskId,
      data,
    }: {
      taskId: string;
      data: AcceptanceCriterionCreate;
    }) => createAcceptanceCriterion(taskId, data),
    onSuccess: (_, { taskId }) => {
      queryClient.invalidateQueries({ queryKey: ['acceptance-criteria', taskId] });
    },
  });
}

export function useUpdateAcceptanceCriterion() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: string;
      data: AcceptanceCriterionUpdate;
    }) => updateAcceptanceCriterion(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['acceptance-criteria'] });
      queryClient.invalidateQueries({ queryKey: ['acceptance-criteria', id] });
    },
  });
}

export function useDeleteAcceptanceCriterion() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => deleteAcceptanceCriterion(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['acceptance-criteria'] });
    },
  });
}

// DoD Items
export function useDoDItems(taskId: string) {
  return useQuery({
    queryKey: ['dod-items', taskId],
    queryFn: () => fetchDoDItems(taskId),
    enabled: !!taskId,
  });
}

export function useDoDItem(id: string) {
  return useQuery({
    queryKey: ['dod-items', id],
    queryFn: () => fetchDoDItem(id),
    enabled: !!id,
  });
}

export function useCreateDoDItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      taskId,
      data,
    }: {
      taskId: string;
      data: DoDItemCreate;
    }) => createDoDItem(taskId, data),
    onSuccess: (_, { taskId }) => {
      queryClient.invalidateQueries({ queryKey: ['dod-items', taskId] });
    },
  });
}

export function useUpdateDoDItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: DoDItemUpdate }) =>
      updateDoDItem(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['dod-items'] });
      queryClient.invalidateQueries({ queryKey: ['dod-items', id] });
    },
  });
}

export function useDeleteDoDItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => deleteDoDItem(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dod-items'] });
    },
  });
}

// Review Verdicts
export function useSubmitReviewVerdict() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      roundId,
      data,
    }: {
      roundId: string;
      data: { verdict: string; confidence: number; summary: string };
    }) => submitReviewVerdict(roundId, data),
    onSuccess: (_, { roundId }) => {
      queryClient.invalidateQueries({ queryKey: ['review-rounds'] });
      queryClient.invalidateQueries({ queryKey: ['review-rounds', roundId] });
    },
  });
}

// Evidence
export function useCreateEvidence(taskId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: { title: string; type: string; description?: string; url?: string; content_snippet?: string }) =>
      createEvidence(taskId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks', taskId, 'evidence'] });
    },
  });
}

export function useUploadEvidenceFile(taskId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ file, title, dodItemId }: { file: File; title: string; dodItemId?: string }) =>
      uploadEvidenceFile(taskId, file, title, dodItemId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks', taskId, 'evidence'] });
    },
  });
}

export function useAcceptEvidence(taskId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (evidenceId: string) => acceptEvidence(evidenceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks', taskId, 'evidence'] });
    },
  });
}

export function useRejectEvidence(taskId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ evidenceId, reason }: { evidenceId: string; reason?: string }) =>
      rejectEvidence(evidenceId, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks', taskId, 'evidence'] });
    },
  });
}

// Review Rounds
export function useCreateReviewRound(taskId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: { reviewer_type?: string; reviewer_id?: string }) =>
      createReviewRound(taskId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks', taskId, 'review-rounds'] });
    },
  });
}
