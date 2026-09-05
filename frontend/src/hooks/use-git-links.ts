import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchGitLinks, createGitLink, deleteGitLink } from '@/lib/api/git';
import type { GitLink } from '@/types/git';

export function useGitLinks(entityType: string, entityId: string) {
  return useQuery({
    queryKey: ['git-links', entityType, entityId],
    queryFn: () => fetchGitLinks(entityType, entityId),
    enabled: !!entityId,
  });
}

export function useCreateGitLink() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Omit<GitLink, 'id'>) => createGitLink(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['git-links'] }),
  });
}

export function useDeleteGitLink() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteGitLink(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['git-links'] }),
  });
}
