// Dedicated Reviews Tab — TASK-0099 Sprint 4

import { useState } from 'react';
import { useTaskReviewRounds } from '@/hooks/use-task-execution';
import { useCreateReviewRound, useSubmitForReview } from '@/hooks/use-quality';
import { ReviewVerdictCard } from '@/components/ui/ReviewVerdictCard';
import { EmptyState } from '@/components/ui/EmptyState';
import { Button } from '@/components/ui/button';
import { showToast } from '@/lib/toast';
import { Shield, Plus, Send } from 'lucide-react';

// Delivery workflow statuses from which the review gate accepts a submission
// (backend ReviewGateService: claimed / in_progress; ready_for_review and
// later states are already submitted or terminal).
const SUBMITTABLE_STATUSES: ReadonlySet<string> = new Set(['claimed', 'in_progress']);

interface ReviewsTabProps {
  taskId: string;
  /** Current task status — gates the "Submit for review" action. */
  taskStatus?: string;
}

export function ReviewsTab({ taskId, taskStatus }: ReviewsTabProps) {
  const { data: reviewRounds, isLoading } = useTaskReviewRounds(taskId);
  const createReviewRound = useCreateReviewRound(taskId);
  const submitForReview = useSubmitForReview(taskId);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const rounds = reviewRounds?.items ?? [];
  const canSubmit = !!taskStatus && SUBMITTABLE_STATUSES.has(taskStatus);

  const handleSubmitForReview = () => {
    setSubmitError(null);
    submitForReview.mutate(undefined, {
      onSuccess: () => showToast.success('Submitted for review'),
      onError: (error) =>
        setSubmitError(
          error instanceof Error && error.message
            ? error.message
            : 'Failed to submit task for review'
        ),
    });
  };

  if (isLoading) {
    return <div className="text-sm text-muted-foreground">Loading...</div>;
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium">Reviews ({rounds.length})</h4>
        <div className="flex items-center gap-2">
          {canSubmit && (
            <Button
              size="sm"
              onClick={handleSubmitForReview}
              disabled={submitForReview.isPending}
            >
              <Send className="mr-1 h-3 w-3" />
              {submitForReview.isPending ? 'Submitting...' : 'Submit for review'}
            </Button>
          )}
          <Button
            size="sm"
            variant="outline"
            onClick={() => createReviewRound.mutate({}, {
              onSuccess: () => showToast.created('Review round'),
              onError: () => showToast.error('Failed to create review round'),
            })}
            disabled={createReviewRound.isPending}
          >
            <Plus className="mr-1 h-3 w-3" />
            {createReviewRound.isPending ? 'Creating...' : 'New Review'}
          </Button>
        </div>
      </div>

      {submitError && (
        <p role="alert" className="text-sm text-destructive">
          {submitError}
        </p>
      )}

      {rounds.length === 0 ? (
        <EmptyState icon={Shield} title="No reviews" description="No review rounds have been created for this task" />
      ) : (
        rounds.map((round) => (
          <ReviewVerdictCard
            key={round.id}
            agentName={round.reviewer_id ?? 'Unknown'}
            verdict={(round.verdict as 'approve' | 'reject' | 'needs_changes') ?? 'approve'}
            confidence={round.confidence ?? undefined}
            summary={round.summary ?? undefined}
            createdAt={round.created_at}
          />
        ))
      )}
    </div>
  );
}
