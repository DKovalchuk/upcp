export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface ErrorResponse {
  error: string;
  detail: string;
}

export interface HealthResponse {
  status: string;
  service: string;
}
