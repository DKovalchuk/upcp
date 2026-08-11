// Dedicated Reviews Tab — TASK-0099 Sprint 4

import { useTaskReviewRounds } from '@/hooks/use-task-execution';
import { useCreateReviewRound } from '@/hooks/use-quality';
import { ReviewVerdictCard } from '@/components/ui/ReviewVerdictCard';
import { EmptyState } from '@/components/ui/EmptyState';
import { Button } from '@/components/ui/button';
import { showToast } from '@/lib/toast';
import { Shield, Plus } from 'lucide-react';

interface ReviewsTabProps {
  taskId: string;
}

export function ReviewsTab({ taskId }: ReviewsTabProps) {
  const { data: reviewRounds, isLoading } = useTaskReviewRounds(taskId);
  const createReviewRound = useCreateReviewRound(taskId);
  const rounds = reviewRounds?.items ?? [];

  if (isLoading) {
    return <div className="text-sm text-muted-foreground">Loading...</div>;
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium">Reviews ({rounds.length})</h4>
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
