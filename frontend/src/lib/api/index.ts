// Re-export all domain modules
export * from './projects';
export * from './components';
export * from './modules';
export * from './features';
export * from './tasks';
export * from './quality';
export * from './dashboard';
export * from './git';
export * from './reports';
export * from './audit';
export * from './agents';
export * from './client';

// Search and health are small enough to keep here
import { apiRequest } from './client';

export interface SearchResult {
  entity_type: string;
  id: string;
  title: string;
  subtitle: string;
  url: string;
}

export async function searchGlobal(
  query: string,
  limit = 20
): Promise<SearchResult[]> {
  return apiRequest<SearchResult[]>(
    `/api/v1/search?q=${encodeURIComponent(query)}&limit=${limit}`
  );
}

export async function fetchHealth() {
  return apiRequest<import('@/types/api').HealthResponse>('/api/v1/health');
}
