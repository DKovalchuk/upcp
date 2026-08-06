import type { GitProvider, GitProviderCreate, GitBranch, GitCommit, GitLink } from '@/types/git';
import { apiRequest } from './client';

// ── Git Providers ──

export async function fetchGitProviders(projectId: string): Promise<GitProvider[]> {
  return apiRequest<GitProvider[]>(`/api/v1/projects/${projectId}/git-providers`);
}

export async function createGitProvider(
  projectId: string,
  data: GitProviderCreate
): Promise<GitProvider> {
  return apiRequest<GitProvider>(`/api/v1/projects/${projectId}/git-providers`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function deleteGitProvider(id: string): Promise<void> {
  return apiRequest<void>(`/api/v1/git-providers/${id}`, {
    method: 'DELETE',
  });
}

// ── Git Branches ──

export async function fetchGitBranches(providerId: string): Promise<GitBranch[]> {
  return apiRequest<GitBranch[]>(`/api/v1/git-providers/${providerId}/branches`);
}

// ── Git Commits ──

export async function fetchGitCommits(
  providerId: string,
  limit = 20
): Promise<GitCommit[]> {
  return apiRequest<GitCommit[]>(
    `/api/v1/git-providers/${providerId}/commits?limit=${limit}`
  );
}

// ── Git Links ──

export async function fetchGitLinks(
  entityType: string,
  entityId: string
): Promise<GitLink[]> {
  return apiRequest<GitLink[]>(
    `/api/v1/git-links?entity_type=${entityType}&entity_id=${entityId}`
  );
}

export async function createGitLink(
  data: Omit<GitLink, 'id'>
): Promise<GitLink> {
  return apiRequest<GitLink>('/api/v1/git-links', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function deleteGitLink(id: string): Promise<void> {
  return apiRequest<void>(`/api/v1/git-links/${id}`, {
    method: 'DELETE',
  });
}
