import { useCallback, useMemo } from 'react';

interface UseUrlPaginationReturn {
  offset: number;
  limit: number;
  page: number;
  pageSize: number;
  setOffset: (offset: number) => void;
  setPageSize: (size: number) => void;
}

function getUrlParam(key: string, fallback: number): number {
  if (typeof window === 'undefined') return fallback;
  const params = new URLSearchParams(window.location.search);
  return Number(params.get(key)) || fallback;
}

function setUrlParams(params: Record<string, string>) {
  const url = new URL(window.location.href);
  for (const [key, value] of Object.entries(params)) {
    url.searchParams.set(key, value);
  }
  window.history.replaceState({}, '', url.toString());
  window.dispatchEvent(new PopStateEvent('popstate'));
}

export function useUrlPagination(defaultPageSize = 20): UseUrlPaginationReturn {
  const page = getUrlParam('page', 1);
  const pageSize = getUrlParam('pageSize', defaultPageSize);
  const offset = (page - 1) * pageSize;

  const setOffset = useCallback(
    (newOffset: number) => {
      const newPage = Math.floor(newOffset / pageSize) + 1;
      setUrlParams({ page: String(newPage), pageSize: String(pageSize) });
    },
    [pageSize]
  );

  const setPageSize = useCallback((newSize: number) => {
    setUrlParams({ page: '1', pageSize: String(newSize) });
  }, []);

  return useMemo(
    () => ({ offset, limit: pageSize, page, pageSize, setOffset, setPageSize }),
    [offset, pageSize, page, setOffset, setPageSize]
  );
}
