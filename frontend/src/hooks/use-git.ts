import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchGitProviders,
  createGitProvider,
  deleteGitProvider,
  fetchGitBranches,
  fetchGitCommits,
} from '@/lib/api';
import type { GitProviderCreate } from '@/types/git';

export function useGitProviders(projectId: string) {
  return useQuery({
    queryKey: ['git-providers', projectId],
    queryFn: () => fetchGitProviders(projectId),
    enabled: !!projectId,
    staleTime: 2 * 60_000,
  });
}

export function useCreateGitProvider() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      projectId,
      data,
    }: {
      projectId: string;
      data: GitProviderCreate;
    }) => createGitProvider(projectId, data),
    onSuccess: (_, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: ['git-providers', projectId] });
    },
  });
}

export function useDeleteGitProvider() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteGitProvider(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['git-providers'] });
    },
  });
}

export function useGitBranches(providerId: string) {
  return useQuery({
    queryKey: ['git-branches', providerId],
    queryFn: () => fetchGitBranches(providerId),
    enabled: !!providerId,
    staleTime: 2 * 60_000,
  });
}

export function useGitCommits(providerId: string, limit = 20) {
  return useQuery({
    queryKey: ['git-commits', providerId, limit],
    queryFn: () => fetchGitCommits(providerId, limit),
    enabled: !!providerId,
    staleTime: 2 * 60_000,
  });
}
