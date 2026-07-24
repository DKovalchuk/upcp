export interface Project {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreate {
  name: string;
  slug?: string;
  description?: string;
  status?: string;
}

export interface ProjectUpdate {
  name?: string;
  slug?: string;
  description?: string;
  status?: string;
}