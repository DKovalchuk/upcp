import type { Report, ReportCreate } from '@/types/report';
import type { PaginatedResponse } from '@/types/api';
import { apiRequest, paginationParams } from './client';

export async function fetchReports(
  projectId: string,
  pagination?: { offset?: number; limit?: number }
): Promise<PaginatedResponse<Report>> {
  return apiRequest<PaginatedResponse<Report>>(
    `/api/v1/projects/${projectId}/reports${paginationParams(pagination)}`
  );
}

export async function fetchReport(id: string): Promise<Report> {
  return apiRequest<Report>(`/api/v1/reports/${id}`);
}

export async function createReport(projectId: string, data: ReportCreate): Promise<Report> {
  return apiRequest<Report>(`/api/v1/projects/${projectId}/reports/daily`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function exportReportMarkdown(
  reportId: string
): Promise<{ markdown: string }> {
  return apiRequest<{ markdown: string }>(`/api/v1/reports/${reportId}/markdown`);
}
