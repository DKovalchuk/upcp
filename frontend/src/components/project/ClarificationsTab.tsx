// Dedicated Clarifications Tab — TASK-0099 Sprint 3

import { useTaskClarifications, useAnswerClarification } from '@/hooks/use-task-execution';
import { ClarificationBanner } from '@/components/ui/ClarificationBanner';
import { EmptyState } from '@/components/ui/EmptyState';
import { showToast } from '@/lib/toast';
import { MessageCircle } from 'lucide-react';

interface ClarificationsTabProps {
  taskId: string;
  taskName: string;
}

export function ClarificationsTab({ taskId, taskName }: ClarificationsTabProps) {
  const { data, isLoading } = useTaskClarifications(taskId);
  const answerClarification = useAnswerClarification(taskId);
  const clarifications = data?.items ?? [];

  if (isLoading) {
    return <div className="text-sm text-muted-foreground">Loading...</div>;
  }

  if (clarifications.length === 0) {
    return (
      <EmptyState
        icon={MessageCircle}
        title="No clarifications"
        description="No clarification requests have been made for this task"
      />
    );
  }

  return (
    <div className="space-y-3">
      {clarifications.map((cr) => (
        <ClarificationBanner
          key={cr.id}
          taskName={taskName}
          question={cr.question}
          askedBy={cr.author_id}
          askedAt={cr.created_at}
          answer={cr.answer}
          answeredBy={cr.answered_by}
          answeredAt={cr.answered_at}
          isBlocking={cr.blocking}
          state={cr.state}
          onAnswer={
            cr.state === 'open'
              ? (answer) => {
                  answerClarification.mutate(
                    { clarificationId: cr.id, answer },
                    {
                      onSuccess: () => showToast.updated('Clarification'),
                      onError: () => showToast.error('Failed to answer'),
                    }
                  );
                }
              : undefined
          }
        />
      ))}
    </div>
  );
}
