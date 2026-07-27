import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchReports, fetchReport, createReport } from '@/lib/api';
import type { ReportCreate } from '@/types/report';

export function useReports(
  projectId: string,
  pagination?: { offset?: number; limit?: number }
) {
  return useQuery({
    queryKey: ['reports', projectId, pagination],
    queryFn: () => fetchReports(projectId, pagination),
    enabled: !!projectId,
  });
}

export function useReport(id: string) {
  return useQuery({
    queryKey: ['reports', id],
    queryFn: () => fetchReport(id),
    enabled: !!id,
  });
}

export function useCreateReport() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      projectId,
      data,
    }: {
      projectId: string;
      data: ReportCreate;
    }) => createReport(projectId, data),
    onSuccess: (_, { projectId }) => {
      queryClient.invalidateQueries({ queryKey: ['reports', projectId] });
    },
  });
}
