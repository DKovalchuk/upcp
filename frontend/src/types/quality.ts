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
  required_evidence_type: string | null;
  status: string;
}

export interface DoDItemCreate {
  name: string;
  required_evidence_type?: string;
}

export interface DoDItemUpdate {
  name?: string;
  status?: string;
}

export interface Evidence {
  id: string;
  task_id: string;
  dod_item_id: string | null;
  type: string;
  title: string;
  description: string | null;
  url: string | null;
  content_snippet: string | null;
  artifact_ref: string | null;
  created_by_type: string;
  created_by_id: string;
  verification_state: string;
  verified_by_type: string | null;
  verified_by_id: string | null;
  verified_at: string | null;
  created_at: string;
}

export interface EvidenceCreate {
  type: string;
  title: string;
  description?: string;
  url?: string;
  content_snippet?: string;
  artifact_ref?: string;
  dod_item_id?: string;
  created_by_type?: string;
  created_by_id?: string;
}


export interface ReviewRound {
  id: string;
  task_id: string;
  requested_by_type: string;
  requested_by_id: string;
  reviewer_type: string | null;
  reviewer_id: string | null;
  state: string;
  verdict: string | null;
  confidence: number | null;
  summary: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}
