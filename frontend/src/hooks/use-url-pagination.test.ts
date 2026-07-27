import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { useUrlPagination } from './use-url-pagination';
import { renderHook } from '@testing-library/react';

describe('useUrlPagination', () => {
  beforeEach(() => {
    window.history.replaceState({}, '', '/');
  });

  afterEach(() => {
    window.history.replaceState({}, '', '/');
  });

  it('returns default values', () => {
    const { result } = renderHook(() => useUrlPagination());
    expect(result.current.page).toBe(1);
    expect(result.current.pageSize).toBe(20);
    expect(result.current.offset).toBe(0);
    expect(result.current.limit).toBe(20);
  });

  it('reads values from URL', () => {
    window.history.replaceState({}, '', '/?page=3&pageSize=50');
    const { result } = renderHook(() => useUrlPagination());
    expect(result.current.page).toBe(3);
    expect(result.current.pageSize).toBe(50);
    expect(result.current.offset).toBe(100);
  });

  it('uses custom default page size', () => {
    const { result } = renderHook(() => useUrlPagination(10));
    expect(result.current.pageSize).toBe(10);
  });

  it('setPageSize updates URL', () => {
    window.history.replaceState({}, '', '/?page=5&pageSize=20');
    const { result } = renderHook(() => useUrlPagination());

    result.current.setPageSize(50);

    const params = new URLSearchParams(window.location.search);
    expect(params.get('pageSize')).toBe('50');
    expect(params.get('page')).toBe('1');
  });

  it('setOffset updates URL with correct page', () => {
    window.history.replaceState({}, '', '/?page=1&pageSize=20');
    const { result } = renderHook(() => useUrlPagination());

    result.current.setOffset(40);

    const params = new URLSearchParams(window.location.search);
    expect(params.get('page')).toBe('3');
  });
});
