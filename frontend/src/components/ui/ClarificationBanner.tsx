import { AlertTriangle, MessageCircle, Clock, CheckCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useState } from 'react';
import { formatRelativeTime } from '@/lib/format';

interface ClarificationBannerProps {
  taskName: string;
  question: string;
  context?: string | null;
  askedBy?: string;
  askedAt: string;
  answer?: string | null;
  answeredBy?: string | null;
  answeredAt?: string | null;
  onAnswer?: (answer: string) => void;
  isBlocking?: boolean;
  state?: string;
}

export function ClarificationBanner({
  taskName,
  question,
  context,
  askedBy,
  askedAt,
  answer,
  answeredBy,
  answeredAt,
  onAnswer,
  isBlocking = false,
  state,
}: ClarificationBannerProps) {
  const [answerText, setAnswerText] = useState('');
  const isResolved = state === 'answered' || state === 'resolved';

  const handleSubmit = () => {
    if (answerText.trim() && onAnswer) {
      onAnswer(answerText.trim());
      setAnswerText('');
    }
  };

  return (
    <div className={`flex items-start gap-3 rounded-lg border p-3 ${isBlocking ? 'border-amber-500/30 bg-amber-500/5 dark:border-amber-500/20 dark:bg-amber-500/5' : 'border-border bg-card'}`}>
      <div className={`mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-md ${isBlocking ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400' : 'bg-blue-500/10 text-blue-600 dark:text-blue-400'}`}>
        {isBlocking ? <AlertTriangle className="h-3.5 w-3.5" /> : <MessageCircle className="h-3.5 w-3.5" />}
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium">{taskName}</p>
        <p className="mt-0.5 text-sm text-muted-foreground line-clamp-2">{question}</p>
        {context && (
          <p className="mt-1 text-xs text-muted-foreground italic line-clamp-2">Context: {context}</p>
        )}
        <div className="mt-1.5 flex items-center gap-2 text-xs text-muted-foreground">
          <Clock className="h-3 w-3" />
          <span>{formatRelativeTime(askedAt)}</span>
          {askedBy && <span>by {askedBy}</span>}
        </div>
        {answer && (
          <div className="mt-2 rounded-md bg-muted/50 p-2">
            <div className="flex items-center gap-1.5 text-xs text-emerald-600 dark:text-emerald-400">
              <CheckCircle className="h-3 w-3" />
              <span className="font-medium">Answered</span>
              {answeredBy && <span className="text-muted-foreground">by {answeredBy}</span>}
              {answeredAt && <span className="text-muted-foreground">{formatRelativeTime(answeredAt)}</span>}
            </div>
            <p className="mt-1 text-sm">{answer}</p>
          </div>
        )}
        {onAnswer && !isResolved && (
          <div className="mt-2 flex items-center gap-2">
            <Input
              value={answerText}
              onChange={(e) => setAnswerText(e.target.value)}
              placeholder="Type your answer..."
              className="h-8 text-sm"
              onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
            />
            <Button size="sm" onClick={handleSubmit} disabled={!answerText.trim()} className="h-8">
              Send
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
