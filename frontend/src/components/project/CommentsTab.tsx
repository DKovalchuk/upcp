// Comments Tab for TaskDetailSheet — TASK-0118

import { useState } from 'react';
import { useComments, useCreateComment } from '@/hooks/use-tasks';
import { EmptyState } from '@/components/ui/EmptyState';
import { Button } from '@/components/ui/button';
import { formatRelativeTime } from '@/lib/format';
import { showToast } from '@/lib/toast';
import { MessageSquare, Reply, Send } from 'lucide-react';

interface CommentsTabProps {
  taskId: string;
}

export function CommentsTab({ taskId }: CommentsTabProps) {
  const { data: comments, isLoading } = useComments(taskId);
  const createComment = useCreateComment(taskId);
  const [newBody, setNewBody] = useState('');
  const [replyTo, setReplyTo] = useState<string | null>(null);

  const items = comments ?? [];
  const topLevel = items.filter((c) => !c.parent_id);
  const replies = items.filter((c) => c.parent_id);

  const getReplies = (parentId: string) => replies.filter((r) => r.parent_id === parentId);

  const handleSubmit = async () => {
    if (!newBody.trim()) return;
    await createComment.mutateAsync({
      body: newBody.trim(),
      parentId: replyTo ?? undefined,
    });
    showToast.created('Comment');
    setNewBody('');
    setReplyTo(null);
  };

  if (isLoading) {
    return <div className="text-sm text-muted-foreground">Loading...</div>;
  }

  return (
    <div className="space-y-3">
      <h4 className="text-sm font-medium">Comments ({items.length})</h4>

      {items.length === 0 ? (
        <EmptyState icon={MessageSquare} title="No comments" description="Start a discussion about this task" />
      ) : (
        <div className="space-y-2">
          {topLevel.map((c) => (
            <div key={c.id} className="rounded-md border p-3">
              <div className="flex items-start gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium">{c.author_id}</span>
                    <span className="text-xs text-muted-foreground">
                      {c.created_at ? formatRelativeTime(c.created_at) : ''}
                    </span>
                  </div>
                  <p className="mt-1 text-sm whitespace-pre-wrap">{c.body}</p>
                </div>
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-6 w-6 p-0 shrink-0"
                  onClick={() => setReplyTo(c.id)}
                >
                  <Reply className="h-3 w-3" />
                </Button>
              </div>
              {getReplies(c.id).map((r) => (
                <div key={r.id} className="ml-6 mt-2 border-l-2 pl-3">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium">{r.author_id}</span>
                    <span className="text-xs text-muted-foreground">
                      {r.created_at ? formatRelativeTime(r.created_at) : ''}
                    </span>
                  </div>
                  <p className="mt-1 text-sm whitespace-pre-wrap">{r.body}</p>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}

      {/* Reply indicator */}
      {replyTo && (
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Reply className="h-3 w-3" />
          Replying to comment
          <Button size="sm" variant="ghost" className="h-5 text-xs" onClick={() => setReplyTo(null)}>
            Cancel
          </Button>
        </div>
      )}

      {/* New comment input */}
      <div className="flex gap-2">
        <textarea
          value={newBody}
          onChange={(e) => setNewBody(e.target.value)}
          placeholder={replyTo ? 'Write a reply...' : 'Write a comment...'}
          className="flex-1 rounded-md border bg-background px-3 py-2 text-sm resize-none min-h-[60px]"
          rows={2}
        />
        <Button
          size="sm"
          onClick={handleSubmit}
          disabled={!newBody.trim() || createComment.isPending}
          className="self-end"
        >
          <Send className="h-3 w-3" />
        </Button>
      </div>
    </div>
  );
}
