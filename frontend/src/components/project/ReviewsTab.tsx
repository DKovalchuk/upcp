// Dedicated Reviews Tab — TASK-0099 Sprint 3

import { useTaskReviewRounds } from '@/hooks/use-task-execution';
import { ReviewVerdictCard } from '@/components/ui/ReviewVerdictCard';
import { EmptyState } from '@/components/ui/EmptyState';
import { Shield } from 'lucide-react';

interface ReviewsTabProps {
  taskId: string;
}

export function ReviewsTab({ taskId }: ReviewsTabProps) {
  const { data: reviewRounds, isLoading } = useTaskReviewRounds(taskId);
  const rounds = reviewRounds ?? [];

  if (isLoading) {
    return <div className="text-sm text-muted-foreground">Loading...</div>;
  }

  if (rounds.length === 0) {
    return (
      <EmptyState
        icon={Shield}
        title="No reviews"
        description="No review rounds have been created for this task"
      />
    );
  }

  return (
    <div className="space-y-3">
      {rounds.map((round) => (
        <ReviewVerdictCard
          key={round.id}
          agentName={round.reviewer_id ?? 'Unknown'}
          verdict={(round.verdict as 'approve' | 'reject' | 'needs_changes') ?? 'approve'}
          confidence={round.confidence}
          summary={round.summary}
          createdAt={round.created_at}
        />
      ))}
    </div>
  );
}
