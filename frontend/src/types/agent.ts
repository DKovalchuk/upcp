// Agent types — TASK-0099 Sprint 2

export interface AgentProfile {
  id: string;
  name: string;
  description: string | null;
  is_active: boolean;
  created_by: string | null;
  created_at: string;
}

export interface AgentMetrics {
  tasks_completed: number;
  tasks_failed: number;
  success_rate: number | null;
  current_task_id: string | null;
  current_task_title: string | null;
  current_progress_percent: number | null;
  last_heartbeat_at: string | null;
  is_stale: boolean;
  status: 'working' | 'idle' | 'blocked' | 'offline' | 'stale';
}

export interface AgentWithMetrics extends AgentProfile {
  metrics: AgentMetrics;
  tokens: AgentTokenSummary[];
}

export interface AgentTokenSummary {
  id: string;
  name: string;
  scopes: Record<string, unknown> | null;
  revoked_at: string | null;
  last_used_at: string | null;
  created_at: string;
}

export interface AgentListResponse {
  items: AgentProfile[];
  total: number;
  offset: number;
  limit: number;
}

export interface AgentCreate {
  name: string;
  description?: string;
}

export interface AgentUpdate {
  name?: string;
  description?: string;
  is_active?: boolean;
}

export interface AgentClaim {
  id: string;
  task_id: string;
  task_title: string | null;
  state: string;
  claimed_at: string | null;
  released_at: string | null;
  last_heartbeat_at: string | null;
}

export interface AgentActivityEvent {
  id: string;
  event_type: string;
  task_id: string | null;
  message: string;
  is_read: boolean;
  created_at: string | null;
}

export interface AgentClarification {
  id: string;
  task_id: string;
  question: string;
  state: string;
  blocking: boolean;
  created_at: string | null;
}
