export interface Task {
  id: string;
  feature_id: string;
  title: string;
  description: string | null;
  status: string;
  priority: number;
  assignee_type: string | null;
  assignee_id: string | null;
  component_id: string | null;
  module_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface TaskCreate {
  title: string;
  description?: string;
  status?: string;
  priority?: number;
  assignee_type?: string;
  assignee_id?: string;
  component_id?: string;
  module_id?: string;
}

export interface TaskUpdate {
  title?: string;
  description?: string;
  status?: string;
  priority?: number;
  assignee_type?: string;
  assignee_id?: string;
  component_id?: string;
  module_id?: string;
}

export interface TaskClaim {
  id: string;
  task_id: string;
  agent_id: string;
  state: string;
  claimed_at: string | null;
}

export interface Heartbeat {
  id: string;
  claim_id: string;
  progress_percent: number;
  current_step: string;
  next_step: string;
  blockers: string | null;
  eta: string | null;
  created_at: string;
}

export interface ClarificationRequest {
  id: string;
  task_id: string;
  author_type: string;
  author_id: string;
  question: string;
  context: string | null;
  blocking: boolean;
  state: string;
  answer: string | null;
  answered_by: string | null;
  answered_at: string | null;
  created_at: string;
}

export interface AgentMe {
  id: string;
  name: string;
  description: string | null;
  is_active: boolean;
  scopes: Record<string, unknown> | null;
  inbox_count: number;
  created_at: string;
}

export interface AgentEvent {
  id: string;
  type: string;
  task_id: string;
  message: string;
  created_at: string;
}
