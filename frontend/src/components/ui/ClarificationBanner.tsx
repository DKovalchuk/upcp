import { AlertTriangle, MessageCircle, Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { formatRelativeTime } from '@/lib/format';

interface ClarificationBannerProps {
  taskName: string;
  question: string;
  askedBy?: string;
  askedAt: string;
  onAnswer?: () => void;
  isBlocking?: boolean;
}

export function ClarificationBanner({
  taskName,
  question,
  askedBy,
  askedAt,
  onAnswer,
  isBlocking = false,
}: ClarificationBannerProps) {
  return (
    <div className={`flex items-start gap-3 rounded-lg border p-3 ${isBlocking ? 'border-amber-500/30 bg-amber-500/5 dark:border-amber-500/20 dark:bg-amber-500/5' : 'border-border bg-card'}`}>
      <div className={`mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-md ${isBlocking ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400' : 'bg-blue-500/10 text-blue-600 dark:text-blue-400'}`}>
        {isBlocking ? <AlertTriangle className="h-3.5 w-3.5" /> : <MessageCircle className="h-3.5 w-3.5" />}
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium">{taskName}</p>
        <p className="mt-0.5 text-sm text-muted-foreground line-clamp-2">{question}</p>
        <div className="mt-1.5 flex items-center gap-2 text-xs text-muted-foreground">
          <Clock className="h-3 w-3" />
          <span>{formatRelativeTime(askedAt)}</span>
          {askedBy && <span>by {askedBy}</span>}
        </div>
      </div>
      {onAnswer && (
        <Button variant="outline" size="sm" onClick={onAnswer} className="shrink-0">
          Answer
        </Button>
      )}
    </div>
  );
}
