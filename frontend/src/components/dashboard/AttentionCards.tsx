import {
  AlertTriangle,
  MessageCircle,
  Clock,
  ShieldAlert,
  TrendingDown,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { EmptyState } from '@/components/ui/EmptyState';

interface AttentionSectionProps {
  title: string;
  emptyMessage: string;
  icon: LucideIcon;
}

function AttentionSection({ title, emptyMessage, icon: SectionIcon }: AttentionSectionProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <SectionIcon className="h-4 w-4" />
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <EmptyState
          icon={SectionIcon}
          title={emptyMessage}
        />
      </CardContent>
    </Card>
  );
}

export function NeedsReviewSection() {
  return (
    <AttentionSection
      title="Needs Your Review"
      icon={ShieldAlert}
      emptyMessage="No items awaiting review"
    />
  );
}

export function OpenClarificationsSection() {
  return (
    <AttentionSection
      title="Open Clarifications"
      icon={MessageCircle}
      emptyMessage="No open questions"
    />
  );
}

export function BlockedTasksSection() {
  return (
    <AttentionSection
      title="Blocked Tasks"
      icon={AlertTriangle}
      emptyMessage="No blocked tasks"
    />
  );
}

export function StaleAgentsSection() {
  return (
    <AttentionSection
      title="Stale Agents"
      icon={Clock}
      emptyMessage="All agents are active"
    />
  );
}

export function FailedQualityGatesSection() {
  return (
    <AttentionSection
      title="Failed Quality Gates"
      icon={TrendingDown}
      emptyMessage="All quality gates passing"
    />
  );
}
