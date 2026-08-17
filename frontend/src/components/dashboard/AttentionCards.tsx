import { useQuery } from '@tanstack/react-query';
import {
  AlertTriangle,
  MessageCircle,
  Clock,
  TrendingDown,
  CheckCircle,
  Ban,
  Eye,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { EmptyState } from '@/components/ui/EmptyState';
import { fetchAttentionDashboard } from '@/lib/api';
import type { AttentionItem } from '@/types/dashboard';

interface AttentionSectionProps {
  title: string;
  emptyMessage: string;
  icon: LucideIcon;
  count: number;
  items: AttentionItem[];
  renderItem: (item: AttentionItem) => React.ReactNode;
}

function AttentionSection({
  title,
  emptyMessage,
  icon: SectionIcon,
  count,
  items,
  renderItem,
}: AttentionSectionProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-sm">
          <SectionIcon className="h-4 w-4" />
          {title}
          {count > 0 && (
            <span className="ml-auto rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
              {count}
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <EmptyState icon={SectionIcon} title={emptyMessage} />
        ) : (
          <div className="space-y-2">{items.map(renderItem)}</div>
        )}
      </CardContent>
    </Card>
  );
}

function TaskLink({ children }: { children: React.ReactNode }) {
  return (
    <div className="block rounded-lg border p-2 text-sm">
      {children}
    </div>
  );
}

export function NeedsReviewSection({ items }: { items: AttentionItem[] }) {
  return (
    <AttentionSection
      title="Needs Your Review"
      icon={Eye}
      emptyMessage="No items awaiting review"
      count={items.length}
      items={items}
      renderItem={(item) => (
        <TaskLink>
          <p className="font-medium">{(item.task_id as string)?.slice(0, 8)}</p>
          <p className="text-xs text-muted-foreground">
            by {item.requested_by as string}
          </p>
        </TaskLink>
      )}
    />
  );
}

export function OpenClarificationsSection({ items }: { items: AttentionItem[] }) {
  return (
    <AttentionSection
      title="Open Questions"
      icon={MessageCircle}
      emptyMessage="No open questions"
      count={items.length}
      items={items}
      renderItem={(item) => (
        <TaskLink>
          <div className="flex items-start gap-2">
            <Ban className="mt-0.5 h-3 w-3 shrink-0 text-red-500" />
            <div className="min-w-0">
              <p className="truncate font-medium">
                {item.question as string}
              </p>
              <p className="text-xs text-muted-foreground">
                from {item.author as string}
              </p>
            </div>
          </div>
        </TaskLink>
      )}
    />
  );
}

export function BlockedTasksSection({ items }: { items: AttentionItem[] }) {
  return (
    <AttentionSection
      title="Blocked Tasks"
      icon={AlertTriangle}
      emptyMessage="No blocked tasks"
      count={items.length}
      items={items}
      renderItem={(item) => (
        <TaskLink>
          <p className="font-medium">{item.title as string}</p>
        </TaskLink>
      )}
    />
  );
}

export function StaleAgentsSection({ items }: { items: AttentionItem[] }) {
  return (
    <AttentionSection
      title="Stale Agent Claims"
      icon={Clock}
      emptyMessage="All agents are active"
      count={items.length}
      items={items}
      renderItem={(item) => (
        <TaskLink>
          <p className="font-medium">{(item.task_id as string)?.slice(0, 8)}</p>
          <p className="text-xs text-muted-foreground">
            agent: {item.agent_id as string}
          </p>
        </TaskLink>
      )}
    />
  );
}

export function FailedQualityGatesSection({ items }: { items: AttentionItem[] }) {
  return (
    <AttentionSection
      title="Failed Quality Gates"
      icon={TrendingDown}
      emptyMessage="All quality gates passing"
      count={items.length}
      items={items}
      renderItem={(item) => (
        <TaskLink>
          <p className="font-medium">{(item.task_id as string)?.slice(0, 8)}</p>
          <p className="text-xs text-muted-foreground">
            failed: {(item.failed_items as string[])?.join(', ')}
          </p>
        </TaskLink>
      )}
    />
  );
}

export function RejectedTasksSection({ items }: { items: AttentionItem[] }) {
  return (
    <AttentionSection
      title="Rejected Tasks"
      icon={Ban}
      emptyMessage="No rejected tasks"
      count={items.length}
      items={items}
      renderItem={(item) => (
        <TaskLink>
          <p className="font-medium">{(item.task_id as string)?.slice(0, 8)}</p>
          <p className="text-xs text-muted-foreground">
            {item.summary as string}
          </p>
        </TaskLink>
      )}
    />
  );
}

export function AgentVerdictsSection({ items }: { items: AttentionItem[] }) {
  return (
    <AttentionSection
      title="Verdicts Waiting"
      icon={CheckCircle}
      emptyMessage="No verdicts awaiting confirmation"
      count={items.length}
      items={items}
      renderItem={(item) => (
        <TaskLink>
          <div className="flex items-center gap-2">
            <span className={`rounded px-1.5 py-0.5 text-xs font-medium ${
              item.verdict === 'approve'
                ? 'bg-emerald-500/10 text-emerald-600'
                : 'bg-red-500/10 text-red-600'
            }`}>
              {item.verdict as string}
            </span>
            <span className="text-xs text-muted-foreground">
              confidence: {item.confidence as number}%
            </span>
          </div>
        </TaskLink>
      )}
    />
  );
}

// eslint-disable-next-line react/only-export-components
export function useAttentionDashboard() {
  return useQuery({
    queryKey: ['dashboard', 'attention'],
    queryFn: fetchAttentionDashboard,
    refetchInterval: 30000,
    staleTime: 15000,
  });
}
