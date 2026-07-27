export interface Subtask {
  id: string;
  task_id: string;
  title: string;
  description: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface SubtaskCreate {
  title: string;
  description?: string;
  status?: string;
}

export interface SubtaskUpdate {
  title?: string;
  description?: string;
  status?: string;
}
