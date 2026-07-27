import { useState, useCallback, useEffect } from 'react';

const STORAGE_KEY = 'upcp_saved_views';

export interface SavedView {
  id: string;
  name: string;
  filters: Record<string, string>;
  createdAt: string;
}

function loadViews(): SavedView[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveViews(views: SavedView[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(views));
}

export function useSavedViews() {
  const [views, setViews] = useState<SavedView[]>(loadViews);

  useEffect(() => {
    saveViews(views);
  }, [views]);

  const addView = useCallback((name: string, filters: Record<string, string>) => {
    const view: SavedView = {
      id: crypto.randomUUID(),
      name,
      filters,
      createdAt: new Date().toISOString(),
    };
    setViews((prev) => [...prev, view]);
    return view;
  }, []);

  const removeView = useCallback((id: string) => {
    setViews((prev) => prev.filter((v) => v.id !== id));
  }, []);

  const updateView = useCallback((id: string, updates: Partial<SavedView>) => {
    setViews((prev) =>
      prev.map((v) => (v.id === id ? { ...v, ...updates } : v))
    );
  }, []);

  return { views, addView, removeView, updateView };
}
