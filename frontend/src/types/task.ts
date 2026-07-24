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
