export interface Module {
  id: string;
  component_id: string;
  name: string;
  slug: string;
  description: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface ModuleCreate {
  name: string;
  slug?: string;
  description?: string;
  status?: string;
}

export interface ModuleUpdate {
  name?: string;
  slug?: string;
  description?: string;
  status?: string;
}
