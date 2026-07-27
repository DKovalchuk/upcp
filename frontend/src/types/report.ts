export interface Report {
  id: string;
  project_id: string;
  report_type: string;
  content: Record<string, unknown> | null;
  summary: string | null;
  created_at: string;
}

export interface ReportCreate {
  report_type: string;
  content?: Record<string, unknown>;
}

export interface ReportSummary {
  summary: string;
}
