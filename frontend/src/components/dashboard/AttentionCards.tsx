import { useQuery } from '@tanstack/react-query';
import { Link } from '@tanstack/react-router';
import {
  AlertTriangle,
  MessageCircle,
  Clock,
  TrendingDown,
  CheckCircle,
  Ban,
  Eye,
  HeartPulse,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { EmptyState } from '@/components/ui/EmptyState';
import { fetchAttentionDashboard } from '@/lib/api';
import type { AttentionItem } from '@/types/dashboard';

export function useAttentionDashboard() {
  return useQuery({
    queryKey: ['attention-dashboard'],
    queryFn: fetchAttentionDashboard,
    refetchInterval: 30_000,
    staleTime: 15_000,
  });
}

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

function TaskLink({
  taskId,
  projectId,
  children,
}: {
  taskId?: string;
  projectId?: string;
  children: React.ReactNode;
}) {
  if (taskId && projectId) {
    return (
      <Link
        to="/projects/$projectId/delivery"
        params={{ projectId }}
        className="block rounded-lg border p-2 text-sm transition-colors hover:bg-muted/50 hover:border-primary/30 cursor-pointer"
      >
        {children}
      </Link>
    );
  }
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
        <TaskLink taskId={item.task_id as string} projectId={item.project_id as string}>
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
        <TaskLink taskId={item.task_id as string} projectId={item.project_id as string}>
          <div className="flex items-start gap-2">
            <MessageCircle className="mt-0.5 h-3 w-3 shrink-0 text-amber-500" />
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
        <TaskLink taskId={item.task_id as string} projectId={item.project_id as string}>
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
        <TaskLink taskId={item.task_id as string} projectId={item.project_id as string}>
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
        <TaskLink taskId={item.task_id as string} projectId={item.project_id as string}>
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
        <TaskLink taskId={item.task_id as string} projectId={item.project_id as string}>
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
        <TaskLink taskId={item.task_id as string} projectId={item.project_id as string}>
          <div className="flex items-center gap-2">
            <span
              className={`rounded px-1.5 py-0.5 text-xs font-medium ${
                item.verdict === 'approve'
                  ? 'bg-emerald-500/10 text-emerald-600'
                  : 'bg-red-500/10 text-red-600'
              }`}
            >
              {item.verdict as string}
            </span>
            <span className="text-xs text-muted-foreground">
              {(item.confidence as number)?.toFixed(0)}% confidence
            </span>
          </div>
        </TaskLink>
      )}
    />
  );
}

export function LowHealthProjectsSection({ items }: { items: AttentionItem[] }) {
  if (!items || items.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-sm">
          <HeartPulse className="h-4 w-4" />
          Low Health Projects
          <span className="ml-auto rounded-full bg-red-500/10 px-2 py-0.5 text-xs font-medium text-red-600">
            {items.length}
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {items.map((item: AttentionItem) => {
            const score = Number(item.health_score) || 0;
            const color = score >= 50 ? 'bg-amber-500' : 'bg-red-500';
            const topIssue = item.top_issue ? String(item.top_issue) : null;
            const projectName = item.project_name ? String(item.project_name) : 'Unknown';
            const projectId = item.project_id ? String(item.project_id) : '';
            return (
              <Link
                key={projectId}
                to="/projects/$projectId"
                params={{ projectId }}
                className="block rounded-lg border p-2 text-sm transition-colors hover:bg-muted/50 hover:border-primary/30 cursor-pointer"
              >
                <div className="flex items-center justify-between">
                  <p className="font-medium">{projectName}</p>
                  <span className="text-xs font-medium text-muted-foreground">{score}%</span>
                </div>
                <div className="mt-1 h-1.5 w-full rounded-full bg-muted">
                  <div className={`h-full rounded-full ${color}`} style={{ width: `${score}%` }} />
                </div>
                {topIssue && (
                  <p className="mt-1 text-xs text-muted-foreground truncate">
                    {topIssue}
                  </p>
                )}
              </Link>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
