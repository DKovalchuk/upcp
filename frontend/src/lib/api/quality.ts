import type {
  AcceptanceCriterion,
  AcceptanceCriterionCreate,
  AcceptanceCriterionUpdate,
  DoDItem,
  DoDItemCreate,
  DoDItemUpdate,
  Evidence,
  EvidenceCreate,
  ReviewRound,
} from '@/types/quality';
import type { QualityStatsResponse } from '@/types/api';
import { apiRequest } from './client';

// ── Acceptance Criteria ──

export async function fetchAcceptanceCriteria(taskId: string): Promise<AcceptanceCriterion[]> {
  const data = await apiRequest<{ items: AcceptanceCriterion[] }>(
    `/api/v1/tasks/${taskId}/acceptance-criteria`
  );
  return data.items ?? [];
}

export async function fetchAcceptanceCriterion(id: string): Promise<AcceptanceCriterion> {
  return apiRequest<AcceptanceCriterion>(`/api/v1/acceptance-criteria/${id}`);
}

export async function createAcceptanceCriterion(
  taskId: string,
  data: AcceptanceCriterionCreate
): Promise<AcceptanceCriterion> {
  return apiRequest<AcceptanceCriterion>(`/api/v1/tasks/${taskId}/acceptance-criteria`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateAcceptanceCriterion(
  id: string,
  data: AcceptanceCriterionUpdate
): Promise<AcceptanceCriterion> {
  return apiRequest<AcceptanceCriterion>(`/api/v1/acceptance-criteria/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function deleteAcceptanceCriterion(id: string): Promise<void> {
  return apiRequest<void>(`/api/v1/acceptance-criteria/${id}`, {
    method: 'DELETE',
  });
}

// ── DoD Items ──

export async function fetchDoDItems(taskId: string): Promise<DoDItem[]> {
  const data = await apiRequest<{ items: DoDItem[] }>(`/api/v1/tasks/${taskId}/dod-items`);
  return data.items ?? [];
}

export async function fetchDoDItem(id: string): Promise<DoDItem> {
  return apiRequest<DoDItem>(`/api/v1/dod-items/${id}`);
}

export async function createDoDItem(taskId: string, data: DoDItemCreate): Promise<DoDItem> {
  return apiRequest<DoDItem>(`/api/v1/tasks/${taskId}/dod-items`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateDoDItem(id: string, data: DoDItemUpdate): Promise<DoDItem> {
  return apiRequest<DoDItem>(`/api/v1/dod-items/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function deleteDoDItem(id: string): Promise<void> {
  return apiRequest<void>(`/api/v1/dod-items/${id}`, {
    method: 'DELETE',
  });
}

// ── Evidence ──

export async function fetchEvidence(
  taskId: string
): Promise<{ items: Evidence[] }> {
  return apiRequest<{ items: Evidence[] }>(`/api/v1/tasks/${taskId}/evidence`);
}

export async function createEvidence(
  taskId: string,
  data: EvidenceCreate
): Promise<Evidence> {
  return apiRequest<Evidence>(`/api/v1/tasks/${taskId}/evidence`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function verifyEvidence(evidenceId: string): Promise<Evidence> {
  return apiRequest<Evidence>(`/api/v1/evidence/${evidenceId}/agent-verify`, {
    method: 'POST',
  });
}

export async function acceptEvidence(evidenceId: string): Promise<Evidence> {
  return apiRequest<Evidence>(`/api/v1/evidence/${evidenceId}/human-accept`, {
    method: 'POST',
  });
}

export async function rejectEvidence(
  evidenceId: string,
  reason?: string
): Promise<Evidence> {
  return apiRequest<Evidence>(`/api/v1/evidence/${evidenceId}/reject`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
  });
}

// ── Review Rounds ──

export async function fetchReviewRounds(
  taskId: string
): Promise<{ items: ReviewRound[] }> {
  return apiRequest<{ items: ReviewRound[] }>(`/api/v1/tasks/${taskId}/review-rounds`);
}

export async function createReviewRound(
  taskId: string,
  data: { reviewer_type?: string; reviewer_id?: string }
): Promise<ReviewRound> {
  return apiRequest<ReviewRound>(`/api/v1/tasks/${taskId}/review-rounds`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function submitReviewVerdict(
  roundId: string,
  data: { verdict: string; confidence: number; summary: string }
): Promise<ReviewRound> {
  return apiRequest<ReviewRound>(`/api/v1/review-rounds/${roundId}/verdict`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function submitForReview(taskId: string): Promise<ReviewRound> {
  return apiRequest<ReviewRound>(`/api/v1/tasks/${taskId}/submit-review`, {
    method: 'POST',
  });
}

// ── Quality Stats ──

export async function fetchQualityStats(
  projectId: string
): Promise<QualityStatsResponse> {
  return apiRequest<QualityStatsResponse>(
    `/api/v1/projects/${projectId}/quality/stats`
  );
}
