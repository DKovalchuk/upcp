export interface Component {
  id: string;
  project_id: string;
  name: string;
  slug: string;
  description: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface ComponentCreate {
  name: string;
  slug?: string;
  description?: string;
  status?: string;
}

export interface ComponentUpdate {
  name?: string;
  slug?: string;
  description?: string;
  status?: string;
}
