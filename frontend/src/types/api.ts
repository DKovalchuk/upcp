export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  offset: number;
  limit: number;
}

export interface ErrorResponse {
  error: string;
  detail: string;
}

export interface HealthCheckResult {
  status: string;
  latency_ms?: number;
  error?: string;
}

export interface HealthResponse {
  status: string;
  service: string;
  db: HealthCheckResult;
  redis: HealthCheckResult;
}

export interface ProjectSummary {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface AuditEventSummary {
  id: string;
  timestamp: string;
  event_type: string;
  entity_type: string;
  entity_id: string;
  actor_type: string;
  actor_id: string;
  payload: Record<string, unknown> | null;
  note: string | null;
}

export interface TaskCountsByStatus {
  backlog: number;
  in_progress: number;
  review: number;
  done: number;
}

export interface DashboardStatsResponse {
  project_count: number;
  task_counts_by_status: TaskCountsByStatus;
  recent_projects: ProjectSummary[];
  recent_activity: AuditEventSummary[];
}

export interface QualityStatsResponse {
  total_tasks: number;
  tasks_with_ac: number;
  total_ac: number;
  passed_ac: number;
  total_dod: number;
  passed_dod: number;
  pass_rate: number;
}
