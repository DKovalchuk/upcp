export interface GitProvider {
  id: string;
  name: string;
  provider_type: string;
  url: string;
  status: string;
}

export interface GitBranch {
  id: string;
  name: string;
  last_commit_sha: string | null;
  is_default: boolean;
}

export interface GitCommit {
  id: string;
  sha: string;
  message: string;
  author: string;
  committed_at: string;
}

export interface GitLink {
  id: string;
  entity_type: string;
  entity_id: string;
  git_type: string;
  git_id: string;
}

export interface GitProviderCreate {
  name: string;
  provider_type: string;
  url: string;
}
