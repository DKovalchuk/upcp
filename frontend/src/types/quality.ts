export interface AcceptanceCriterion {
  id: string;
  task_id: string;
  description: string;
  status: string;
}

export interface AcceptanceCriterionCreate {
  description: string;
}

export interface AcceptanceCriterionUpdate {
  description?: string;
  status?: string;
}

export interface DoDItem {
  id: string;
  task_id: string;
  name: string;
  status: string;
}

export interface DoDItemCreate {
  name: string;
}

export interface DoDItemUpdate {
  name?: string;
  status?: string;
}
