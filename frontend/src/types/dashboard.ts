export interface Notification {
  id: string;
  type: string;
  title: string;
  message: string;
  entity_type: string | null;
  entity_id: string | null;
  is_read: boolean;
  created_at: string;
}

export interface AttentionDashboard {
  needs_review: AttentionItem[];
  open_questions: AttentionItem[];
  blocked_tasks: AttentionItem[];
  stale_claims: AttentionItem[];
  failed_dod: AttentionItem[];
  rejected_tasks: AttentionItem[];
  agent_verdicts_waiting: AttentionItem[];
  low_health_projects: AttentionItem[];
  recent_activity: AttentionItem[];
}

export interface AttentionItem {
  task_id?: string;
  round_id?: string;
  question_id?: string;
  project_id?: string;
  title?: string;
  name?: string;
  score?: number;
  [key: string]: unknown;
}

export interface ProjectHealth {
  score: number;
  breakdown: {
    blocked: number;
    stale_claims: number;
    failed_dod: number;
    open_clarifications: number;
    rejected: number;
  };
  top_issue: string;
}

export interface PortfolioOverview {
  total_projects: number;
  total_tasks: number;
  tasks_by_status: Record<string, number>;
  projects: PortfolioProject[];
}

export interface PortfolioProject {
  id: string;
  name: string;
  slug: string;
  task_count: number;
  tasks_done: number;
  tasks_total: number;
  health_score: number;
  top_issue: string;
}

export interface AgentActivityItem {
  agent_id: string;
  agent_name: string;
  task_id: string;
  task_title: string;
  claimed_at: string | null;
  last_heartbeat_at: string | null;
  progress_percent: number;
  current_step: string;
  is_stale: boolean;
}
