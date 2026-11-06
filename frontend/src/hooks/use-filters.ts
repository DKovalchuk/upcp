import { useCallback, useMemo } from 'react';
import { useNavigate, useSearch } from '@tanstack/react-router';

export interface FilterState {
  search?: string;
  status?: string;
  priority?: string;
  [key: string]: string | undefined;
}

export function useFilters() {
  const navigate = useNavigate();
  const search = useSearch({ strict: false }) as Record<string, string | undefined>;

  const filters: FilterState = useMemo(() => {
    const result: FilterState = {};
    for (const [key, value] of Object.entries(search)) {
      if (value !== undefined && value !== '' && key !== 'project_id') {
        result[key] = value;
      }
    }
    return result;
  }, [search]);

  const setFilter = useCallback(
    (key: string, value: string | undefined) => {
      const newSearch = { ...search };
      if (value === undefined || value === '') {
        delete newSearch[key];
      } else {
        newSearch[key] = value;
      }
      // Documented escape (TASK-0155): routes are registered without
      // search validators — typed navigate() accepts only
      // true | ParamsReducerFn for search, so object-form needs a cast
      // (probe: TS2322). Fix belongs to router search-validator typing.
      navigate({ search: newSearch as any });
    },
    [navigate, search],
  );

  const clearFilters = useCallback(() => {
    const newSearch: Record<string, string> = {};
    if (search.project_id) newSearch.project_id = search.project_id;
    navigate({ search: newSearch as any });
  }, [navigate, search]);

  const hasActiveFilters = useMemo(() => {
    return Object.keys(filters).length > 0;
  }, [filters]);

  return { filters, setFilter, clearFilters, hasActiveFilters };
}
