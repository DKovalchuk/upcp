import { Skeleton } from '@/components/ui/skeleton';

interface PageSkeletonProps {
  rows?: number;
  hasHeader?: boolean;
  hasTable?: boolean;
  hasCards?: boolean;
  cardCount?: number;
}

export function PageSkeleton({
  rows = 5,
  hasHeader = true,
  hasTable = true,
  hasCards = false,
  cardCount = 4,
}: PageSkeletonProps) {
  return (
    <div className="space-y-6">
      {hasHeader && (
        <div className="space-y-2">
          <Skeleton className="h-8 w-[250px]" />
          <Skeleton className="h-4 w-[400px]" />
        </div>
      )}

      {hasCards && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: cardCount }).map((_, i) => (
            <Skeleton key={i} className="h-[120px] w-full rounded-lg" />
          ))}
        </div>
      )}

      {hasTable && (
        <div className="space-y-3">
          <Skeleton className="h-10 w-full" />
          {Array.from({ length: rows }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      )}
    </div>
  );
}
