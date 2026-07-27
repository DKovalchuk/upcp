export interface Feature {
  id: string;
  project_id: string;
  name: string;
  slug: string;
  description: string | null;
  status: string;
  component_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface FeatureCreate {
  name: string;
  slug?: string;
  description?: string;
  status?: string;
  component_id?: string;
}

export interface FeatureUpdate {
  name?: string;
  slug?: string;
  description?: string;
  status?: string;
  component_id?: string;
}
