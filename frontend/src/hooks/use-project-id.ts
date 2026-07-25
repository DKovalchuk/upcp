import { useMemo } from 'react';
import { useLocation } from '@tanstack/react-router';

export function useProjectId(): string {
  const location = useLocation();
  return useMemo(() => {
    const match = location.pathname.match(/^\/projects\/([^/]+)/);
    return match?.[1] ?? '';
  }, [location.pathname]);
}
