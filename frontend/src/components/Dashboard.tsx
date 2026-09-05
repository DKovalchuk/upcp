import { Link, useNavigate, useSearch } from '@tanstack/react-router';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { PageSkeleton } from '@/components/ui/PageSkeleton';
import { ErrorState } from '@/components/ui/ErrorState';
import { EmptyState } from '@/components/ui/EmptyState';
import { formatRelativeTime } from '@/lib/format';
import {
  FolderKanban,
  GitBranch,
  CalendarCheck,
  Ban,
  HeartPulse,
  ArrowRight,
} from 'lucide-react';
import {
  NeedsReviewSection,
  OpenClarificationsSection,
  BlockedTasksSection,
  StaleAgentsSection,
  FailedQualityGatesSection,
  RejectedTasksSection,
  AgentVerdictsSection,
  LowHealthProjectsSection,
  useAttentionDashboard,
} from '@/components/dashboard/AttentionCards';
import { LiveActivityFeed } from '@/components/dashboard/LiveActivityFeed';
import { AgentActivitySummary } from '@/components/dashboard/AgentActivitySummary';
import { TaskDistributionDonut } from '@/components/dashboard/TaskDistributionDonut';
import { VelocityChart } from '@/components/dashboard/VelocityChart';
import { PortfolioTable } from '@/components/dashboard/PortfolioTable';
import { ProjectSelector } from '@/components/dashboard/ProjectSelector';
import { useGlobalVelocity } from '@/hooks/use-analytics';
import { useDashboardStats, usePortfolioOverview } from '@/hooks/use-dashboard';

// ── Health Score Color ──────────────────────────────────────

function healthVariant(score: number): 'success' | 'warning' | 'error' {
  if (score >= 80) return 'success';
  if (score >= 50) return 'warning';
  return 'error';
}

function healthColor(score: number): string {
  if (score >= 80) return 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400';
  if (score >= 50) return 'bg-amber-500/10 text-amber-600 dark:text-amber-400';
  return 'bg-red-500/10 text-red-600 dark:text-red-400';
}

// ── Stat Card ───────────────────────────────────────────────

const STAT_CARD_STYLES = {
  default: 'border-l-4 border-l-primary',
  warning: 'border-l-4 border-l-amber-500 bg-amber-500/5 dark:bg-amber-500/5',
  error: 'border-l-4 border-l-red-500 bg-red-500/5 dark:bg-red-500/5',
  info: 'border-l-4 border-l-blue-500 bg-blue-500/5 dark:bg-blue-500/5',
  success: 'border-l-4 border-l-emerald-500 bg-emerald-500/5 dark:bg-emerald-500/5',
} as const;

function StatCard({
  label,
  value,
  icon: Icon,
  color,
  variant = 'default',
  to,
}: {
  label: string;
  value: number | string;
  icon: React.ElementType;
  color: string;
  variant?: keyof typeof STAT_CARD_STYLES;
  to?: string;
}) {
  const content = (
    <Card
      className={`transition-all ${to ? 'cursor-pointer hover:shadow-md hover:ring-1 hover:ring-ring/20' : ''} ${STAT_CARD_STYLES[variant]}`}
    >
      <CardContent className="flex items-center gap-4 p-4">
        <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${color}`}>
          <Icon className="h-5 w-5" />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-2xl font-bold tracking-tight">{value}</p>
          <p className="text-sm text-muted-foreground">{label}</p>
        </div>
        {to && (
          <ArrowRight className="h-4 w-4 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
        )}
      </CardContent>
    </Card>
  );

  if (to) {
    return (
      <Link to={to} className="group block">
        {content}
      </Link>
    );
  }
  return content;
}

// ── Dashboard ───────────────────────────────────────────────

export function Dashboard() {
  const search = useSearch({ strict: false }) as Record<string, string | undefined>;
  const projectId = search.project_id;
  const { data: stats, isLoading, error } = useDashboardStats(projectId);
  const { data: attention } = useAttentionDashboard();
  const { data: velocityData, isLoading: velocityLoading } = useGlobalVelocity(8, projectId);
  const { data: portfolio, isLoading: portfolioLoading } = usePortfolioOverview();
  const navigate = useNavigate();

  if (isLoading) {
    return <PageSkeleton hasCards cardCount={5} rows={5} />;
  }

  if (error) {
    return <ErrorState message="Failed to load dashboard data" />;
  }

  if (stats && stats.project_count === 0) {
    return (
      <EmptyState
        icon={FolderKanban}
        title="No projects yet"
        description="Create your first project to get started with UPCP."
        action={{ label: 'New Project', onClick: () => navigate({ to: '/projects' }) }}
      />
    );
  }

  const tc = stats?.task_counts_by_status;
  const activeTasks = (tc?.in_progress ?? 0) + (stats?.claimed_count ?? 0) + (tc?.blocked ?? 0);
  const health = stats?.health_score ?? 100;

  return (
    <div className="space-y-6 animate-fade-in-up">
      {/* ── Project Selector ── */}
      <div className="flex items-center justify-between">
        <div />
        <ProjectSelector />
      </div>

      {/* ── Row 1: KPI Cards ── */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5 animate-stagger">
        <StatCard
          label="Projects"
          value={stats?.project_count ?? 0}
          icon={FolderKanban}
          color="bg-primary/10 text-primary"
          variant="default"
          to="/projects"
        />
        <StatCard
          label="Active Tasks"
          value={activeTasks}
          icon={GitBranch}
          color="bg-blue-500/10 text-blue-600 dark:text-blue-400"
          variant="info"
          to="/delivery?status=in_progress,claimed,blocked"
        />
        <StatCard
          label="Done This Week"
          value={stats?.done_this_week ?? 0}
          icon={CalendarCheck}
          color="bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
          variant="success"
          to="/delivery?status=done"
        />
        <StatCard
          label="Blocked"
          value={stats?.blocked_count ?? 0}
          icon={Ban}
          color="bg-red-500/10 text-red-600 dark:text-red-400"
          variant={stats?.blocked_count ? 'error' : 'success'}
          to="/delivery?status=blocked"
        />
        <StatCard
          label="Health Score"
          value={`${health}%`}
          icon={HeartPulse}
          color={healthColor(health)}
          variant={healthVariant(health)}
        />
      </div>

      {/* ── Row 2: Charts ── */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="lg:col-span-1">
          <TaskDistributionDonut counts={tc} />
        </div>
        <div className="lg:col-span-2">
          <VelocityChart data={velocityData?.items} isLoading={velocityLoading} />
        </div>
      </div>

      {/* ── Row 3: Attention Dashboard ── */}
      <div>
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-3">
          Needs Attention
        </h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          <NeedsReviewSection items={attention?.needs_review ?? []} />
          <OpenClarificationsSection items={attention?.open_questions ?? []} />
          <BlockedTasksSection items={attention?.blocked_tasks ?? []} />
          <StaleAgentsSection items={attention?.stale_claims ?? []} />
          <FailedQualityGatesSection items={attention?.failed_dod ?? []} />
          <RejectedTasksSection items={attention?.rejected_tasks ?? []} />
          <AgentVerdictsSection items={attention?.agent_verdicts_waiting ?? []} />
          <LowHealthProjectsSection items={attention?.low_health_projects ?? []} />
        </div>
      </div>

      {/* ── Row 4: Activity & Agents ── */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <LiveActivityFeed />
        </div>
        <div>
          <AgentActivitySummary />
        </div>
      </div>

      {/* ── Row 5: Portfolio ── */}
      <PortfolioTable projects={portfolio?.projects} isLoading={portfolioLoading} />

      {/* ── Row 6: Recent Projects ── */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Projects</CardTitle>
        </CardHeader>
        <CardContent>
          {!stats?.recent_projects?.length ? (
            <p className="text-sm text-muted-foreground py-4 text-center">
              No recent projects.
            </p>
          ) : (
            <div className="space-y-2">
              {stats.recent_projects.map((project) => (
                <Link
                  key={project.id}
                  to="/projects/$projectId"
                  params={{ projectId: project.id }}
                  className="flex items-center justify-between rounded-lg border border-border p-3 transition-all hover:bg-muted/50 hover:ring-1 hover:ring-ring/20 group"
                >
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-medium group-hover:text-primary transition-colors">{project.name}</p>
                    {project.description && (
                      <p className="truncate text-sm text-muted-foreground">
                        {project.description}
                      </p>
                    )}
                  </div>
                  <div className="ml-4 flex items-center gap-3">
                    <StatusBadge status={project.status} />
                    <span className="whitespace-nowrap text-xs text-muted-foreground">
                      {formatRelativeTime(project.updated_at)}
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
