import React, { Suspense } from 'react';
import { Skeleton } from '@/components/ui/skeleton';
import type { Feature } from '@/types/feature';

const BoardView = React.lazy(() =>
  import('./BoardView').then((m) => ({ default: m.BoardView })),
);

interface LazyBoardViewProps {
  projectId: string;
  features: Feature[];
  search: string;
  onSelectTask: (taskId: string) => void;
}

function BoardFallback() {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {['Backlog', 'In Progress', 'Review', 'Done'].map((label) => (
        <div key={label} className="space-y-2">
          <Skeleton className="h-8 w-full" />
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-20 w-full rounded-lg" />
          ))}
        </div>
      ))}
    </div>
  );
}

export function LazyBoardView(props: LazyBoardViewProps) {
  return (
    <Suspense fallback={<BoardFallback />}>
      <BoardView {...props} />
    </Suspense>
  );
}
